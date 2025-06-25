import unittest
from dataclasses import dataclass
from typing import Optional, Protocol, TypeVar

from strong_typing.core import JsonType

from pyopenapi.decorators import webmethod
from pyopenapi.proxy import make_proxy_class

K = TypeVar("K")
V = TypeVar("V")


@dataclass
class Document:
    title: str
    text: str


@dataclass
class HTTPBinResponse:
    args: dict[str, str]
    headers: dict[str, str]
    origin: str
    url: str


@dataclass
class HTTPBinPostResponse(HTTPBinResponse):
    data: str
    json: JsonType
    files: dict[str, str]
    form: dict[str, str]


class API(Protocol):
    @webmethod(route="/get")
    async def get_method(self, /, id: str) -> HTTPBinResponse: ...

    @webmethod(route="/put")
    async def set_method(self, /, id: str, doc: Document) -> HTTPBinPostResponse: ...


class TestOpenAPI(unittest.IsolatedAsyncioTestCase):
    def assertDictSubset(self, subset: dict[K, V], superset: dict[K, V]) -> None:
        self.assertLessEqual(subset.items(), superset.items())

    def assertResponse(
        self,
        response: HTTPBinResponse,
        params: dict[str, str],
        headers: Optional[dict[str, str]] = None,
    ) -> None:
        self.assertIsInstance(response, HTTPBinResponse)
        self.assertDictEqual(response.args, params)
        if headers:
            self.assertDictSubset(headers, response.headers)

    async def test_http(self) -> None:
        Proxy = make_proxy_class(API)  # type: ignore
        proxy = Proxy("http://httpbin.org")  # type: ignore

        response = await proxy.get_method("abc")
        self.assertResponse(response, params={"id": "abc"})

        response = await proxy.set_method("abc", Document("title", "text"))
        self.assertResponse(response, params={"id": "abc"}, headers={"Content-Type": "application/json"})


if __name__ == "__main__":
    unittest.main()
