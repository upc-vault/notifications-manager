from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class Attachment(BaseModel):
    id: str = None
    name: Optional[str] = None
    size: Optional[str] = None
    timestamp: Optional[datetime] = None
