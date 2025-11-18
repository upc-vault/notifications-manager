from pydantic import BaseModel
from typing import List, Optional
from attachment import Attachment
from value import Value
from sender import Sender
from app import App
from receiver import Receiver
from datetime import datetime


class Notification(BaseModel):
    sender: Sender = None
    app: App = None
    receivers: List[Receiver] = None
    notification_type: str = None
    values: Optional[List[Value]] = None
    channels: List[str] = None
    attachments: Optional[List[Attachment]] = None
    timestamp: datetime = None
