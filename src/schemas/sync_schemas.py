from pydantic import BaseModel


class SyncTriggerResponse(BaseModel):
    status: str
    message: str
