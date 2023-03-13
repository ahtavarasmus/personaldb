from redis_om import (Field,JsonModel,EmbeddedJsonModel)
from typing import List,Dict
from datetime import datetime

class Settings(EmbeddedJsonModel):
    idea_stream_public: bool = Field(index=True,default=False)

class User(JsonModel):
    username: str = Field(index=True)
    password: str = Field(index=True)
    phone: str = Field(index=True)
    ideas: List[str] = Field(index=True) # on halt atm
    #settings: Settings = Field(default=Settings())

class Reminder(JsonModel):
    user: str = Field(index=True)
    message: str = Field(index=True)
    time: int = Field(index=True)

class Idea(JsonModel):
    user: str = Field(index=True)
    message: str = Field(index=True,full_text_search=True)
    time: int = Field(index=True,default=int(round(datetime.now().timestamp())))

class Timer(JsonModel):
    user: str = Field(index=True)
    time: int = Field(index=True)

class NoteBag(JsonModel):
    user: str = Field(index=True)
    name: str = Field(index=True)

class Note(JsonModel):
    user: str = Field(index=True)
    bag: str = Field(index=True)
    message: str = Field(index=True)
    time: int = Field(index=True,default=int(round(datetime.now().timestamp())))
    

