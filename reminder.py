from redis_om import (Field,JsonModel)
from datetime import datetime

class Reminder(JsonModel):
    message: str = Field(index=True)
    time: str = Field(index=True)



