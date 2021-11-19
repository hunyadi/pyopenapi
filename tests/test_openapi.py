import os.path
import unittest

from pyopenapi import Info, Options, Server, Specification

from endpoint import Endpoint


class TestOpenAPI(unittest.TestCase):
    specification: Specification

    def setUp(self) -> None:
        super().setUp()

        self.specification = Specification(
            Endpoint,
            Options(
                server=Server(url="/api"),
                info=Info(title="Example specification", version="1.0"),
            ),
        )

    def test_json(self):
        path = os.path.join(os.path.dirname(__file__), "test_openapi.json")
        with open(path, "w", encoding="utf-8") as f:
            self.specification.write_json(f)

    def test_yaml(self):
        try:
            import yaml

            path = os.path.join(os.path.dirname(__file__), "test_openapi.yaml")
            with open(path, "w", encoding="utf-8") as f:
                yaml.dump(self.specification.get_json(), f, allow_unicode=True)

        except ImportError:
            self.skipTest("package PyYAML is required for `*.yaml` output")

    def test_html(self):
        path = os.path.join(os.path.dirname(__file__), "test_openapi.html")
        with open(path, "w", encoding="utf-8") as f:
            self.specification.write_html(f)


if __name__ == "__main__":
    unittest.main()
