from redis_om import (Field,JsonModel)

class Reminder(JsonModel):
    message: str = Field(index=True)
    time: int = Field(index=True)



