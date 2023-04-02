from redis_om import (Field,JsonModel,EmbeddedJsonModel)
from typing import List,Dict
from datetime import datetime

class Note(JsonModel):
    message: str = Field(index=True)
    time: str = Field(index=True,default=str(round(datetime.now().timestamp())))
class NoteBag(JsonModel):
    name: str = Field(index=True)
    notes: List[Note] = Field(index=True,default=[])

class MasterNoteBag(JsonModel):
    notebags: List[NoteBag] = Field(index=True,default=[NoteBag(name="main")])

class Settings(JsonModel):
    idea_stream_public: str = Field(index=True,default="false")

class Quote(JsonModel):
    quote: str = Field(index=True)

class User(JsonModel):
    username: str = Field(index=True)
    password: str = Field(index=True)
    phone: str = Field(index=True)
    notebags: List[NoteBag] = Field(index=True,default=[NoteBag(name='main')])
    master_notebag: MasterNoteBag = Field(index=True,default=MasterNoteBag())
    quotes: List[Quote] = Field(index=True,default=[Quote(quote="default")])
    links: List[str] = Field(index=True,default=["https://www.google.com"])
    settings: Settings = Field(index=True,default=Settings()) 

class Reminder(JsonModel):
    user: str = Field(index=True)
    message: str = Field(index=True)
    time: int = Field(index=True)
    reoccurring: str = Field(index=True,default="false")
    remind_method: str = Field(index=True,default="text")

class Idea(JsonModel):
    user: str = Field(index=True)
    message: str = Field(index=True,full_text_search=True)
    time: int = Field(index=True,default=int(round(datetime.now().timestamp())))

class Timer(JsonModel):
    user: str = Field(index=True)
    time: int = Field(index=True)
   
