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

    def write_json(self, f: TextIO) -> None:
        json_doc = self.get_json()
        json.dump(json_doc, f, check_circular=False, ensure_ascii=False, indent=4)

    def write_html(self, f: TextIO) -> None:
        json_doc = self.get_json()

        html_template_path = os.path.join(os.path.dirname(__file__), "template.html")
        with open(html_template_path, "r") as html_template_file:
            html_template = html_template_file.read()

        html = html_template.replace(
            "{ /* OPENAPI_SPECIFICATION */ }",
            json.dumps(
                json_doc,
                check_circular=False,
                ensure_ascii=False,
                separators=(",", ":"),
            ),
        )

        f.write(html)
