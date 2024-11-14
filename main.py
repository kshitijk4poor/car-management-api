from fastapi import FastAPI, HTTPException, Depends, status, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta
import jwt
import bcrypt
import motor.motor_asyncio
from bson import ObjectId
import os
from dotenv import load_dotenv
import json
import uuid
from fastapi.staticfiles import StaticFiles
import aiofiles

load_dotenv()

app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# MongoDB connection
client = motor.motor_asyncio.AsyncIOMotorClient(os.getenv("MONGODB_URL"))
db = client.car_management

# JWT settings
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Models
class UserCreate(BaseModel):
    email: str
    password: str
    name: str

class User(BaseModel):
    id: str
    email: str
    name: str

class Token(BaseModel):
    access_token: str
    token_type: str

class CarCreate(BaseModel):
    title: str
    description: str
    tags: List[str]
    images: List[str]

class Car(BaseModel):
    id: str
    title: str
    description: str
    tags: List[str]
    images: List[str]
    user_id: str
    created_at: datetime

# Auth utilities
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user = await db.users.find_one({"_id": ObjectId(payload["sub"])})
        if user is None:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        return User(id=str(user["_id"]), email=user["email"], name=user["name"])
    except:
        raise HTTPException(status_code=401, detail="Invalid credentials")

# Auth endpoints
@app.post("/api/users/register", response_model=User)
async def register(user: UserCreate):
    if await db.users.find_one({"email": user.email}):
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = bcrypt.hashpw(user.password.encode(), bcrypt.gensalt())
    user_dict = user.dict()
    user_dict["password"] = hashed_password
    result = await db.users.insert_one(user_dict)
    
    created_user = await db.users.find_one({"_id": result.inserted_id})
    return User(id=str(created_user["_id"]), email=created_user["email"], name=created_user["name"])

@app.post("/api/users/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await db.users.find_one({"email": form_data.username})
    if not user or not bcrypt.checkpw(form_data.password.encode(), user["password"]):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = jwt.encode(
        {"sub": str(user["_id"]), "exp": datetime.utcnow() + access_token_expires},
        SECRET_KEY,
        algorithm=ALGORITHM,
    )
    return {"access_token": access_token, "token_type": "bearer"}

# Car endpoints
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)  # Create uploads directory if it doesn't exist

app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

@app.post("/api/cars", response_model=Car)
async def create_car(
    title: str = Form(...),
    description: str = Form(...),
    tags: str = Form(...),
    urlImages: str = Form(...),
    imageFiles: List[UploadFile] = File([]),
    current_user: User = Depends(get_current_user)
):
    url_images = json.loads(urlImages)
    total_images = len(url_images) + len(imageFiles)
    
    if total_images > 10:
        raise HTTPException(
            status_code=400,
            detail="Total number of images cannot exceed 10"
        )
    
    uploaded_images = []
    if imageFiles:
        for file in imageFiles:
            # Generate unique filename
            ext = file.filename.split('.')[-1]
            filename = f"{uuid.uuid4()}.{ext}"
            file_path = os.path.join(UPLOAD_DIR, filename)
            
            # Save file
            async with aiofiles.open(file_path, 'wb') as buffer:
                content = await file.read()
                await buffer.write(content)
            
            # Store the URL path
            uploaded_images.append(f"/uploads/{filename}")
    
    # Combine URLs
    all_images = url_images + uploaded_images
    
    car_dict = {
        "title": title,
        "description": description,
        "tags": json.loads(tags),
        "images": all_images,
        "user_id": current_user.id,
        "created_at": datetime.utcnow()
    }
    
    result = await db.cars.insert_one(car_dict)
    created_car = await db.cars.find_one({"_id": result.inserted_id})
    return {**created_car, "id": str(created_car["_id"])}

@app.get("/api/cars", response_model=List[Car])
async def list_cars(search: Optional[str] = None, current_user: User = Depends(get_current_user)):
    query = {"user_id": current_user.id}
    if search:
        query["$or"] = [
            {"title": {"$regex": search, "$options": "i"}},
            {"description": {"$regex": search, "$options": "i"}},
            {"tags": {"$regex": search, "$options": "i"}}
        ]
    cars = await db.cars.find(query).to_list(None)
    return [{**car, "id": str(car["_id"])} for car in cars]

@app.get("/api/cars/{car_id}", response_model=Car)
async def get_car(car_id: str, current_user: User = Depends(get_current_user)):
    car = await db.cars.find_one({"_id": ObjectId(car_id), "user_id": current_user.id})
    if not car:
        raise HTTPException(status_code=404, detail="Car not found")
    return {**car, "id": str(car["_id"])}

@app.put("/api/cars/{car_id}", response_model=Car)
async def update_car(car_id: str, car: CarCreate, current_user: User = Depends(get_current_user)):
    car_dict = car.dict()
    result = await db.cars.update_one(
        {"_id": ObjectId(car_id), "user_id": current_user.id},
        {"$set": car_dict}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Car not found")
    updated_car = await db.cars.find_one({"_id": ObjectId(car_id)})
    return {**updated_car, "id": str(updated_car["_id"])}

@app.delete("/api/cars/{car_id}")
async def delete_car(car_id: str, current_user: User = Depends(get_current_user)):
    result = await db.cars.delete_one({"_id": ObjectId(car_id), "user_id": current_user.id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Car not found")
    return {"message": "Car deleted successfully"}
