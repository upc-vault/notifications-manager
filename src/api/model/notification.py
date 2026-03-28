from pydantic import BaseModel
from typing import List
from model.attachment import Attachment
from model.sender import Sender
from model.receiver import Receiver
from model.data import Data
from datetime import datetime


class Notification(BaseModel):
    id: str = None
    sender: Sender
    receiver: Receiver
    channelCode: str
    notificationType: str
    data: List[Data] = None
    attachments: List[Attachment] = None
    sendingTime: datetime
