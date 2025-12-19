from pydantic import BaseModel
from typing import List, Optional
from model.attachment import Attachment
from model.sender import Sender
from model.receiver import Receiver
from model.data import Data
from datetime import datetime


class Notification(BaseModel):
    id: str = None
    sender: Sender = None
    receiver: Receiver = None
    channelCode: str = None
    notificationType: str = None
    data: Optional[List[Data]] = None
    attachments: Optional[List[Attachment]] = None
    sendingTime: datetime = None
