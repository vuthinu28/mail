from fastapi import APIRouter, Form
from fastapi.param_functions import Query, Security
from fastapi.security import OAuth2PasswordRequestForm
from fastapi import Body, HTTPException, status, Depends
from fastapi.encoders import jsonable_encoder
from jose import jwt
from starlette.responses import JSONResponse
from passlib.context import CryptContext
from config import settings
from bson import ObjectId
from contracts.filter import ExploreFilterPagination
from contracts.user import *
from contracts.token import *
from contracts.role import Role
from db import db
from middleware.get_current_user import get_current_user
import random
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import datetime
from utils import send_template_email

router = APIRouter()

# USER
# REGISTRATION:


def get_hashed_password(password: str):
    return CryptContext(schemes=["bcrypt"], deprecated="auto").hash(password)
# Step 1:

@router.post("/user/registration/step-1")
async def Registration_step1(data: UserRegistrationStep1):
    email = data.dict()["email"]
    
    code = f"{int(random.random()*1000000):06d}"  
    expire_at = datetime.datetime.now() + datetime.timedelta(minutes=30)
    
    user = await db["Users"].find_one({"email": email})
    
    if user is not None and user["state"] == "created":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="email_already_used")
    elif user is not None and ( user["state"] == "active" or user["state"] == "inactive"):
        await db["Users"].update_one({"email": email}, {"$set": {"state": "inactive","otp":code,"otp_expiration":expire_at}})
    else:
        await db["Users"].insert_one({"email": email, "state": "inactive", "otp":code, "otp_expiration":expire_at})     
    
    result = send_template_email(
        from_email="support@sunrisedanangvn.com",
        to_email= email,
        subject="「ワッツアップダナン」ご登録の確認",
        template="verification_email.html",
        code = code,
        duration=30
    )
    return result

# Step 2:

@router.post("/user/registration/step-2")
async def Registration_step2(data: UserRegistrationStep2):
    data = data.dict()
    code_input = data["code"]
    email_input = data["email"]
    user = await db["Users"].find_one({"email": email_input})
    code = user['otp']
    if code_input == code and user['otp_expiration'] >= datetime.datetime.now():
        print("Right code")
        await db["Users"].update_one({"email": email_input}, {"$set":{"state": "active"}})
        return JSONResponse(status_code=status.HTTP_200_OK, content={"message": "Right code"})
    else:
        print("Wrong code")
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="wrong-code-or-code-expired")

# Step 4:


@router.post("/user/registration/step-4")
async def Registration_step4(user: UserRegistrationStep4):
    user = jsonable_encoder(user)
    user_db = await db["Users"].find_one({"email": user["email"]})
    if user_db["state"] == "inactive":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="email not active")
    elif user_db["state"] == "created":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="user already exist")
    if user["otp"] != user_db["otp"]:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="wrong code")
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    user_db.update({
                    "otp":"",
                    "state": "created",
                    "password": get_hashed_password(user["password"]),
                    "name": user["name"],
                    "given_name":user["given_name"],
                    "family_name": user["family_name"],
                    "gender": user["gender"],
                    "createdAt": now,
                    "modifiedAt": now, 
                    "role": "user", 
                    "history": [], 
                    "favourite": []
                })
    result = await db["Users"].update_one({"email": user["email"]}, {"$set": user_db})
    if result.modified_count == 1:
        send_template_email(
            from_email="support@sunrisedanangvn.com",
            to_email= user["email"],
            subject="「ワッツアップダナン」ご登録ありがとうございます。",
            template="thanks_email.html",
            duration=30
        )
        return JSONResponse(status_code=status.HTTP_201_CREATED, content={"message": "success"})
    return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"message": "fail"})


# LOGIN:
def verify_password(password: str, hashed_password: str):
    return CryptContext(schemes=["bcrypt"], deprecated="auto").verify(password, hashed_password)


async def authenticate_user(email: str, password: str):
    user = await db["Users"].find_one({"email": email})
    if not user:
        return False
    if not verify_password(password, user["password"]):
        return False
    return user

# Login


@router.post("/user/login", response_model=Token)
async def login(user_data: UserLogin = Body(...)):
    user_data = user_data.dict()
    user = await authenticate_user(user_data["email"], user_data["password"])
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = datetime.timedelta(minutes=300)
    if(user["role"] == "admin"): access_token_expires = datetime.timedelta(minutes=600)
    # refresh_token_expires = datetime.timedelta(minutes=60)
    access_token = create_access_token(
        data={"sub": user["email"], "role": user["role"],
              "name": user["given_name"]+user["family_name"]}, expires_delta=access_token_expires
    )
    # refresh_token = create_access_token(
    #     data={"sub": user["email"]}, expires_delta=refresh_token_expires
    # )
    return {"access_token": access_token, "token_type": "bearer"}


def create_access_token(data: dict, expires_delta: Optional[datetime.timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.datetime.utcnow() + expires_delta
    else:
        expire = datetime.datetime.utcnow() + datetime.timedelta(minutes=30)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm="HS256")
    return encoded_jwt


# HISTORY:
@router.get("/user/history", response_model=PropertyPagination)
async def get_user_history(
    page: int = Query(..., gt=0),
    size: int = Query(..., gt=0),
    current_user: UserDB = Security(get_current_user, scopes=[Role.user["name"], Role.admin["name"]])):
    if current_user is None:
        raise  HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")
    result = db["Users"].aggregate([
        {
            '$match':
            {
                '_id': current_user["_id"]
            }
        },
        {
            '$lookup':
            {
                'from': 'Properties',
                'localField': 'history', 
                'foreignField': '_id',
                # 'let':{'history': '$history'},
                # 'pipeline':[
                #     {
                #         '$match':{
                #             '$expr':{
                #                 "$in": ["$_id","$$history"]
                #             }
                #         }
                #     },
                #     {'$skip': size*(page-1)},
                #     {'$limit': size},
                # ],
                'as': 'history'
            }
        },
        {
            '$project':
            {
                '_id': 0,
                'history': '$history'
            }
        }
    ])
    await result.fetch_next
    result = result.next_object()
    response=[]
    for item in result['history']:
        item["_id"] = str(item["_id"])
        response.append(PropertyModel(**item))
    properties = response[size*(page-1) : size*page]
    history = current_user["history"][size*(page-1): size*page]
    properties.sort(key=lambda x: history.index(ObjectId(x.getId())))
    history = {
        "properties": properties,
        "totalItems": len(response),
    }
    return history

# FAVORITE:
# Add to list



@router.get("/user/favourite/{id}")
async def add_to_favourites_list(id: str, current_user=Security(get_current_user, scopes=[Role.user["name"], Role.admin["name"]])):
    if current_user is None:
        raise  HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")

    property = await db["Properties"].find_one({"_id": ObjectId(id)})
    if property is None:
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"message": "property not found"})  
    elif ObjectId(id) in current_user["favourite"]:
        await db["Users"].update_one(
        {"email": current_user["email"]},
        {
            '$pull': {
                'favourite': ObjectId(id)
            }
        })
        return JSONResponse(status_code=status.HTTP_200_OK, content={"isFavourite": False, "message": "remove from favourite"})
    result = await db["Users"].update_one(
        {"email": current_user["email"]},
        {
            '$push': {
                'favourite': {
                    '$each':[ObjectId(id)],
                    '$position': 0
                }
            }
        }
    )
    return JSONResponse(status_code=status.HTTP_200_OK, content={"isFavourite": True, "message": "add to favourite"})

# Get list


@router.get("/user/favourite", response_model=PropertyPagination)
async def get_favourites_list(
    page: int = Query(..., gt=0),
    size: int = Query(..., gt=0),
    current_user=Security(get_current_user, scopes=[Role.user["name"], Role.admin["name"]])):
    if current_user is None:
        raise  HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")

    result = db["Users"].aggregate([
        {
            '$match':
            {
                '_id': current_user["_id"]
            }
        },
        {
            '$lookup':
            {
                'from': 'Properties',
                'localField': 'favourite',
                'foreignField': '_id',
                # 'let':{"favourite": "$favourite"},
                # 'pipeline':[
                #     {
                #         '$match':{
                #             '$expr':{
                #                 "$in": ["$_id","$$favourite"]
                #             }
                #         }
                #     },
                #     {'$skip': size*(page-1)},
                #     {'$limit': size},
                # ],
                'as': 'favourite'
            }
        },
        {
            '$project':
            {
                '_id': 0,
                'favourite': '$favourite'
            }
        }
    ])
    await result.fetch_next
    result = result.next_object()
    response=[]
    for item in result["favourite"]:
        item["_id"] = str(item["_id"])
        response.append(PropertyModel(**item))
    properties = response[size*(page-1) : size*page]
    favourite = current_user["favourite"][size*(page-1): size*page]
    response.sort(key=lambda x: favourite.index(ObjectId(x.getId())))
    favourite = {
        "properties": properties,
        "totalItems": len(response),
    }
    return favourite

@router.get("/user/favouriteCount")
async def get_favourite_count(current_user=Security(get_current_user, scopes=[Role.user["name"], Role.admin["name"]])):
    if current_user is None:
        return 0
    return len(current_user["favourite"])

#Forgot Password
@router.post("/forgotPassword")
async def forgot_password(email: ForgotPassword = Body(...)):
    email = email.dict()["email"]
    user = await db["Users"].find_one({"email": email})
    if user is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="email_not_found")
    token = create_access_token(data={"email": email},expires_delta=datetime.timedelta(minutes=15))

    result = send_template_email(
        from_email="support@sunrisedanangvn.com",
        to_email=email,
        subject="Forgot Password",
        template="forgot_password_email.html",
        link = settings.base_fe_url+"/#/reset-password/"+token,
        duration=15
    )
    return result

@router.post("/resetPassword")
async def reset_password(user: ResetPassword = Body(...)):
    user = user.dict()
    try:
        decode_token = jwt.decode(user["token"], settings.secret_key, algorithms="HS256")
    except Exception:
        raise HTTPException(status_code=status.HTTP_408_REQUEST_TIMEOUT, detail="link expired")
    email = decode_token["email"]
    userdb = await db["Users"].find_one({"email": email})
    if userdb is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="email not found")
    userdb.update({"password": get_hashed_password(user["new_password"])})
    await db["Users"].update_one({"email": email}, {"$set": userdb})
    return JSONResponse(status_code=status.HTTP_200_OK, content={"message": "password updated"})
    
