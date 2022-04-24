import datetime
import enum
import uuid
from dataclasses import dataclass
from typing import Callable, List

from pyopenapi import webmethod
from strong_typing.schema import json_schema_type


@json_schema_type(schema={"type": "string", "format": "uri", "pattern": "^https?://"})
@dataclass
class URL:
    "A Uniform Resource Locator (URL)."

    url: str

    def __str__(self):
        return self.url


class Status(enum.Enum):
    Created = "created"
    Running = "running"
    Stopped = "stopped"


class Format(enum.Enum):
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
    id: uuid.UUID
    status: Status
    started_at: datetime.datetime
    description: Description


@json_schema_type
@dataclass
class EventObject:
    """
    Triggered when an out-of-band event takes place.

    :param id: Uniquely identifies the job which the event corresponds to.
    :param description: Textual description of the event.
    """

    id: uuid.UUID
    description: str


@json_schema_type
@dataclass
class Person:
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

    # a list of events triggered by the endpoint asynchronously
    job_event: Callable[[Job], None]
    data_event: Callable[[EventObject], None]


class PeopleCatalog:
    """
    Operations related to people.
    """

    @webmethod(route="/person/id/{id}")
    def get_person_by_id(self, id: str, /) -> Person:
        """
        Find a person by their identifier.
        """
        ...

    @webmethod(route="/person/name/{family}/{given}")
    def get_person_by_name(self, family: str, given: str, /) -> Person:
        """
        Find a person by their name.
        """
        ...


class Endpoint(JobManagement, PeopleCatalog):
    pass
