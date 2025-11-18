from pydantic import BaseModel


class Value(BaseModel):
    id: str = None
    name: str = None
