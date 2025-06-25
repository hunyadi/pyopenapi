import os
import os.path
import unittest
from datetime import datetime
from http import HTTPStatus
from typing import TextIO
from uuid import UUID

from endpoint import AuthenticationError, BadRequestError, Endpoint, InternalServerError, NotFoundError, Student, Teacher, ValidationError

from pyopenapi.options import Options
from pyopenapi.specification import Info, SecuritySchemeHTTP, Server
from pyopenapi.utility import Specification

try:
    from pygments import highlight
    from pygments.formatter import Formatter
    from pygments.formatters import HtmlFormatter
    from pygments.lexers import get_lexer_by_name

    def save_with_highlight(f: TextIO, code: str, format: str) -> None:
        lexer = get_lexer_by_name(format)
        formatter: Formatter = HtmlFormatter()  # type: ignore[type-arg]
        style = formatter.get_style_defs(".highlight")
        f.writelines(
            [
                "<!DOCTYPE html>",
                "<html>",
                "<head>",
                '<meta charset="utf-8" />',
                '<meta name="viewport" content="width=device-width, initial-scale=1">',
                f"<style>{style}</style>",
                "</head>",
                "<body>",
            ]
        )
        highlight(code, lexer, formatter, outfile=f)
        f.writelines(["</body>", "</html>"])

except ImportError:

    def save_with_highlight(f: TextIO, code: str, format: str) -> None:
        pass


class ExampleType:
    """
    An example type with a few properties.

    :param uuid: Uniquely identifies this instance.
    :param count: A sample property of an integer type.
    :param value: A sample property of a string type.
    :param created_at: A timestamp. The date type is identified with OpenAPI's format string.
    :param updated_at: A timestamp.
    """

    uuid: UUID
    count: int
    value: str
    created_at: datetime
    updated_at: datetime


class UnreferencedType:
    "A type not referenced from anywhere else but passed as an additional type to the initializer of the class `Specification`."


class TestOpenAPI(unittest.TestCase):
    root: str
    specification: Specification

    def setUp(self) -> None:
        super().setUp()

        with open(os.path.join(os.path.dirname(__file__), "endpoint.md"), "r") as f:
            description = f.read()

        self.root = os.path.join(os.path.dirname(__file__), "..", "website", "examples")
        os.makedirs(self.root, exist_ok=True)
        self.specification = Specification(
            Endpoint,
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
                success_responses={
                    Student: HTTPStatus.CREATED,
                    Teacher: HTTPStatus.ACCEPTED,
                },
                error_responses={
                    AuthenticationError: HTTPStatus.UNAUTHORIZED,
                    BadRequestError: 400,
                    InternalServerError: 500,
                    NotFoundError: HTTPStatus.NOT_FOUND,
                    ValidationError: 400,
                },
                error_wrapper=True,
            ),
        )

    def test_json(self) -> None:
        json_dir = os.path.join(self.root, "json")
        os.makedirs(json_dir, exist_ok=True)

        path = os.path.join(json_dir, "openapi.json")
        with open(path, "w", encoding="utf-8") as f:
            self.specification.write_json(f, pretty_print=True)

        code = self.specification.get_json_string(pretty_print=True)
        path = os.path.join(json_dir, "index.html")
        with open(path, "w", encoding="utf-8") as f:
            save_with_highlight(f, code, "json")

    def test_yaml(self) -> None:
        try:
            import yaml

            yaml_dir = os.path.join(self.root, "yaml")
            os.makedirs(yaml_dir, exist_ok=True)

            path = os.path.join(yaml_dir, "openapi.yaml")
            with open(path, "w", encoding="utf-8") as f:
                yaml.dump(self.specification.get_json(), f, allow_unicode=True)

            code = yaml.dump(self.specification.get_json(), allow_unicode=True)
            path = os.path.join(yaml_dir, "index.html")
            with open(path, "w", encoding="utf-8") as f:
                save_with_highlight(f, code, "yaml")

        except ImportError:
            self.skipTest("package PyYAML is required for `*.yaml` output")

    def test_html(self) -> None:
        path = os.path.join(self.root, "index.html")
        with open(path, "w", encoding="utf-8") as f:
            self.specification.write_html(f, pretty_print=False)

    def test_python(self) -> None:
        source = os.path.join(os.path.dirname(__file__), "endpoint.py")
        with open(source, "r", encoding="utf-8") as f:
            code = f.read()

        python_dir = os.path.join(self.root, "python")
        os.makedirs(python_dir, exist_ok=True)
        path = os.path.join(python_dir, "openapi.py")
        with open(path, "w", encoding="utf-8") as f:
            f.write(code)

        path = os.path.join(python_dir, "index.html")
        with open(path, "w", encoding="utf-8") as f:
            save_with_highlight(f, code, "python")


if __name__ == "__main__":
    unittest.main()
