"""
Generate an OpenAPI specification from a Python class definition

Copyright 2021-2026, Levente Hunyadi

:see: https://github.com/hunyadi/pyopenapi
"""

import dataclasses
import enum
from dataclasses import dataclass
from typing import Any, ClassVar

from strong_typing.core import JsonType as JsonType
from strong_typing.core import Schema, StrictJsonType

URL = str


@dataclass
class Ref:
    ref_type: ClassVar[str]
    id: str

    def to_json(self) -> StrictJsonType:
        return {"$ref": f"#/components/{self.ref_type}/{self.id}"}


@dataclass
class SchemaRef(Ref):
    ref_type: ClassVar[str] = "schemas"


@dataclass
class ResponseRef(Ref):
    ref_type: ClassVar[str] = "responses"


@dataclass
class ParameterRef(Ref):
    ref_type: ClassVar[str] = "parameters"


@dataclass
class ExampleRef(Ref):
    ref_type: ClassVar[str] = "examples"


@dataclass
class Contact:
    name: str | None = None
    url: URL | None = None
    email: str | None = None


@dataclass
class License:
    name: str
    url: URL | None = None


@dataclass
class Info:
    title: str
    version: str
    description: str | None = None
    termsOfService: str | None = None
    contact: Contact | None = None
    license: License | None = None


@dataclass
class MediaType:
    schema: Schema | SchemaRef | None = None
    example: Any | None = None
    examples: dict[str, "Example | ExampleRef"] | None = None


@dataclass
class RequestBody:
    content: dict[str, MediaType]
    description: str | None = None
    required: bool | None = None


@dataclass
class Response:
    description: str
    content: dict[str, MediaType] | None = None


@enum.unique
class ParameterLocation(enum.Enum):
    Query = "query"
    Header = "header"
    Path = "path"
    Cookie = "cookie"


@dataclass
class Parameter:
    name: str
    in_: ParameterLocation
    description: str | None = None
    required: bool | None = None
    schema: Schema | SchemaRef | None = None
    example: Any | None = None


@dataclass
class Operation:
    responses: dict[str, Response | ResponseRef]
    tags: list[str] | None = None
    summary: str | None = None
    description: str | None = None
    operationId: str | None = None
    parameters: list[Parameter] | None = None
    requestBody: RequestBody | None = None
    callbacks: dict[str, "Callback"] | None = None
    security: list["SecurityRequirement"] | None = None
    deprecated: bool | None = None


@dataclass
class PathItem:
    summary: str | None = None
    description: str | None = None
    get: Operation | None = None
    put: Operation | None = None
    post: Operation | None = None
    delete: Operation | None = None
    options: Operation | None = None
    head: Operation | None = None
    patch: Operation | None = None
    trace: Operation | None = None

    def update(self, other: "PathItem") -> None:
        "Merges another instance of this class into this object."

        for field in dataclasses.fields(self.__class__):
            value = getattr(other, field.name)
            if value is not None:
                setattr(self, field.name, value)


# maps run-time expressions such as "$request.body#/url" to path items
Callback = dict[str, PathItem]


@dataclass
class Example:
    summary: str | None = None
    description: str | None = None
    value: Any | None = None
    externalValue: URL | None = None


@dataclass
class Server:
    url: URL
    description: str | None = None


@enum.unique
class SecuritySchemeType(enum.Enum):
    ApiKey = "apiKey"
    HTTP = "http"
    OAuth2 = "oauth2"
    OpenIDConnect = "openIdConnect"


@dataclass
class SecurityScheme:
    type: SecuritySchemeType
    description: str


@dataclass(init=False)
class SecuritySchemeAPI(SecurityScheme):
    name: str
    in_: ParameterLocation

    def __init__(self, description: str, name: str, in_: ParameterLocation) -> None:
        super().__init__(SecuritySchemeType.ApiKey, description)
        self.name = name
        self.in_ = in_


@dataclass(init=False)
class SecuritySchemeHTTP(SecurityScheme):
    scheme: str
    bearerFormat: str | None = None

    def __init__(self, description: str, scheme: str, bearerFormat: str | None = None) -> None:
        super().__init__(SecuritySchemeType.HTTP, description)
        self.scheme = scheme
        self.bearerFormat = bearerFormat


@dataclass(init=False)
class SecuritySchemeOpenIDConnect(SecurityScheme):
    openIdConnectUrl: str

    def __init__(self, description: str, openIdConnectUrl: str) -> None:
        super().__init__(SecuritySchemeType.OpenIDConnect, description)
        self.openIdConnectUrl = openIdConnectUrl


@dataclass
class Components:
    schemas: dict[str, Schema] | None = None
    responses: dict[str, Response] | None = None
    parameters: dict[str, Parameter] | None = None
    examples: dict[str, Example] | None = None
    requestBodies: dict[str, RequestBody] | None = None
    securitySchemes: dict[str, SecurityScheme] | None = None
    callbacks: dict[str, Callback] | None = None


SecurityScope = str
SecurityRequirement = dict[str, list[SecurityScope]]


@dataclass
class Tag:
    name: str
    description: str | None = None
    displayName: str | None = None


@dataclass
class TagGroup:
    """
    A ReDoc extension to provide information about groups of tags.

    Exposed via the vendor-specific property "x-tagGroups" of the top-level object.

    :param name: Group name.
    :param tags: Tags that are members of this group.
    """

    name: str
    tags: list[str]


@dataclass
class Document:
    """
    This class is a Python dataclass adaptation of the OpenAPI Specification.

    For details, see <https://swagger.io/specification/>

    :param openapi: Version number of the OpenAPI Specification that the OpenAPI document uses.
    :param info: Provides metadata about the API.
    :param servers: An array of objects that provide connectivity information to a target server.
    :param paths: The available paths and operations for the API.
    :param jsonSchemaDialect: The default value for the `$schema` keyword within schema objects in this document, in the form of a URI.
    :param components: An element to hold various objects for the OpenAPI description.
    :param security: A declaration of which security mechanisms can be used across the API.
    :param tags: A list of tags used by the OpenAPI description with additional metadata.
    :param tagGroups: Provides information about a group of tags. (Extension to OpenAPI.)
    """

    openapi: str
    info: Info
    servers: list[Server]
    paths: dict[str, PathItem]
    jsonSchemaDialect: str | None = None
    components: Components | None = None
    security: list[SecurityRequirement] | None = None
    tags: list[Tag] | None = None
    tagGroups: list[TagGroup] | None = None
