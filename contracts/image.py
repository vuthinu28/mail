from typing import List
from pydantic import BaseModel
from pydantic.fields import Field

class DeleteImage(BaseModel):
    images: List[str] = Field(...)
    type: str = Field(...)