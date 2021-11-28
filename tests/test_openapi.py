import os
import os.path
from typing import TextIO
import unittest

from pyopenapi import Info, Options, Server, Specification

from endpoint import Endpoint


try:
    from pygments import highlight
    from pygments.lexers import get_lexer_by_name
    from pygments.formatters import HtmlFormatter

    def save_with_highlight(f: TextIO, code: str, format: str) -> None:
        lexer = get_lexer_by_name(format)
        formatter = HtmlFormatter()
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


class TestOpenAPI(unittest.TestCase):
    root: str
    specification: Specification

    def setUp(self) -> None:
        super().setUp()

        self.root = os.path.join(os.path.dirname(__file__), "..", "examples")
        os.makedirs(self.root, exist_ok=True)
        self.specification = Specification(
            Endpoint,
            Options(
                server=Server(url="/api"),
                info=Info(title="Example specification", version="1.0"),
            ),
        )

    def test_json(self):
        json_dir = os.path.join(self.root, "json")
        os.makedirs(json_dir, exist_ok=True)

        path = os.path.join(json_dir, "openapi.json")
        with open(path, "w", encoding="utf-8") as f:
            self.specification.write_json(f, pretty_print=True)

        code = self.specification.get_json_string(pretty_print=True)
        path = os.path.join(json_dir, "index.html")
        with open(path, "w", encoding="utf-8") as f:
            save_with_highlight(f, code, "json")

    def test_yaml(self):
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

    def test_html(self):
        path = os.path.join(self.root, "index.html")
        with open(path, "w", encoding="utf-8") as f:
            self.specification.write_html(f, pretty_print=False)

    def test_python(self):
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
