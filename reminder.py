from redis_om import (Field,JsonModel)

class Reminder(JsonModel):
    message: str = Field(index=True)
    time: str = Field(index=True)


