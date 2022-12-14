from os import remove
from typing import List
from fastapi import Body, HTTPException, status
from fastapi import APIRouter
from fastapi.datastructures import UploadFile
from fastapi.encoders import jsonable_encoder
from fastapi.params import File
from bson import ObjectId
from starlette import responses
from starlette.responses import JSONResponse
from contracts.post import *
from config import *
from db import db
from contracts.role import Role
from fastapi.param_functions import Query, Security
from config import settings
from middleware.get_current_user import get_current_user
from datetime import datetime

router = APIRouter()

# POST:
# Create
@router.post("/post/create", response_model=PostDB)
async def create_post(post: PostCreateUpdate = Body(...),
    current_user=Security(get_current_user, scopes=[Role.admin["name"]])
):
    if current_user is None:
        raise  HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")

    now = datetime.now()
    year = datetime.now().strftime("%Y")
    month = datetime.now().strftime("%m")
    day = datetime.now().strftime("%d")
    now_in_ja=year+'年'+month+'月'+day+'日'
    post = jsonable_encoder(post)
    post.update({"createdAt": now, "modifiedAt": now_in_ja})
    post_db = await db["Posts"].insert_one(post)
    created_post = await db["Posts"].find_one({"_id": post_db.inserted_id})
    if created_post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="create fail")
    return created_post

# get all
@router.get("/post", response_model=PostPagination)
async def get_all_posts(page: int = Query(..., gt=0), size: int = Query(...,gt=0)):
    posts = db["Posts"].find().sort('createdAt', -1)
    list_posts = []
    async for post in posts:
        post["_id"] = str(post["_id"])
        list_posts.append(PostModel(**post))

    posts = list_posts[size*(page-1) : size*page]
    if len(posts) == 0 and page > 1:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not found")
    response = {
        "posts": posts,
        "totalItems": len(list_posts)
    }
    return response

# get limit posts in homepage
@router.get("/post-limit", response_model=List[PostDB])
async def get_limit_posts():
    posts = db["Posts"].find().sort('createdAt', -1).limit(10)
    list_posts = []
    async for post in posts:
        list_posts.append(post)
    return list_posts

# get a single post
@router.get("/post/{id}", response_model=PostDB)
async def get_a_post(id: str):
    post = await db["Posts"].find_one({"_id": ObjectId(id)})
    if post is None:
        raise HTTPException(status_code=404, detail="post not found")
    return post


# update a post


@router.patch("/post/{id}", response_model=PostDB)
async def update_post(id: str, new_post: PostCreateUpdate = Body(...),
    current_user=Security(get_current_user, scopes=[Role.admin["name"]])
):
    if current_user is None:
        raise  HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")

    post = await db["Posts"].find_one({"_id": ObjectId(id)})
    if post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="post not found")
    # now = datetime.now()
    # year = datetime.now().strftime("%Y")
    # month = datetime.now().strftime("%m")
    # day = datetime.now().strftime("%d")
    # now_in_ja=year+'年'+month+'月'+day+'日'
    new_post = jsonable_encoder(new_post)
    # new_post.update({"modifiedAt": now_in_ja})
    await db["Posts"].update_one(
        {"_id": ObjectId(id)}, {"$set":new_post})
    updated_post = await db["Posts"].find_one({"_id": ObjectId(id)})
    return updated_post


# delete a post


@router.delete("/post/{id}")
async def delete_post(id: str, current_user=Security(get_current_user, scopes=[Role.admin["name"]])):
    if current_user is None:
        raise  HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")
        
    post = await db["Posts"].find_one({"_id": ObjectId(id)})
    if post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="post not found")
    try:
        remove(post["thumbnail"])
        for filename in post["images"]:
            if filename != None and "comming-soon.png" not in filename:
                remove(filename)
    except Exception:
        print("file not found")
    await db["Posts"].delete_one({"_id": ObjectId(id)})
    return JSONResponse(status_code=status.HTTP_200_OK, content={"message": "post deleted"})
