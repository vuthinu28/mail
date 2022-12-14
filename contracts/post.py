from pydantic import BaseModel, Field
from typing import List, Optional
from contracts.pyObjectId import *
from datetime import datetime

class PostCreateUpdate(BaseModel):
    title: str = Field(...)
    content: str = Field(...)
    thumbnail: str = Field(...)
    images: List[str] = Field(...)

    class Config:
        schema_extra = {
            "example": {
                "title": "Danang FantastiCity",
                "content": "<h3>Lorem ipsum dolor sit amet</h3>, <p>consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.</p>",
                "thumbnail": "",
            }
        }


class PostDB(BaseModel):
    id: PyObjectId = Field(alias="_id")
    title: str = Field(...)
    content : str = Field(...)
    createdAt: datetime = Field(...)
    modifiedAt: str = Field(...)
    thumbnail: str = Field(...)
    images: List[str] = Field(...)

    class Config:
        json_encoders = {ObjectId: str}

class PostModel(BaseModel):
    id: str = Field(alias="_id")
    title: str = Field(...)
    content : str = Field(...)
    createdAt: datetime = Field(...)
    modifiedAt: str = Field(...)
    thumbnail: str = Field(...)
    images: List[str] = Field(...)

class PostPagination(BaseModel):
    posts: List[PostModel] = Field(...)
    totalItems: int = Field(...)