from pydantic import BaseModel, Field
from typing import Optional, List

from contracts.property import PropertyModel


class ExploreFilter(BaseModel):
    sector: int = Field(...)
    option: str = Field(...)
    type: List[str] = Field(...)
    square_max: int = Field(...)
    square_min: int  = Field(...)
    min_cost: int  = Field(...)
    max_cost: int = Field(...)
    condition: List[str] = Field(...)
    plan: List[str] = Field(...)
    construction_year: int = Field(...)

    class Config:
        schema_extra = {
            "example": {
                "sector": 1,
                "option": "rent",
                "type": ["property", "office", "apartment"],
                "square_max": 800,
                "square_min": 200,
                "cost": 10000,
                "condition": ["school", "market"],
                "plan": ["studio", "1LDK"],
                "construction_year": [2015]
            }
        }

class ExploreFilterPagination(BaseModel):
    properties: List[PropertyModel]
    totalItems: int

class SidebarFilter(BaseModel):
    option: List[str] = Field(...)
    type: List[str] = Field(...)
    plan: List[str] = Field(...)

    class Config:
        schema_extra = {
            "example": {
                "option": ["rent"],
                "type": ["apartment"],
                "plan": ["studio", "1LDK"],
            }
        }

