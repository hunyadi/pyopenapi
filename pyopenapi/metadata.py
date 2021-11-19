from dataclasses import dataclass


@dataclass
class WebMethod:
    "Additional metadata tied to an endpoint operation function."

    route: str
