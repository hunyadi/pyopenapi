# Generate an OpenAPI specification from a Python class

*PyOpenAPI* produces an OpenAPI specification in JSON, YAML or HTML format with endpoint definitions extracted from member functions of a strongly-typed Python class.

## Features

* supports standard and asynchronous functions (`async def`)
* maps function name prefixes such as `get_` or `create_` to HTTP GET, POST, PUT, DELETE, PATCH
* handles both simple and composite types (`int`, `str`, `Enum`, `@dataclass`)
* handles generic types (`list[T]`, `dict[K, V]`, `Optional[T]`, `Union[T1, T2, T3]`)
* maps Python positional-only and keyword-only arguments (of simple types) to path and query parameters, respectively
* maps composite types to HTTP request body
* supports user-defined routes, request and response samples with decorator `@webmethod`
* extracts description text from class and function doc-strings (`__doc__`)
* recognizes parameter description text given in reStructuredText doc-string format (`:param name: ...`)
* converts exceptions declared in doc-strings into HTTP 4xx and 5xx responses (e.g. `:raises TypeError:`)
* recursively converts composite types into JSON schemas
* groups frequently used composite types into a separate section and re-uses them with `$ref`
* displays generated OpenAPI specification in HTML with [ReDoc](https://github.com/Redocly/redoc)

## Live examples

* [Endpoint definition in Python](https://hunyadi.github.io/pyopenapi/examples/python/index.html)
* [Generated OpenAPI specification in JSON](https://hunyadi.github.io/pyopenapi/examples/json/index.html)
* [Generated OpenAPI specification in YAML](https://hunyadi.github.io/pyopenapi/examples/yaml/index.html)
* [Generated OpenAPI specification in HTML with ReDoc](https://hunyadi.github.io/pyopenapi/examples/index.html)

## User guide

### The specification object

In order to generate an [OpenAPI specification document](https://spec.openapis.org/oas/latest.html), you should first construct a `Specification` object, which encapsulates the formal definition:

```python
specification = Specification(
    MyEndpoint,
    Options(
        server=Server(url="http://example.com/api"),
        info=Info(
            title="Example specification",
            version="1.0",
            description=description,
        ),
        default_security_scheme=SecuritySchemeHTTP(
            "Authenticates a request by verifying a JWT (JSON Web Token) passed in the `Authorization` HTTP header.",
            "bearer",
            "JWT",
        ),
        extra_types=[ExampleType, UnreferencedType],
        error_wrapper=True,
    ),
)
```

The first argument to `Specification` is a Python class (`type`) whose methods will be inspected and converted into OpenAPI endpoint operations. The second argument is additional options that fine-tune how the specification is generated.

### Defining endpoint operations

Let's take a look at the definition of a simple endpoint called `JobManagement`:

```python
class JobManagement:
    def create_job(self, items: list[URL]) -> uuid.UUID:
        ...

    def get_job(self, job_id: uuid.UUID, /, format: Format) -> Job:
        ...

    def remove_job(self, job_id: uuid.UUID, /) -> None:
        ...

    def update_job(self, job_id: uuid.UUID, /, job: Job) -> None:
        ...
```

The name of each method begins with a prefix such as `create`, `get`, `remove` or `update`, each of which maps to an HTTP verb, e.g. `POST`, `GET`, `DELETE` or `PATCH`. The rest of the function name serves as an identifier, e.g. `job`. The `self` argument to the function is ignored. Other arguments indicate what path and query [parameter objects](https://spec.openapis.org/oas/latest.html#parameter-object), and what [HTTP request body](https://spec.openapis.org/oas/latest.html#request-body-object) the operation accepts.

### Function signatures for operations

Function signatures for operations must have full type annotation, including parameter types and return type.

Python [positional-only arguments](https://peps.python.org/pep-0570/) map to path parameters. Python positional-or-keyword arguments map to query parameters if they are of a simple type (e.g. `int` or `str`). If a composite type (e.g. a class, a list or a union) occurs in the Python parameter list, it is treated as the definition of the HTTP request body. Only one composite type may appear in the parameter list. The return type of the function is treated as the HTTP response body. If the function returns `None`, it corresponds to an HTTP response with no payload (i.e. a `Content-Length` of 0).

The JSON schema for the HTTP request and response body is generated with the library [json_strong_typing](https://github.com/hunyadi/strong_typing), and is automatically embedded in the OpenAPI specification document.

### User-defined operation path

By default, the library constructs the operation path from the Python function name and positional-only parameters. However, it is possible to supply a custom path (route) using the `@webmethod` decorator:

```python
@webmethod(
    route="/person/name/{family}/{given}",
)
def get_person_by_name(self, family: str, given: str, /) -> Person:
    ...
```

The custom path must have placeholders for all positional-only parameters in the function signature, and vice versa.

### Documenting operations

Use Python ReST (ReStructured Text) doc-strings to attach documentation to operations:

```python
def get_job(self, job_id: uuid.UUID, /, format: Format) -> Job:
    """
    Query status information about a job.

    :param job_id: Unique identifier for the job to query.
    :returns: Status information about the job.
    :raises NotFoundError: The job does not exist.
    :raises ValidationError: The input is malformed.
    """
    ...
```

Fields such as `param` and `returns` help document path and query parameters, HTTP request and response body. The field `raises` helps document error responses by identifying the exact return type when an error occurs. The Python type for `returns` and `raises` is translated to a JSON schema and embedded in the OpenAPI specification document.

### Request and response examples

OpenAPI supports specifying [examples](https://spec.openapis.org/oas/latest.html#example-object) for the HTTP request and response body of endpoint operations. This is supported via the `@webmethod` decorator:

```python
    @webmethod(
        route="/member/name/{family}/{given}",
        response_examples=[
            Student("Szörnyeteg", "Lajos"),
            Student("Ló", "Szerafin"),
            Student("Bruckner", "Szigfrid"),
            Student("Nagy", "Zoárd"),
            Teacher("Mikka", "Makka", "Négyszögletű Kerek Erdő"),
            Teacher("Vacska", "Mati", "Négyszögletű Kerek Erdő"),
        ],
    )
    def get_member_by_name(self, family: str, given: str, /) -> Union[Student, Teacher]:
        ...
```

A response example may be an exception or error class (a type that derives from `Exception`). These are usually shown under an HTTP status code of 4xx or 5xx.

The Python objects in `request_examples` and `response_examples` are translated to JSON with the library [json_strong_typing](https://github.com/hunyadi/strong_typing).

### Mapping function name prefixes to HTTP verbs

The following table identifies which function name prefixes map to which HTTP verbs:

| Prefix | HTTP verb   |
| ------ | ----------- |
| create | POST        |
| delete | REMOVE      |
| do     | GET or POST |
| get    | GET         |
| post   | POST        |
| put    | POST        |
| remove | REMOVE      |
| set    | PUT         |
| update | PATCH       |

If the function signature conflicts with the HTTP verb (e.g. a function name starts with `get` but has a composite type in the parameter list, which maps to a non-empty HTTP request body), the HTTP verb is automatically adjusted.

### Associating HTTP status codes with response types

By default, the library associates success responses with HTTP status code 200, and error responses with HTTP status code 500. However, it is possible to associate any Python type with any HTTP status code:

```python
specification = Specification(
    MyEndpoint,
    Options(
        server=Server(url="http://example.com/api"),
        info=Info(
            title="Example specification",
            version="1.0",
            description=description,
        ),
        success_responses={
            Student: HTTPStatus.CREATED,
            Teacher: HTTPStatus.ACCEPTED,
        },
        error_responses={
            AuthenticationError: HTTPStatus.UNAUTHORIZED,
            BadRequestError: 400,
            InternalServerError: 500,
            NotFoundError: HTTPStatus.NOT_FOUND,
            ValidationError: "400",
        },
        error_wrapper=True,
    ),
)
```

The arguments `success_responses` and `error_responses` take a dictionary that maps types to status codes. Status codes may be integers (e.g. `400`), strings (e.g. `"400"` or `"4xx"`) or [HTTPStatus](https://docs.python.org/3/library/http.html#http.HTTPStatus) enumeration values. The string representation of the status code must be valid as per the OpenAPI specification.
