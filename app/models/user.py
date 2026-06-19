from datetime import datetime
from uuid import uuid4

from pydantic import BaseModel, Field


def generate_id():
    return str(uuid4())


def generate_date():
    return str(datetime.now())


class User(BaseModel):
    id: str = Field(default_factory=generate_id)
    username: str
    age: int
    created_at: str = Field(default_factory=generate_date)
