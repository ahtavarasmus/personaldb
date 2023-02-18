from redis_om import (Field,JsonModel,EmbeddedJsonModel)


class User(JsonModel):
    username: str = Field(index=True)
    password: str = Field(index=True)
    phone: str = Field(index=True)

class Reminder(JsonModel):
    user: str = Field(index=True)
    message: str = Field(index=True)
    time: int = Field(index=True)

class Idea(JsonModel):
    user: str = Field(index=True)
    message: str = Field(index=True,full_text_search=True)



