from pydantic import BaseModel


class Receiver(BaseModel):
    id: str = None
