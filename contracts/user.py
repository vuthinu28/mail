from pydantic import BaseModel, Field
from contracts.pyObjectId import *
from contracts.property import *


class UserDB(BaseModel):
    id: PyObjectId = Field(alias="_id")
    email: str = Field(...)
    state: str = Field(...)
    otp:str = Field(...)
    password: str = Field(...)
    gender: str = Field(...)
    name: str = Field(...)
    given_name: str = Field(...)
    family_name: str = Field(...)
    role: str = Field(...)
    history: List[PyObjectId] = Field(...)
    favourite: List[PyObjectId] = Field(...)
    createdAt: str = Field(...)
    modifiedAt: str = Field(...)

    class Config:
        json_encoders = {ObjectId: str}


class UserRegistrationStep1(BaseModel):
    email: str = Field(...)

    class Config:
        schema_extra = {
            "example": {
                "email": "damhieu2808@gmail.com"
            }
        }


class UserRegistrationStep2(BaseModel):
    email: str = Field(...)
    code: str = Field(...)
    class Config:
        schema_extra = {
            "example": {
                "email": "damhieu2808@gmail.com",
                "code": ""
            }
        }


class UserRegistrationStep4(BaseModel):
    email: str = Field(...)
    name: str = Field(...)
    given_name: str = Field(...)
    family_name: str = Field(...)
    password: str = Field(...)
    gender: str = Field(...)
    otp: str = Field(...)

    class Config:
        schema_extra = {
            "example": {
                "email": "htduc00@gmail.com",
                "name": "duchoang",
                "given_name": "Duc",
                "family_name": "Hoang",
                "password": "123456",
                "gender": "Male"
            }
        }

class ForgotPassword(BaseModel):
    email: str = Field(...)

class ResetPassword(BaseModel):
    token: str = Field(...)
    new_password: str = Field(...)

class UserLogin(BaseModel):
    email: str = Field(...)
    password: str = Field(...)