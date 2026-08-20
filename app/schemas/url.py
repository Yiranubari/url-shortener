from typing import Annotated

from pydantic import BaseModel, Field, HttpUrl


class ShortenRequest(BaseModel):
    url: Annotated[HttpUrl, Field(max_length=2048)]


class ShortenResponse(BaseModel):
    short_url: str
    long_url: str
    short_code: str

