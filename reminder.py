from redis_om import (Field,JsonModel)
import datetime

class Reminder(JsonModel):
    message: str = Field(index=True)
    time: datetime.datetime = Field(index=True)



