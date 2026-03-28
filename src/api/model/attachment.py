from pydantic import BaseModel
from datetime import datetime


class Attachment(BaseModel):
    id: str
    name: str = None
    size: str = None
    timestamp: datetime = None
