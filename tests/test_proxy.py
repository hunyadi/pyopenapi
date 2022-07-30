import unittest
from dataclasses import dataclass
from typing import Dict

from pyopenapi import webmethod
from pyopenapi.proxy import make_proxy_class
from strong_typing.schema import JsonType


@dataclass
class Document:
    title: str
    text: str


@dataclass
class HTTPBinResponse:
    args: Dict[str, str]
    headers: Dict[str, str]
    origin: str
    url: str


@dataclass
class HTTPBinPostResponse(HTTPBinResponse):
    data: str
    json: JsonType
    files: Dict[str, str]
    form: Dict[str, str]


class API:
    @webmethod(route="/get")
    def get_method(self, /, id: str) -> HTTPBinResponse:
        ...

    @webmethod(route="/put")
    def set_method(self, /, id: str, doc: Document) -> HTTPBinPostResponse:
        ...


class TestOpenAPI(unittest.IsolatedAsyncioTestCase):
    def assertDictSubset(self, subset: dict, superset: dict) -> None:
        self.assertLessEqual(subset.items(), superset.items())

    def assertResponse(
        self,
        response: HTTPBinResponse,
        params: Dict[str, str],
        headers: Dict[str, str] = None,
    ) -> None:
        self.assertIsInstance(response, HTTPBinResponse)
        self.assertDictEqual(response.args, params)
        if headers:
            self.assertDictSubset(headers, response.headers)

    async def test_http(self):
        Proxy = make_proxy_class(API)
        proxy = Proxy("http://httpbin.org")

        response = await proxy.get_method("abc")
        self.assertResponse(response, params={"id": "abc"})

        response = await proxy.set_method("abc", Document("title", "text"))
        self.assertResponse(
            response, params={"id": "abc"}, headers={"Content-Type": "application/json"}
        )


if __name__ == "__main__":
    unittest.main()
