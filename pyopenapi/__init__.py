import json
import os.path
from typing import Callable, TextIO, Type

from strong_typing import JsonType, object_to_json

from .generator import Generator
from .metadata import WebMethod
from .options import *
from .specification import Document


def webmethod(route: str):
    "Decorator that supplies additional metadata to an endpoint operation function."

    def wrap(cls: Callable):
        cls.__webmethod__ = WebMethod(route=route)
        return cls

    return wrap


class Specification:
    document: Document

    def __init__(self, endpoint: Type, options: Options):
        generator = Generator(endpoint)
        self.document = generator.generate(options)

    def get_json(self) -> JsonType:
        """
        Returns the OpenAPI specification as a Python data type (e.g. `dict` for an object, `list` for an array).

        The result can be serialized to a JSON string with `json.dump` or `json.dumps`.
        """

        json_doc = object_to_json(self.document)

        # rename vendor-specific properties
        tag_groups = json_doc.pop("tagGroups", None)
        if tag_groups:
            json_doc["x-tagGroups"] = tag_groups
        tags = json_doc.get("tags")
        if tags:
            for tag in tags:
                display_name = tag.pop("displayName", None)
                if display_name:
                    tag["x-displayName"] = display_name

        return json_doc

    def get_json_string(self, pretty_print: bool = False) -> str:
        """
        Returns the OpenAPI specification as a JSON string.

        :param pretty_print: Whether to use line indents to beautify the output.
        """

        json_doc = self.get_json()
        if pretty_print:
            return json.dumps(
                json_doc, check_circular=False, ensure_ascii=False, indent=4
            )
        else:
            return json.dumps(
                json_doc,
                check_circular=False,
                ensure_ascii=False,
                separators=(",", ":"),
            )

    def write_json(self, f: TextIO, pretty_print: bool = False) -> None:
        """
        Writes the OpenAPI specification to a file as a JSON string.

        :param pretty_print: Whether to use line indents to beautify the output.
        """

        json_doc = self.get_json()
        if pretty_print:
            json.dump(json_doc, f, check_circular=False, ensure_ascii=False, indent=4)
        else:
            json.dump(
                json_doc,
                f,
                check_circular=False,
                ensure_ascii=False,
                separators=(",", ":"),
            )

    def write_html(self, f: TextIO, pretty_print: bool = False) -> None:
        """
        Creates a stand-alone HTML page for the OpenAPI specification with ReDoc.

        :param pretty_print: Whether to use line indents to beautify the JSON string in the HTML file.
        """

        html_template_path = os.path.join(os.path.dirname(__file__), "template.html")
        with open(html_template_path, "r") as html_template_file:
            html_template = html_template_file.read()

        html = html_template.replace(
            "{ /* OPENAPI_SPECIFICATION */ }",
            self.get_json_string(pretty_print=pretty_print),
        )

        f.write(html)