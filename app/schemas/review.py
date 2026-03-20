from datetime import datetime

from pydantic import BaseModel


class ReviewQueueItemOut(BaseModel):
    request_id: str
    status: str
    created_at: datetime