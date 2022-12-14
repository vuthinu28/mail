from fastapi.security import OAuth2PasswordBearer, SecurityScopes
from jose import jwt
from jose.exceptions import JWTError
from contracts.role import Role
from fastapi import Body, HTTPException, status, Depends
from fastapi import FastAPI
from config import settings
from db import db
app = FastAPI()

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="user/login",
    scopes={
        Role.user["name"]: Role.user["description"],
        Role.admin["name"]: Role.admin["description"],
        "GUEST": "test",
    },
    auto_error= False
)


@app.middleware("http")
async def get_current_user(security_scopes: SecurityScopes, token: str = Depends(oauth2_scheme)):
    if security_scopes.scopes:
        authenticate_value = f'Bearer scope="{security_scopes.scope_str}"'
    else:
        authenticate_value = f"Bearer"
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        return None
    try:
        decode_token = jwt.decode(token, settings.secret_key, algorithms="HS256")
        email = decode_token.get("sub")
        role = decode_token.get("role")
        user = await db["Users"].find_one({"email": email})
        if user is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    if security_scopes.scopes and role not in security_scopes.scopes:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not enough permissions",
            headers={"WWW-Authenticate": authenticate_value},
        )
    return user
