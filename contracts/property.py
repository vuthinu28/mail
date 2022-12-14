from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional, List
from contracts.pyObjectId import PyObjectId
from bson import ObjectId


class PropertyCreateUpdate(BaseModel):
    option: str = Field(...)
    type: str = Field(...)
    title: str = Field(...)
    sector: int = Field(...)
    address: str = Field(...)
    square: int = Field(...)
    cost: int = Field(...)
    rent_in_vnd: Optional[int] = Field(None)
    deposit: str = Field(...)
    contract_period: str = Field(...)
    plan: str = Field(...)
    condition: List[str] = Field(...)
    construction_year: int = Field(...)
    equipment: List[str] = Field(...)
    bedroom: int = Field(...)
    bathroom: int = Field(...)
    images: List[str] = Field(...)
    recommendation: str = Field(...)
    isHide: bool = Field(...)
    class Config:
        schema_extra = {
            "example":{
                "option": "rent",
                "type": "apartment",
                "title": "Aqua",
                "sector": 1,
                "address": "Minh Khai str.",
                "square": 500,
                "cost": 500,
                "rent_in_vnd": 500,
                "deposit": "NAN",
                "contract_period": "long",
                "plan": "1ldk",
                "condition": ["school","bus station","gym","pool","pets allowed","hospital"],
                "construction_year": 2016,
                "equipment": ["tv", "shower"],
                "bedroom": 2,
                "bathroom":2,
                "images":[],
                "recommendation": "The apartment designed with an open living room, a balcony in front of the living room. There is a modern kitchen with built-in oven, dish washer, microwave and kitchenware. The apartment has 2 bedroom and 2 bathroom with bath-tub and walk-in shower. It has a lot of natural light, quiet and clean." 
            }
        }


class PropertyDB(BaseModel):
    id: PyObjectId = Field(alias="_id")
    option: str = Field(...)
    type: str = Field(...)
    title: str = Field(...)
    sector: int = Field(...)
    address: str = Field(...)
    square: int = Field(...)
    cost: int = Field(...)
    rent_in_vnd: Optional[int]= Field(None)
    deposit: str = Field(...)
    contract_period: str = Field(...)
    plan: str = Field(...)
    condition: List[str] = Field(...)
    construction_year: int = Field(...)
    equipment: List[str] = Field(...)
    bedroom: int = Field(...)
    bathroom: int = Field(...)
    images: List[str] = Field(...)
    createdAt: datetime = Field(...)
    modifiedAt: datetime = Field(...)
    recommendation: str = Field(...)
    isHide: bool = Field(...)

    class Config:
        json_encoders = {ObjectId: str}

class PropertyModel(BaseModel):
    id: str = Field(alias="_id")
    option: str = Field(...)
    type: str = Field(...)
    title: str = Field(...)
    sector: int = Field(...)
    address: str = Field(...)
    square: int = Field(...)
    cost: int = Field(...)
    rent_in_vnd: Optional[int]= Field(None)
    deposit: str = Field(...)
    contract_period: str = Field(...)
    plan: str = Field(...)
    condition: List[str] = Field(...)
    construction_year: int = Field(...)
    equipment: List[str] = Field(...)
    bedroom: int = Field(...)
    bathroom: int = Field(...)
    images: List[str] = Field(...)
    recommendation: str = Field(...)
    createdAt: datetime = Field(...)
    modifiedAt: datetime = Field(...)
    isHide: bool = Field(...)

    def getId(self):
        return self.id

class PropertyPagination(BaseModel):
    properties: List[PropertyModel] = Field(...)
    totalItems: int = Field(...)

class SearchContent(BaseModel):
    content: str = Field(...)