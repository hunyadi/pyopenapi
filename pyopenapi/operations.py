import collections.abc
import enum
import inspect
import sys
import typing
import uuid
from dataclasses import dataclass
from typing import (
    Any,
    Callable,
    Dict,
    Iterable,
    Iterator,
    List,
    Optional,
    Tuple,
    Type,
    Union,
)

from strong_typing import is_type_enum, is_type_optional, unwrap_optional_type

from .metadata import WebMethod


def split_prefix(
    s: str, sep: str, prefix: Union[str, Iterable[str]]
) -> Tuple[str, str]:
    """
    Recognizes a prefix at the beginning of a string.

    :param s: The string to check.
    :param sep: A separator between (one of) the prefix(es) and the rest of the string.
    :param prefix: A string or a set of strings to identify as a prefix.
    :return: A tuple of the recognized prefix (if any) and the rest of the string excluding the separator (or the entire string).
    """

    if isinstance(prefix, str):
        if s.startswith(prefix + sep):
            return prefix, s[len(prefix) + len(sep) :]
        else:
            return None, s

    for p in prefix:
        if s.startswith(p + sep):
            return p, s[len(p) + len(sep) :]

    return None, s


def _get_annotation_type(annotation: Union[type, str], callable: Callable) -> type:
    "Maps a stringized reference to a type, as if using `from __future__ import annotations`."

    if isinstance(annotation, str):
        return eval(annotation, callable.__globals__)
    else:
        return annotation


class HTTPMethod(enum.Enum):
    "HTTP method used to invoke an endpoint operation."

    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"


OperationParameter = Tuple[str, Type]


@dataclass
class EndpointOperation:
    """
    Type information and metadata associated with an endpoint operation.

    "param defining_class: The most specific class that defines the endpoint operation.
    :param name: The short name of the endpoint operation.
    :param func_name: The name of the function to invoke when the operation is triggered.
    :param func_ref: The callable to invoke when the operation is triggered.
    :param route: A custom route string assigned to the operation.
    :param path_params: Parameters of the operation signature that are passed in the path component of the URL string.
    :param query_params: Parameters of the operation signature that are passed in the query string as `key=value` pairs.
    :param request_param: The parameter that corresponds to the data transmitted in the request body.
    :param event_type: The Python type of the data that is transmitted out-of-band (e.g. via websockets) while the operation is in progress.
    :param response_type: The Python type of the data that is transmitted in the response body.
    :param http_method: The HTTP method used to invoke the endpoint such as POST, GET or PUT.
    """

    defining_class: Type
    name: str
    func_name: str
    func_ref: Callable[..., Any]
    route: Optional[str]
    path_params: List[OperationParameter]
    query_params: List[OperationParameter]
    request_param: Optional[OperationParameter]
    event_type: Type
    response_type: Type
    http_method: HTTPMethod

    def get_route(self) -> str:
        if self.route is not None:
            return self.route

        route_parts = ["", self.name]
        for param_name, _ in self.path_params:
            route_parts.append("{" + param_name + "}")
        return "/".join(route_parts)


class _FormatParameterExtractor:
    "A visitor to exract parameters in a format string."

    keys: List[str]

    def __init__(self):
        self.keys = []

    def __getitem__(self, key: str):
        self.keys.append(key)
        return None


def _get_route_parameters(route: str) -> List[str]:
    extractor = _FormatParameterExtractor()
    route.format_map(extractor)
    return extractor.keys


def _get_endpoint_functions(
    endpoint: Type, prefixes: List[str]
) -> Iterator[Tuple[str, str, str, Callable]]:

    if not inspect.isclass(endpoint):
        raise TypeError(f"object is not a class type: {endpoint}")

    functions = inspect.getmembers(endpoint, inspect.isfunction)
    for func_name, func_ref in functions:
        prefix, operation_name = split_prefix(func_name, "_", prefixes)
        if not prefix:
            continue

        yield prefix, operation_name, func_name, func_ref


def _get_defining_class(member_fn: str, derived_cls: Type) -> Type:
    "Find the class in which a member function is first defined in a class inheritance hierarchy."

    # iterate in reverse member resolution order to find most specific class first
    for cls in reversed(inspect.getmro(derived_cls)):
        for name, _ in inspect.getmembers(cls, inspect.isfunction):
            if name == member_fn:
                return cls

    raise ValueError(f"cannot find defining class for {member_fn} in {derived_cls}")


def get_endpoint_operations(endpoint: Type) -> List[EndpointOperation]:
    """
    Extracts a list of member functions in a class eligible for HTTP interface binding.

    These member functions are expected to have a signature like
    ```
    async def get_object(self, uuid: str, version: int) -> Object:
        ...
    ```
    where the prefix `get_` translates to an HTTP GET, `object` corresponds to the name of the endpoint operation,
    `uuid` and `version` are mapped to route path elements in "/object/{uuid}/{version}", and `Object` becomes
    the response payload type, transmitted as an object serialized to JSON.

    If the member function has a composite class type in the argument list, it becomes the request payload type,
    and the caller is expected to provide the data as serialized JSON in an HTTP POST request.

    :param endpoint: A class with member functions that can be mapped to an HTTP endpoint.
    """

    result = []

    for prefix, operation_name, func_name, func_ref in _get_endpoint_functions(
        endpoint,
        [
            "create",
            "delete",
            "get",
            "post",
            "put",
            "remove",
            "set",
            "update",
        ],
    ):

        # extract routing information from function metadata
        route = None
        route_params = None
        webmethod: Optional[WebMethod] = getattr(func_ref, "__webmethod__", None)
        if webmethod is not None:
            route = webmethod.route
            route_params = _get_route_parameters(route)

        # inspect function signature for path and query parameters, and request/response payload type
        if sys.version_info >= (3, 10):
            signature = inspect.signature(func_ref, eval_str=True)
        else:
            signature = inspect.signature(func_ref)

        path_params = []
        query_params = []
        request_param = None

        for param_name, parameter in signature.parameters.items():
            param_type = _get_annotation_type(parameter.annotation, func_ref)

            # omit "self" for instance methods
            if param_name == "self" and param_type is inspect.Parameter.empty:
                continue

            if is_type_optional(param_type):
                inner_type = unwrap_optional_type(param_type)
            else:
                inner_type = param_type

            if (
                inner_type is bool
                or inner_type is int
                or inner_type is float
                or inner_type is str
                or inner_type is uuid.UUID
                or is_type_enum(inner_type)
            ):
                if parameter.kind == inspect.Parameter.POSITIONAL_ONLY:
                    if route_params is not None and param_name not in route_params:
                        raise TypeError(
                            f"positional parameter '{param_name}' absent from user-defined route '{route}' for function '{func_name}'"
                        )

                    # simple type maps to route path element, e.g. /study/{uuid}/{version}
                    path_params.append((param_name, param_type))
                else:
                    if route_params is not None and param_name in route_params:
                        raise TypeError(
                            f"query parameter '{param_name}' found in user-defined route '{route}' for function '{func_name}'"
                        )

                    # simple type maps to key=value pair in query string
                    query_params.append((param_name, param_type))
            else:
                if route_params is not None and param_name in route_params:
                    raise TypeError(
                        f"user-defined route '{route}' for function '{func_name}' has parameter '{param_name}' of composite type: {param_type}"
                    )

                if request_param is not None:
                    param = (param_name, param_type)
                    raise TypeError(
                        f"only a single composite type is permitted in a signature but multiple composite types found in function '{func_name}': {request_param} and {param}"
                    )

                # composite types are read from body
                request_param = (param_name, param_type)

        return_type = _get_annotation_type(signature.return_annotation, func_ref)
        if typing.get_origin(return_type) is collections.abc.Generator:
            event_type, _, response_type = typing.get_args(return_type)
        else:
            event_type = None
            response_type = return_type

        # set HTTP request method based on type of request and presence of payload
        if request_param is None:
            if prefix in ["delete", "remove"]:
                http_method = HTTPMethod.DELETE
            else:
                http_method = HTTPMethod.GET
        else:
            if prefix == "set":
                http_method = HTTPMethod.PUT
            elif prefix == "update":
                http_method = HTTPMethod.PATCH
            else:
                http_method = HTTPMethod.POST

        result.append(
            EndpointOperation(
                defining_class=_get_defining_class(func_name, endpoint),
                name=operation_name,
                func_name=func_name,
                func_ref=func_ref,
                route=route,
                path_params=path_params,
                query_params=query_params,
                request_param=request_param,
                event_type=event_type,
                response_type=response_type,
                http_method=http_method,
            )
        )

    if not result:
        raise TypeError(f"no eligible endpoint operations in type {endpoint}")

    return result


def get_endpoint_events(endpoint: Type) -> Dict[str, Type]:
    results = {}

    for name, decl in typing.get_type_hints(endpoint).items():
        # check if signature is Callable[...]
        origin = typing.get_origin(decl)
        if origin is None or not issubclass(origin, Callable):
            continue

        # check if signature is Callable[[...], Any]
        args = typing.get_args(decl)
        if len(args) != 2:
            continue
        params_type, return_type = args
        if not isinstance(params_type, list):
            continue

        # check if signature is Callable[[...], None]
        if not issubclass(return_type, type(None)):
            continue

        # check if signature is Callable[[EventType], None]
        if len(params_type) != 1:
            continue

        param_type = params_type[0]
        results[param_type.__name__] = param_type

    return results