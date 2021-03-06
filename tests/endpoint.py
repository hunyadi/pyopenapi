import datetime
import enum
import uuid
from dataclasses import dataclass
from typing import Callable, Generator, List

from pyopenapi import webmethod
from strong_typing.schema import json_schema_type


@json_schema_type(schema={"type": "string", "format": "uri", "pattern": "^https?://"})
@dataclass
class URL:
    """A Uniform Resource Locator (URL).

    :param url: The URL encapsulated in this object.
    """

    url: str

    def __str__(self):
        return self.url


class Status(enum.Enum):
    "Status of a job."

    Created = "created"
    Running = "running"
    Stopped = "stopped"


class Format(enum.Enum):
    "Possible representation formats."

    HTML = "text/html"
    Plain = "text/plain"
    Markdown = "text/markdown"


@json_schema_type
@dataclass
class Description:
    """
    A textual description as plain text or a well-known markup format.

    :param format: The representation format for the text.
    :param text: The text string.
    """

    format: Format
    text: str


@json_schema_type
@dataclass
class Job:
    """
    A unit of execution.

    :param id: Job identifier.
    :param status: Current job status.
    :param started_at: The timestamp (in UTC) when the job was started.
    :param description: Additional information associated with the job.
    """

    id: uuid.UUID
    status: Status
    started_at: datetime.datetime
    description: Description


@json_schema_type
@dataclass
class StatusResponse:
    """
    Triggered synchronously as the immediate response to an asynchronous operation.

    This response serves as an acknowledgment, and may be followed by several out-of-band events, transmitted e.g. over a websocket connection.

    :param id: Uniquely identifies the job which the response corresponds to.
    :param description: Textual description associated with the response.
    """

    id: uuid.UUID
    description: str


@json_schema_type
@dataclass
class StatusEvent:
    """
    Triggered when an out-of-band event takes place.

    This message is typically transmitted in a separate channel, e.g. over a websocket connection.

    :param id: Uniquely identifies the job which the event corresponds to.
    :param status: The current status of the job.
    """

    id: uuid.UUID
    status: Status


@dataclass
class DataEvent:
    data: bytes


@json_schema_type
@dataclass
class Person:
    """
    Represents a real person.

    :param family_name: The person's family name (typically last name).
    :param given_name: The person's given name (typically first name).
    """

    family_name: str
    given_name: str


class JobManagement:
    """
    Job management.

    Operations to create, inspect, update and terminate jobs.
    """

    def create_job(self, items: List[URL]) -> uuid.UUID:
        """
        Creates a new job with the given data as input.

        :param items: A set of URLs to resources used to initiate the job.
        :return: The unique identifier of the newly created job.
        """
        ...

    def get_job(self, job_id: uuid.UUID, /, format: Format) -> Job:
        """
        Query status information about a job.

        :param job_id: Unique identifier for the job to query.
        :return: Status information about the job.
        """
        ...

    def remove_job(self, job_id: uuid.UUID, /) -> None:
        """
        Terminates a job.

        :param job_id: Unique identifier for the job to terminate.
        """
        ...

    def update_job(self, job_id: uuid.UUID, /, job: Job) -> None:
        """
        Updates information related to a job.

        May cause the job to be stopped and restarted.

        :param job_id: Unique identifier for the job to update.
        :param job: Data to update the job with.
        """
        ...

    def get_status(
        self, job_id: uuid.UUID, /
    ) -> Generator[StatusEvent, None, StatusResponse]:
        """
        Provides asynchronous status information about a job.

        This operation is defined with the special return type of `Generator`. `Generator[Y,S,R]` has the yield type
        `Y`, the send type `S` of `None`, and the return type `R`. `R` is the response type immediately returned by
        a call to this operation. However, the client will receive out-of-band events of type `Y` over a different
        channel, e.g. a websocket connection or an HTTP callback.
        """

    # a list of out-of-band events triggered by the endpoint asynchronously
    data_event: Callable[[DataEvent], None]


class PeopleCatalog:
    """
    Operations related to people.
    """

    @webmethod(route="/person/id/{id}")
    def get_person_by_id(self, id: str, /) -> Person:
        """
        Find a person by their identifier.

        This operation has a custom route associated with it.
        """
        ...

    @webmethod(
        route="/person/name/{family}/{given}",
        response_example=Person("Hunyadi", "Levente"),
    )
    def get_person_by_name(self, family: str, given: str, /) -> Person:
        """
        Find a person by their name.

        This operation has a custom route associated with it.
        """
        ...


class Endpoint(JobManagement, PeopleCatalog):
    pass
