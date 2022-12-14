from typing import List
from fastapi.encoders import jsonable_encoder
from fastapi.param_functions import Security
from fastapi.routing import APIRouter
from fastapi.param_functions import Query, Security
from fastapi import Body, HTTPException, status, Depends
from bson import ObjectId
from starlette.responses import JSONResponse
from contracts.contact import *
from config import settings
from contracts.role import Role
from contracts.user import UserDB
from db import db
from middleware.get_current_user import get_current_user
from contracts.role import Role
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

from utils import send_template_email

router = APIRouter()


# CONTACT:
# Create
@router.post("/contact")
async def create_contact(contact: ContactCreate = Body(...)):
    contact = jsonable_encoder(contact)
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    contact.update({"createdAt":now, "isDone": False})
    result = await db["Contacts"].insert_one(contact)
    created_contact = await db["Contacts"].find_one({"_id": result.inserted_id})
    if created_contact is None:
        return JSONResponse(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                            content={"message": "fail to create contact"})
    return JSONResponse(status_code=status.HTTP_201_CREATED, content={"message": "success"})


# Get all
@router.get("/contact", response_model=ContactPagination)
async def get_all_contact(
    page: int = Query(...,gt=0),
    size: int = Query(...,gt=0),
    current_user: UserDB = Security(get_current_user, scopes=[Role.admin["name"]])
):
    if current_user is None:
        raise  HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")
        
    result = db["Contacts"].find({"isDone": False})
    list_contact = []
    async for item in result:
        item["_id"] = str(item["_id"])
        list_contact.append(ContactModel(**item))

    contacts = list_contact[size*(page-1) : size*page]
    if len(contacts) == 0 and page > 1:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not found")
    response = {
        "contacts": contacts,
        "totalItems": len(list_contact)
    }
    return response


# # Detail
# @router.get("/contact/{id}", response_model=ContactDB)
# async def get_contact(id: str, current_user: UserDB = Security(get_current_user, scopes=[Role.admin["name"]])):
#     contact = await db["Contacts"].find_one({"_id": ObjectId(id)})
#     if contact is None:
#         return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"message": " contact not found"})
#     return contact

@router.post("/contact/answer/{id}")
async def answer_contact(id: str, data : ContactAnswer = Body(...),
    current_user: UserDB = Security(get_current_user, scopes=[Role.admin["name"]])
):
    if current_user is None:
        raise  HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")
    data = data.dict()
    
    result = send_template_email(
        from_email="support@sunrisedanangvn.com",
        to_email=data["email"],
        subject=data["title"],
        template="answer_contact_email.html",
        name = data["name"],
        message=data["message"]
    )
    await db["Contacts"].update_one({"_id": ObjectId(id)},{"$set":{"isDone": True}})
    return result
