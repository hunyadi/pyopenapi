from typing import Any, Dict, Set, Union

from strong_typing.docstring import parse_type
from strong_typing.inspection import (
    is_generic_list,
    is_type_optional,
    is_type_union,
    unwrap_generic_list,
    unwrap_optional_type,
    unwrap_union_types,
)
from strong_typing.name import python_type_to_name
from strong_typing.schema import (
    JsonSchemaGenerator,
    Schema,
    SchemaOptions,
    get_schema_identifier,
)
from strong_typing.serialization import object_to_json

from .operations import (
    EndpointOperation,
    HTTPMethod,
    get_endpoint_events,
    get_endpoint_operations,
)
from .options import *
from .specification import (
    Components,
    Document,
    Example,
    ExampleRef,
    MediaType,
    Operation,
    Parameter,
    ParameterLocation,
    PathItem,
    RequestBody,
    Response,
    ResponseRef,
    SchemaRef,
    Tag,
    TagGroup,
)


class Generator:
    endpoint: type
    options: Options
    schema_generator: JsonSchemaGenerator
    schemas: Dict[str, Schema]
    responses: Dict[str, Response]

    def __init__(self, endpoint: type, options: Options) -> None:
        self.endpoint = endpoint
        self.options = options
        self.schema_generator = JsonSchemaGenerator(
            SchemaOptions(
                definitions_path="#/components/schemas/",
                property_description_fun=options.property_description_fun,
            )
        )
        self.schemas = {}
        self.responses = {}

    def _classdef_to_schema(self, typ: type) -> Schema:
        """
        Converts a type to a JSON schema.
        For nested types found in the type hierarchy, adds the type to the schema registry in the OpenAPI specification section `components`.
        """

        type_schema, type_definitions = self.schema_generator.classdef_to_schema(typ)

        # append schema to list of known schemas, to be used in OpenAPI's Components Object section
        for ref, schema in type_definitions.items():
            if ref not in self.schemas:
                self.schemas[ref] = schema

        return type_schema

    def _classdef_to_ref(self, typ: type) -> Union[Schema, SchemaRef]:
        """
        Converts a type to a JSON schema, and if possible, returns a schema reference.
        For composite types (such as classes), adds the type to the schema registry in the OpenAPI specification section `components`.
        """

        type_schema = self._classdef_to_schema(typ)
        if typ is str or typ is int or typ is float:
            # represent simple types as themselves
            return type_schema

        type_name = get_schema_identifier(typ)
        if type_name is not None:
            return self._build_ref(type_name, type_schema)

        try:
            type_name = python_type_to_name(typ)
            return self._build_ref(type_name, type_schema)
        except TypeError:
            pass

        return type_schema

    def _build_ref(self, type_name: str, type_schema: Schema) -> SchemaRef:
        if type_name not in self.schemas:
            self.schemas[type_name] = type_schema
        return SchemaRef(type_name)

    def _build_media_type(
        self, item_type: type, examples: List[Any] = None
    ) -> MediaType:
        return MediaType(
            schema=self._classdef_to_ref(item_type),
            examples=self._build_examples(examples),
        )

    def _build_examples(
        self, examples: List[Any] = None
    ) -> Optional[Dict[str, Union[Example, ExampleRef]]]:

        return (
            {
                str(example): Example(value=object_to_json(example))
                for example in examples
            }
            if examples is not None
            else None
        )

    def _build_content(
        self, payload_type: type, examples: List[Any] = None
    ) -> Dict[str, MediaType]:
        "Creates the content subtree for a request or response."

        if is_generic_list(payload_type):
            media_type = "application/jsonl"
            item_type = unwrap_generic_list(payload_type)
        else:
            media_type = "application/json"
            item_type = payload_type

        return {media_type: self._build_media_type(item_type, examples)}

    def _build_response(
        self, response_type: type, description: str, examples: List[Any] = None
    ) -> Response:
        "Creates a response subtree."

        if response_type is not None:
            return Response(
                description=description,
                content=self._build_content(response_type, examples),
            )
        else:
            return Response(description=description)

    def _build_response_group(
        self,
        response_type_descriptions: Dict[type, str],
        response_examples: Optional[List[Any]],
        response_status_catalog: Dict[type, Union[int, str]],
        default_status_code: Union[int, str],
    ) -> Dict[str, Union[Response, ResponseRef]]:
        """
        Groups responses that have the same status code.

        :param response_type_descriptions: Maps each response type to a textual description (if available).
        :param response_examples: A list of response examples.
        :param response_status_catalog: Maps each response type to an HTTP status code.
        :param default_status_code: HTTP status code assigned to responses that have no mapping.
        """

        status_responses: Dict[str, List[type]] = {}
        for response_type in response_type_descriptions.keys():
            status_code = str(
                response_status_catalog.get(response_type, default_status_code)
            )
            if status_code not in status_responses:
                status_responses[status_code] = []
            status_responses[status_code].append(response_type)

        responses: Dict[str, Union[Response, ResponseRef]] = {}
        for status_code, response_type_list in status_responses.items():
            response_type_tuple = tuple(response_type_list)
            if len(response_type_tuple) > 1:
                composite_response_type: type = Union[response_type_tuple]  # type: ignore
            else:
                response_type = response_type_tuple[0]
                composite_response_type = response_type

            description = " **OR** ".join(
                filter(
                    None,
                    (
                        response_type_descriptions[response_type]
                        for response_type in response_type_tuple
                    ),
                )
            )

            if response_examples:
                if all(isinstance(t, type) for t in response_type_tuple):
                    examples = [
                        example
                        for example in response_examples
                        if isinstance(example, response_type_tuple)
                    ]
                else:
                    examples = response_examples
            else:
                examples = []

            responses[status_code] = self._build_response(
                response_type=composite_response_type,
                description=description,
                examples=examples if examples else None,
            )

        return responses

    def _build_type_tag(self, ref: str, schema: Schema) -> Tag:
        definition = f'<SchemaDefinition schemaRef="#/components/schemas/{ref}" />'
        title = schema.get("title")
        description = schema.get("description")
        return Tag(
            name=ref,
            description="\n\n".join(
                s for s in (title, description, definition) if s is not None
            ),
        )

    def _build_extra_tag_groups(
        self, extra_types: Dict[str, List[type]]
    ) -> Dict[str, List[Tag]]:
        """
        Creates a dictionary of tag group captions as keys, and tag lists as values.

        :param extra_types: A dictionary of type categories and list of types in that category.
        """

        extra_tags: Dict[str, List[Tag]] = {}

        for category_name, category_items in extra_types.items():
            tag_list: List[Tag] = []

            for extra_type in category_items:
                ref = extra_type.__name__
                type_schema = self._classdef_to_schema(extra_type)
                self.schemas[ref] = type_schema
                tag_list.append(self._build_type_tag(ref, type_schema))

            extra_tags[category_name] = tag_list

        return extra_tags

    def _build_operation(self, op: EndpointOperation) -> Operation:
        doc_string = parse_type(op.func_ref)
        doc_params = dict(
            (param.name, param.description) for param in doc_string.params.values()
        )

        # parameters passed in URL component path
        path_parameters = [
            Parameter(
                name=param_name,
                in_=ParameterLocation.Path,
                description=doc_params.get(param_name),
                required=True,
                schema=self._classdef_to_ref(param_type),
            )
            for param_name, param_type in op.path_params
        ]

        # parameters passed in URL component query string
        query_parameters = []
        for param_name, param_type in op.query_params:
            if is_type_optional(param_type):
                inner_type = unwrap_optional_type(param_type)
                required = False
            else:
                inner_type = param_type
                required = True

            query_parameter = Parameter(
                name=param_name,
                in_=ParameterLocation.Query,
                description=doc_params.get(param_name),
                required=required,
                schema=self._classdef_to_ref(inner_type),
            )
            query_parameters.append(query_parameter)

        # parameters passed anywhere
        parameters = path_parameters + query_parameters

        # data passed in payload
        if op.request_param:
            request_name, request_type = op.request_param
            requestBody = RequestBody(
                content={
                    "application/json": self._build_media_type(
                        request_type, op.request_examples
                    )
                },
                description=doc_params.get(request_name),
                required=True,
            )
        else:
            requestBody = None

        # success response types
        if doc_string.returns is None and is_type_union(op.response_type):
            # split union of return types into a list of response types
            success_type_descriptions = {
                item: parse_type(item).short_description
                for item in unwrap_union_types(op.response_type)
            }
        else:
            # use return type as a single response type
            success_type_descriptions = {
                op.response_type: doc_string.returns.description
                if doc_string.returns
                else "OK"
            }

        responses: Dict[str, Union[Response, ResponseRef]] = self._build_response_group(
            success_type_descriptions,
            op.response_examples,
            self.options.success_responses,
            "200",
        )

        # failure response types
        if doc_string.raises:
            exception_types = {
                item.raise_type: item.description for item in doc_string.raises.values()
            }

            responses.update(
                self._build_response_group(
                    exception_types,
                    op.response_examples,
                    self.options.error_responses,
                    "500",
                )
            )

        if op.event_type is not None:
            callbacks = {
                f"{op.func_name}_callback": {
                    "{$request.query.callback}": PathItem(
                        post=Operation(
                            requestBody=RequestBody(
                                content=self._build_content(op.event_type)
                            ),
                            responses={"200": Response(description="OK")},
                        )
                    )
                }
            }

        else:
            callbacks = None

        return Operation(
            tags=[op.defining_class.__name__],
            summary=doc_string.short_description,
            description=doc_string.long_description,
            parameters=parameters,
            requestBody=requestBody,
            responses=responses,
            callbacks=callbacks,
            security=[] if op.public else None,
        )

    def generate(self) -> Document:
        paths: Dict[str, PathItem] = {}
        endpoint_classes: Set[type] = set()
        for op in get_endpoint_operations(self.endpoint):
            endpoint_classes.add(op.defining_class)

            operation = self._build_operation(op)

            if op.http_method is HTTPMethod.GET:
                pathItem = PathItem(get=operation)
            elif op.http_method is HTTPMethod.PUT:
                pathItem = PathItem(put=operation)
            elif op.http_method is HTTPMethod.POST:
                pathItem = PathItem(post=operation)
            elif op.http_method is HTTPMethod.DELETE:
                pathItem = PathItem(delete=operation)
            elif op.http_method is HTTPMethod.PATCH:
                pathItem = PathItem(patch=operation)
            else:
                raise NotImplementedError(f"unknown HTTP method: {op.http_method}")

            route = op.get_route()
            if route in paths:
                paths[route].update(pathItem)
            else:
                paths[route] = pathItem

        operation_tags: List[Tag] = []
        for cls in endpoint_classes:
            doc_string = parse_type(cls)
            operation_tags.append(
                Tag(
                    name=cls.__name__,
                    description=doc_string.long_description,
                    displayName=doc_string.short_description,
                )
            )

        # types that are produced/consumed by operations
        type_tags = [
            self._build_type_tag(ref, schema) for ref, schema in self.schemas.items()
        ]

        # types that are emitted by events
        event_tags: List[Tag] = []
        events = get_endpoint_events(self.endpoint)
        for ref, event_type in events.items():
            event_schema = self._classdef_to_schema(event_type)
            if ref not in self.schemas:
                self.schemas[ref] = event_schema
            event_tags.append(self._build_type_tag(ref, event_schema))

        # types that are explicitly declared
        extra_tag_groups: Dict[str, List[Tag]] = {}
        if self.options.extra_types is not None:
            if isinstance(self.options.extra_types, list):
                extra_tag_groups = self._build_extra_tag_groups(
                    {"AdditionalTypes": self.options.extra_types}
                )
            elif isinstance(self.options.extra_types, dict):
                extra_tag_groups = self._build_extra_tag_groups(
                    self.options.extra_types
                )
            else:
                raise TypeError(
                    f"type mismatch for collection of extra types: {type(self.options.extra_types)}"
                )

        # list all operations and types
        tags: List[Tag] = []
        tags.extend(operation_tags)
        tags.extend(type_tags)
        tags.extend(event_tags)
        for extra_tag_group in extra_tag_groups.values():
            tags.extend(extra_tag_group)

        tag_groups = []
        if operation_tags:
            tag_groups.append(
                TagGroup(
                    name=self.options.map("Operations"),
                    tags=sorted(tag.name for tag in operation_tags),
                )
            )
        if type_tags:
            tag_groups.append(
                TagGroup(
                    name=self.options.map("Types"),
                    tags=sorted(tag.name for tag in type_tags),
                )
            )
        if event_tags:
            tag_groups.append(
                TagGroup(
                    name=self.options.map("Events"),
                    tags=sorted(tag.name for tag in event_tags),
                )
            )
        for caption, extra_tag_group in extra_tag_groups.items():
            tag_groups.append(
                TagGroup(
                    name=self.options.map(caption),
                    tags=sorted(tag.name for tag in extra_tag_group),
                )
            )

        if self.options.default_security_scheme:
            securitySchemes = {"Default": self.options.default_security_scheme}
        else:
            securitySchemes = None

        return Document(
            openapi="3.1.0",
            info=self.options.info,
            servers=[self.options.server],
            paths=paths,
            components=Components(
                schemas=self.schemas,
                responses=self.responses,
                securitySchemes=securitySchemes,
            ),
            security=[{"Default": []}],
            tags=tags,
            tagGroups=tag_groups,
        )
