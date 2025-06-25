import datetime
import enum
import uuid
from dataclasses import dataclass
from typing import Callable, Generator, Optional, Protocol, Union

from strong_typing.schema import json_schema_type

from pyopenapi.decorators import webmethod


@json_schema_type(schema={"type": "string", "format": "uri", "pattern": "^https?://"})  # type: ignore
@dataclass
class URL:
    """A Uniform Resource Locator (URL).

    :param url: The URL encapsulated in this object.
    """

    url: str

    def __str__(self) -> str:
        return self.url


@json_schema_type
@dataclass
class OperationError(Exception):
    """
    Encapsulates an error from an endpoint operation.

    :param type: A machine-processable identifier for the error. Typically corresponds to the fully-qualified exception
    class (i.e. Python exception type).
    :param uuid: Unique identifier of the error. This identifier helps locate the exact source of the error (e.g. find
    the log entry in the server log stream). Make sure to include this identifier when contacting support.
    :param message: A human-readable description for the error for informational purposes. The exact format of the
    message is unspecified, and implementations should not rely on the presence of any specific information.
    """

    type: str
    uuid: uuid.UUID
    message: str


@dataclass
class AuthenticationError(OperationError):
    """
    Raised when the client fails to provide valid authentication credentials.
    """


@dataclass
class BadRequestError(OperationError):
    """
    The server cannot process the request due a client error.

    This might be due to malformed request syntax or invalid usage.
    """


@dataclass
class InternalServerError(OperationError):
    "The server encountered an unexpected error when processing the request."


@dataclass
class NotFoundError(OperationError):
    """
    Raised when an entity does not exist or has expired.

    :param id: The identifier of the entity not found, e.g. the UUID of a job.
    :param kind: The entity that is not found such as a namespace, object, person or job.
    """

    id: str
    kind: str


@dataclass
class Location:
    """
    Refers to a location in parsable text input (e.g. JSON, YAML or structured text).

    :param line: Line number (1-based).
    :param column: Column number w.r.t. the beginning of the line (1-based).
    :param character: Character number w.r.t. the beginning of the input (1-based).
    """

    line: int
    column: int
    character: int


@dataclass
class ValidationError(OperationError):
    """
    Raised when a JSON validation error occurs.

    :param location: Location of where invalid input was found.
    """

    location: Location


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

    def __str__(self) -> str:
        return f"{self.given_name} {self.family_name}"


@json_schema_type
@dataclass
class Student(Person):
    "A student at a university."

    birth_date: Optional[datetime.date] = None


@json_schema_type
@dataclass
class Teacher(Person):
    "A lecturer at a university."

    subject: str


#
# Endpoint examples
#


class JobManagement(Protocol):
    """
    Job management.

    Operations to create, inspect, update and terminate jobs.
    """

    def create_job(self, items: list[URL]) -> uuid.UUID:
        """
        Creates a new job with the given data as input.

        :param items: A set of URLs to resources used to initiate the job.
        :returns: The unique identifier of the newly created job.
        :raises BadRequestError: URL points to an invalid location.
        :raises InternalServerError: Unexpected error while creating job.
        :raises ValidationError: The input is malformed.
        """
        ...

    @webmethod(
        response_examples=[
            NotFoundError(
                "NotFoundException",
                uuid.UUID("123e4567-e89b-12d3-a456-426614174000"),
                "Job does not exist.",
                "12345678-1234-5678-1234-567812345678",
                "job",
            )
        ],
    )
    def get_job(self, job_id: uuid.UUID, /, format: Format) -> Job:
        """
        Query status information about a job.

        :param job_id: Unique identifier for the job to query.
        :returns: Status information about the job.
        :raises NotFoundError: The job does not exist.
        :raises ValidationError: The input is malformed.
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
        :raises ValidationError: The input is malformed.
        """
        ...

    def get_status(self, job_id: uuid.UUID, /) -> Generator[StatusEvent, None, StatusResponse]:
        """
        Provides asynchronous status information about a job.

        This operation is defined with the special return type of `Generator`. `Generator[Y,S,R]` has the yield type
        `Y`, the send type `S` of `None`, and the return type `R`. `R` is the response type immediately returned by
        a call to this operation. However, the client will receive out-of-band events of type `Y` over a different
        channel, e.g. a websocket connection or an HTTP callback.
        """

    # a list of out-of-band events triggered by the endpoint asynchronously
    data_event: Callable[[DataEvent], None]


class PeopleCatalog(Protocol):
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

    @webmethod(
        route="/member/name/{family}/{given}",
        response_examples=[
            Student("Szörnyeteg", "Lajos"),
            Student("Ló", "Szerafin"),
            Student("Bruckner", "Szigfrid"),
            Student("Nagy", "Zoárd"),
            Teacher("Mikka", "Makka", "Négyszögletű Kerek Erdő"),
            Teacher("Vacska", "Mati", "Négyszögletű Kerek Erdő"),
        ],
    )
    def get_member_by_name(self, family: str, given: str, /) -> Union[Student, Teacher]:
        """
        Find a member by their name.

        This operation has multiple response payload types.
        """
        ...


#
# Authentication and authorization
#


@dataclass
class Credentials:
    """
    Authentication credentials.

    :param client_id: An API key.
    :param client_secret: The secret that corresponds to the API key.
    """

    client_id: str
    client_secret: str


@dataclass
class TokenProperties:
    """
    Authentication/authorization token issued in response to an authentication request.

    :param access_token: A base64-encoded access token string with header, payload and signature parts.
    :param expires_at: Expiry of the access token. This field is informational, the timestamp is also embedded in the access token.
    """

    access_token: str
    expires_at: datetime.datetime


class Endpoint(JobManagement, PeopleCatalog, Protocol):
    @webmethod(route="/auth", public=True)
    def do_authenticate(self, credentials: Credentials) -> TokenProperties:
        """
        Issues a JSON Web Token (JWT) to be passed to API calls.

        :raises AuthenticationError: Client lacks valid authentication credentials.
        :raises ValidationError: The input is malformed.
        """
        ...
