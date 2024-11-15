# 🚗 Car Management API

A robust FastAPI service for managing car listings with image uploads, user authentication, and search capabilities.

## 🌟 Features

- 🔐 JWT Authentication
- 📝 CRUD operations for car listings
- 🖼️ Multiple image uploads (up to 10 per listing)
- 🔍 Search functionality
- ☁️ Cloudinary integration for image storage
- 🗄️ MongoDB database

## 🚀 Quick Deploy

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/render-examples/fastapi)

## 🛠️ Manual Deployment Steps

1. Clone this repository or use it as a template
2. Create a new Web Service on Render
3. Connect your repository
4. Add your environment variables:
   - `MONGODB_URL`
   - `JWT_SECRET_KEY`
   - `CLOUDINARY_URL`
5. Use this start command:
```
uvicorn main:app --host 0.0.0.0 --port $PORT
```

## 📚 API Documentation

Once deployed, access the interactive API documentation at:
- Swagger UI: `/docs`
- ReDoc: `/redoc`

These endpoints provide detailed API specifications and allow you to test endpoints directly.

Access the interactive API documentation at:
- Swagger UI: [https://car-management-api-cw20.onrender.com/docs](https://car-management-api-cw20.onrender.com/docs)
- ReDoc: [https://car-management-api-cw20.onrender.com/redoc](https://car-management-api-cw20.onrender.com/redoc)


## 🔧 Local Development

1. Create a virtual environment:
```
python -m venv venv
source venv/bin/activate
```

2. Install dependencies:
```
pip install -r requirements.txt
```

3. Create `.env` file with required environment variables
4. Run the server:
```
uvicorn main:app --reload
```

## 📝 Environment Variables

- `MONGO_URL`: MongoDB URI
- `JWT_SECRET_KEY`: Secret key for JWT
- `CLOUDINARY_URL`: Cloudinary URL
