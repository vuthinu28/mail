from datetime import datetime
from os import getcwd, remove
from fastapi import APIRouter, Depends, status
from typing import List, Union
from fastapi import File, UploadFile
from fastapi.encoders import jsonable_encoder
from fastapi.params import File, Query, Security
from fastapi.routing import APIRouter
from fastapi import Body, HTTPException, status, Depends
from bson import ObjectId
from starlette.responses import JSONResponse
from contracts.property import *
from contracts.filter import *
from config import *
from db import db
from config import settings
from contracts.role import Role
from middleware.get_current_user import get_current_user
import uuid

router = APIRouter()

# Create


@router.post("/property/create", response_model=PropertyDB)
async def create_property(property: PropertyCreateUpdate = Body(...),
                          current_user=Security(get_current_user, scopes=[
                                                Role.admin["name"]])
                          ):
    if current_user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Could not validate credentials")
    property = jsonable_encoder(property)
    img_len = len(property["images"])
    for i in range(8-img_len):
        property["images"].append(f"{settings.upload_path}/property/comming-soon.png")
    now = datetime.now()
    property.update({"createdAt": now, "modifiedAt": now})
    db_property = await db["Properties"].insert_one(property)
    created_property = await db["Properties"].find_one({"_id": db_property.inserted_id})
    return created_property

# get all


@router.get("/property", response_model=PropertyPagination)
async def get_all_property(
    page: int = Query(..., gt=0),
    size: int = Query(..., gt=0),
    current_user=Depends(get_current_user)
):
    property = db["Properties"].find({"isHide": False}).sort('createdAt', -1)
    if current_user["role"] == "admin":
        property = db["Properties"].find().sort('createdAt', -1)
    result = []
    async for item in property:
        item["_id"] = str(item["_id"])
        result.append(PropertyModel(**item))

    properties = result[size*(page-1): size*page]
    if len(properties) == 0 and page > 1:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="not found")
    response = {
        "properties": properties,
        "totalItems": len(result)
    }
    return response


# get limit property
@router.get("/property-limit", response_model=List[PropertyDB])
async def get_all_property():
    property = db["Properties"].find({"isHide": False}).sort('createdAt', -1).limit(3)
    result = []
    async for item in property:
        result.append(item)
    return result


# Detail:


@router.get("/property/{id}")
async def get_property_detail(id: str, current_user=Depends(get_current_user)):
    property = await db["Properties"].find_one({"_id": ObjectId(id)})
    if property is None or property["isHide"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")
    if current_user is None:
        return {"property": PropertyDB(**property), "isFavourite": False}
    history = current_user["history"]
    if(not property["_id"] in history):
        if(len(history) >= 50):
            history.pop()
            history.insert(0, property["_id"])
        else:
            history.insert(0, property["_id"])
    else:
        history.remove(property["_id"])
        history.insert(0, property["_id"])
    await db["Users"].update_one({"_id": current_user["_id"]}, {"$set": {"history": history}})
    isFavourite = ObjectId(id) in current_user["favourite"]
    return {"property": PropertyDB(**property), "isFavourite": isFavourite}


@router.patch("/property/{id}", response_model=PropertyDB)
async def update_property(id: str, new_property: PropertyCreateUpdate = Body(...),
                          current_user=Security(get_current_user, scopes=[
                                                Role.admin["name"]])
                          ):
    if current_user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Could not validate credentials")

    property = await db["Properties"].find_one({"_id": ObjectId(id)})
    if property is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")
    new_property = jsonable_encoder(new_property)
    img_len = len(new_property["images"])
    for i in range(8-img_len):
        new_property["images"].append(f"{settings.upload_path}/property/comming-soon.png")
    now = datetime.now()
    new_property.update({"modifiedAt": now})
    await db["Properties"].update_one({"_id": ObjectId(id)}, {"$set": new_property})
    updated_property = await db["Properties"].find_one({"_id": ObjectId(id)})
    return updated_property

# delete a property


@router.delete("/property/{id}")
async def delete_property(id: str, current_user=Security(get_current_user, scopes=[Role.admin["name"]])):
    if current_user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Could not validate credentials")

    property = await db["Properties"].find_one({"_id": ObjectId(id)})
    if property is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")
    try:
        for filename in property["images"]:
            if filename != None and "comming-soon.png" not in filename:
                remove(filename)
    except Exception:
        print("file not found")
    await db["Properties"].delete_one({"_id": ObjectId(id)})
    return JSONResponse(status_code=status.HTTP_200_OK, content={"message": "property deteted"})


# FILTER:
@router.post('/filter', response_model=ExploreFilterPagination)
async def get_filter_result(
    page: int = Query(..., gt=0),
    size: int = Query(..., gt=0),
    data: SidebarFilter = Body(...)
):
    data = jsonable_encoder(data)
    result = db["Properties"].aggregate([
        {
            '$match': {
                "option": {
                    '$in': data["option"]
                },
                "type":{
                    '$in': data["type"]
                },
                "plan":{
                    '$in': data["plan"]
                },
                "isHide" : False
            }
        },
        {"$sort": {
            "createdAt": -1
        }},
    ])
    response = []
    async for item in result:
        item["_id"] = str(item["_id"])
        response.append(PropertyModel(**item))
    filterResult = {
        "properties": response[size*(page-1): size*page],
        "totalItems": len(response),
    }
    return filterResult


# EXPLORE FILTER:

@router.post("/explore", response_model=ExploreFilterPagination)
async def get_expore_filter_result(
    page: int = Query(..., gt=0),
    size: int = Query(..., gt=0),
    data: ExploreFilter = Body(...)
):
    data = jsonable_encoder(data)
    condition_len = len(data["condition"])
    if condition_len >= 13:
        result = db["Properties"].aggregate([
            {
                '$match': {
                    "sector": data["sector"],
                    "option": data["option"],
                    "construction_year": {
                        '$gte': data["construction_year"]
                    },
                    '$and':[
                        {"cost": {'$gte': data["min_cost"]}},
                        {"cost": {'$lte': data["max_cost"]}},
                        {"square": {'$gte': data["square_min"]}},
                        {"square": {'$lte': data["square_max"]}}
                    ],
                    "type":{
                        '$in': data["type"]
                    },
                    "plan":{
                        '$in': data["plan"]
                    },
                    "isHide" : False
                }
            },
            {"$sort": {
                "createdAt": -1
            }},

        ])
    else:
        result = db["Properties"].aggregate([
            {
                '$match': {
                    "sector": data["sector"],
                    "option": data["option"],
                    "construction_year": {
                        '$gte': data["construction_year"]
                    },
                    '$and':[
                        {"cost": {'$gte': data["min_cost"]}},
                        {"cost": {'$lte': data["max_cost"]}},
                        {"square": {'$gte': data["square_min"]}},
                        {"square": {'$lte': data["square_max"]}}
                    ],
                    "type":{
                        '$in': data["type"]
                    },
                    "plan":{
                        '$in': data["plan"]
                    },
                    "condition":{
                        '$all': data["condition"]
                    },
                    "isHide" : False
                }
            },
            {"$sort": {
                "createdAt": -1
            }},

        ])
    response = []
    async for item in result:
        item["_id"] = str(item["_id"])
        response.append(PropertyModel(**item))
    filterResult = {
        "properties": response[size*(page-1): size*page],
        "totalItems": len(response),
    }
    return filterResult


@router.get("/property/attribute/{sector}")
async def get_all_attribute(sector: int):
    result = db["Properties"].aggregate([
        {
            '$match':
            {
                'sector': sector
            }
        },
        {'$unwind': "$construction_year"},
        {
            '$group': {
                '_id': 'null',
                'years': {'$addToSet': '$construction_year'}
            }
        }
    ])
    response = await result.to_list(length=1)
    return response


# SEARCH:

# SEARCH Properties
# @router.post("/search", response_model=PropertyPagination)
# async def search_property(search_content: SearchContent = Body(...),
#     page: int = Query(...,gt=0),
#     size: int = Query(...,gt=0),
# ):
#     search_content = search_content.dict()
#     result1 = db["Properties"].find({"$text":{"$search" : search_content["content"]}})
#     result2 = db["Properties"].find({"$text":{"$search" : f'"\"{search_content["content"]}\""'}})
#     response = []
#     async for item in result2:
#         item["_id"] = str(item["_id"])
#         response.append(PropertyModel(**item))
#     async for item in result1:
#         item["_id"] = str(item["_id"])
#         if PropertyModel(**item) not in response:
#             response.append(PropertyModel(**item))
#     searchResult = {
#         "properties": response[size*(page-1): size*page],
#         "totalItems": len(response),
#     }
#     return searchResult

@router.post("/property/hide/{id}", response_model=PropertyDB)
async def hide_property(id: str,current_user=Security(get_current_user, scopes=[Role.admin["name"]])):
    if current_user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Could not validate credentials")
    property = await db["Properties"].find_one({"_id": ObjectId(id)})
    if property is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")
    isHide = property["isHide"]
    property.update({"modifiedAt": datetime.now(), "isHide": not isHide})
    await db["Properties"].update_one({"_id": ObjectId(id)}, {"$set": property})
    return property