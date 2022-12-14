from typing import List
from pydantic import BaseModel
from pydantic.fields import Field
from contracts.pyObjectId import *
import datetime


class ContactCreate(BaseModel):
    email: str = Field(...)
    name: str = Field(...)
    category: str = Field(...)
    title: str = Field(...)
    message: str = Field(...)

    class Config:
        schema_extra = {
            "example": {
                "email": "htduc00@gmail.com",
                "name": "Duc Hoang",
                "category": "asd",
                "title": "",
                "message": ""
            }
        }


class ContactDB(BaseModel):
    id: PyObjectId = Field(alias="_id")
    email: str = Field(...)
    name: str = Field(...)
    category: str = Field(...)
    title: str = Field(...)
    message: str = Field(...)
    createdAt: str = Field(...)
    isDone: bool = Field(...)

    class Config:
        json_encoders = {ObjectId: str}

class ContactModel(BaseModel):
    id: str = Field(alias="_id")
    email: str = Field(...)
    name: str = Field(...)
    category: str = Field(...)
    title: str = Field(...)
    message: str = Field(...)
    createdAt: str = Field(...)
    isDone: bool = Field(...)

class ContactPagination(BaseModel):
    contacts: List[ContactModel] =  Field(...)
    totalItems: int = Field(...)

class ContactAnswer(BaseModel):
    name:str=Field(...)
    title: str = Field(...)
    email: str = Field(...)
    message: str = Field(...)
