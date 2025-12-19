from pydantic import BaseModel


class Data(BaseModel):
    key: str = None
    value: str = None
