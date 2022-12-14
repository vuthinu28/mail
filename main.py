from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
from router import contact, post, property, user, image
from fastapi.staticfiles import StaticFiles
from config import settings

app = FastAPI()
app.include_router(user.router)
app.include_router(post.router)
app.include_router(property.router)
app.include_router(contact.router)
app.include_router(image.router)

origins = [
    settings.base_fe_url
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/uploads", StaticFiles(directory=settings.upload_path), name="uploads")
