# Generate an OpenAPI specification from a Python class

*PyOpenAPI* produces an OpenAPI specification in JSON, YAML or HTML format with endpoint definitions extracted from member functions of a strongly-typed Python class.

## Features

* supports standard and asynchronous functions (`async def`)
* maps function name prefixes such as `get_` or `create_` to HTTP GET, POST, PUT, DELETE, PATCH
* handles both simple and composite types (`int`, `str`, `Enum`, `@dataclass`)
* maps Python positional-only and keyword-only arguments (of simple types) to path and query parameters, respectively
* maps composite types to HTTP request body
* supports user-defined routes with decorator `@webmethod`
* extracts description text from class and function docstrings (`__doc__`)
* recognizes parameter description text given in reStructuredText docstring format (`:param name: ...`)
* recursively converts composite types into JSON schemas
* groups frequently used composite types into a separate section and re-uses them with `$ref`
* displays generated OpenAPI specification in HTML with [ReDoc](https://github.com/Redocly/redoc)

## Examples

* [Endpoint definition in Python](https://hunyadi.github.io/pyopenapi/examples/python/index.html)
* [Generated OpenAPI specification in JSON](https://hunyadi.github.io/pyopenapi/examples/json/index.html)
* [Generated OpenAPI specification in YAML](https://hunyadi.github.io/pyopenapi/examples/yaml/index.html)
* [Generated OpenAPI specification in HTML with ReDoc](https://hunyadi.github.io/pyopenapi/examples/index.html)
