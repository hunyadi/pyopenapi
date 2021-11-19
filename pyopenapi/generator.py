from dataclasses import dataclass
from typing import Any, Dict, Type

import docstring_parser
from strong_typing import (
    JsonSchemaGenerator,
    Schema,
    SchemaOptions,
    is_generic_list,
    is_type_optional,
    unwrap_generic_list,
    unwrap_optional_type,
)

from .operations import HTTPMethod, get_endpoint_events, get_endpoint_operations
from .options import *
from .specification import (
    Components,
    Document,
    MediaType,
    Operation,
    Parameter,
    ParameterLocation,
    PathItem,
    RequestBody,
    Response,
    ResponseRef,
    Tag,
    TagGroup,
)


class Generator:
    endpoint: Type
    schema_generator: JsonSchemaGenerator
    schemas: Dict[str, Schema]

    def __init__(self, endpoint: Any):
        self.endpoint = endpoint
        self.schema_generator = JsonSchemaGenerator(
            SchemaOptions(definitions_path="#/components/schemas/")
        )
        self.schemas = {}

    def _classdef_to_schema(self, typ: Type) -> Schema:
        type_schema, type_definitions = self.schema_generator.classdef_to_schema(typ)

        # append schema to list of known schemas, to be used in OpenAPI's Components Object section
        self.schemas.update(type_definitions)

        return type_schema

    def _build_content(self, payload_type: Type) -> Dict[str, MediaType]:
        if is_generic_list(payload_type):
            media_type = "application/jsonl"
            item_type = unwrap_generic_list(payload_type)
        else:
            media_type = "application/json"
            item_type = payload_type

        return {media_type: MediaType(schema=self._classdef_to_schema(item_type))}

    def _build_response(self, response_type: Type, description: str) -> Response:
        if response_type is not None:
            return Response(
                description=description, content=self._build_content(response_type)
            )
        else:
            return Response(description=description)

    def generate(self, options: Options) -> Document:
        paths = {}
        endpoint_classes = set()
        for op in get_endpoint_operations(self.endpoint):
            endpoint_classes.add(op.defining_class)

            doc_string = docstring_parser.parse(op.func_ref.__doc__)
            doc_params = dict(
                (param.arg_name, param.description) for param in doc_string.params
            )

            path_parameters = [
                Parameter(
                    name=param_name,
                    in_=ParameterLocation.Path,
                    description=doc_params.get(param_name),
                    required=True,
                    schema=self._classdef_to_schema(param_type),
                )
                for param_name, param_type in op.path_params
            ]
            query_parameters = []
            for param_name, param_type in op.query_params:
                if is_type_optional(param_type):
                    query_parameter = Parameter(
                        name=param_name,
                        in_=ParameterLocation.Query,
                        description=doc_params.get(param_name),
                        required=False,
                        schema=self._classdef_to_schema(
                            unwrap_optional_type(param_type)
                        ),
                    )
                else:
                    query_parameter = Parameter(
                        name=param_name,
                        in_=ParameterLocation.Query,
                        description=doc_params.get(param_name),
                        required=True,
                        schema=self._classdef_to_schema(param_type),
                    )
                query_parameters.append(query_parameter)

            parameters = path_parameters + query_parameters

            if op.request_param:
                request_name, request_type = op.request_param
                requestBody = RequestBody(
                    content={
                        "application/json": MediaType(
                            schema=self._classdef_to_schema(request_type)
                        )
                    },
                    description=doc_params.get(request_name),
                    required=True,
                )
            else:
                requestBody = None

            response_description = (
                doc_string.returns.description if doc_string.returns else None
            )
            if op.event_type is not None:
                responses = {
                    "200": self._build_response(
                        response_type=op.event_type, description=response_description
                    ),
                    "default": ResponseRef("BadRequest"),
                }

                callbacks = {
                    f"{op.func_name}_callback": {
                        "{$request.query.url}": PathItem(
                            post=Operation(
                                requestBody=RequestBody(
                                    content=self._build_content(op.response_type)
                                ),
                                responses={"200": Response(description="OK")},
                            )
                        )
                    }
                }

            else:
                responses = {
                    "200": self._build_response(
                        response_type=op.response_type, description=response_description
                    ),
                    "default": ResponseRef("BadRequest"),
                }
                callbacks = None

            operation = Operation(
                tags=[op.defining_class.__name__],
                summary=doc_string.short_description,
                description=doc_string.long_description,
                parameters=parameters,
                requestBody=requestBody,
                responses=responses,
                callbacks=callbacks,
            )

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
                raise NotImplementedError()

            route = op.get_route()
            if route in paths:
                paths[route].update(pathItem)
            else:
                paths[route] = pathItem

        operation_tags = []
        for cls in endpoint_classes:
            doc_string = docstring_parser.parse(cls.__doc__)
            operation_tags.append(
                Tag(
                    name=cls.__name__,
                    description=doc_string.long_description,
                    displayName=doc_string.short_description,
                )
            )

        # types that are explicitly declared
        if options.extra_types is not None:
            for extra_type in options.extra_types:
                type_schema = self._classdef_to_schema(extra_type)
                self.schemas[extra_type.__name__] = type_schema

        # types that are produced/consumed by operations
        schema_tags = [
            Tag(
                name=ref,
                description=f'<SchemaDefinition schemaRef="#/components/schemas/{ref}" />',
            )
            for ref in self.schemas.keys()
        ]

        # types that are emitted by events
        events = get_endpoint_events(self.endpoint)
        for event_type in events.values():
            self._classdef_to_schema(event_type)
        event_tags = [
            Tag(
                name=ref,
                description=f'<SchemaDefinition schemaRef="#/components/schemas/{ref}" />',
            )
            for ref in events.keys()
        ]

        # list all operations and types
        tags = []
        tags.extend(operation_tags)
        tags.extend(event_tags)
        tags.extend(schema_tags)

        tag_groups = []
        if operation_tags:
            tag_groups.append(
                TagGroup(name="Operations", tags=[tag.name for tag in operation_tags])
            )
        if event_tags:
            tag_groups.append(
                TagGroup(name="Events", tags=[tag.name for tag in event_tags])
            )
        if schema_tags:
            tag_groups.append(
                TagGroup(name="Types", tags=[tag.name for tag in schema_tags])
            )

        responses = {
            "BadRequest": Response(
                description=None,
                content={
                    "application/json": MediaType(
                        schema=self._classdef_to_schema(ErrorResponse)
                    )
                },
            )
        }

        if options.default_security_scheme:
            securitySchemes = {"Default": options.default_security_scheme}
        else:
            securitySchemes = None

        return Document(
            openapi="3.0.0",
            info=options.info,
            servers=[options.server],
            paths=paths,
            components=Components(
                schemas=self.schemas,
                responses=responses,
                securitySchemes=securitySchemes,
            ),
            security=[{"Default": []}],
            tags=tags,
            tagGroups=tag_groups,
        )
