from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from openai import OpenAI
import base64
import json
from typing import List, Optional
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import uuid
from passlib.context import CryptContext
import jwt
from .models import (
    User, UserCreate, Store, MenuItem, Order, 
    OrderCreate, OrderStatus, OrderItem
)

# Load environment variables
load_dotenv()

app = FastAPI()

# Security
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# OpenAI client
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

# In-memory storage (replace with database in production)
users = {}
stores = {}
orders = {}

def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None or user_id not in users:
            raise credentials_exception
        return users[user_id]
    except jwt.JWTError:
        raise credentials_exception

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

@app.post("/register", response_model=User)
async def register_user(user: UserCreate):
    if user.email in [u.email for u in users.values()]:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )
    
    user_id = str(uuid.uuid4())
    hashed_password = pwd_context.hash(user.password)
    
    db_user = User(
        id=user_id,
        email=user.email,
        name=user.name,
        created_at=datetime.utcnow()
    )
    users[user_id] = {**db_user.dict(), "hashed_password": hashed_password}
    
    return db_user

@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = None
    for u in users.values():
        if u["email"] == form_data.username:
            user = u
            break
    
    if not user or not pwd_context.verify(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=400,
            detail="Incorrect email or password"
        )
    
    access_token = create_access_token(
        data={"sub": user["id"]}
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/upload-menu")
async def upload_menu(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """
    Upload a menu image and process it to extract menu items
    """
    try:
        # Read the image file
        image_content = await file.read()
        
        # Encode the image to base64
        base64_image = base64.b64encode(image_content).decode('utf-8')
        
        # Call OpenAI Vision API to analyze the menu
        response = client.chat.completions.create(
            model="gpt-4-vision-preview",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "This is a menu image. Please analyze it and extract all menu items in the following JSON format:\n"
                                  "{\n"
                                  "  'store_name': 'Name of the restaurant',\n"
                                  "  'items': [\n"
                                  "    {\n"
                                  "      'name': 'Item name',\n"
                                  "      'price': float price,\n"
                                  "      'description': 'Item description',\n"
                                  "      'category': 'Food category'\n"
                                  "    }\n"
                                  "  ]\n"
                                  "}"
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=1500
        )
        
        # Parse the response
        menu_data = json.loads(response.choices[0].message.content)
        
        # Create store
        store_id = str(uuid.uuid4())
        store = Store(
            id=store_id,
            name=menu_data["store_name"],
            owner_id=current_user.id,
            items=[MenuItem(**item) for item in menu_data["items"]],
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(days=7),  # Store expires in 7 days
            share_url=f"/store/{store_id}"
        )
        
        stores[store_id] = store
        
        return {
            "message": "Menu processed successfully",
            "store": store
        }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing menu: {str(e)}")

@app.get("/stores")
async def get_stores(current_user: User = Depends(get_current_user)):
    """
    Get list of all stores owned by the current user
    """
    user_stores = [
        store for store in stores.values()
        if store.owner_id == current_user.id
    ]
    return user_stores

@app.get("/store/{store_id}")
async def get_store(store_id: str):
    """
    Get menu for a specific store (public endpoint)
    """
    if store_id not in stores:
        raise HTTPException(status_code=404, detail="Store not found")
    
    store = stores[store_id]
    if not store.is_active or (store.expires_at and store.expires_at < datetime.utcnow()):
        raise HTTPException(status_code=404, detail="Store has expired or is inactive")
    
    return store

@app.post("/store/{store_id}/order")
async def create_order(store_id: str, order: OrderCreate):
    """
    Create a new order (public endpoint)
    """
    if store_id not in stores:
        raise HTTPException(status_code=404, detail="Store not found")
    
    store = stores[store_id]
    if not store.is_active or (store.expires_at and store.expires_at < datetime.utcnow()):
        raise HTTPException(status_code=404, detail="Store has expired or is inactive")
    
    # Calculate total amount
    total_amount = 0
    for item in order.items:
        menu_item = next(
            (mi for mi in store.items if mi.name == item.menu_item_name),
            None
        )
        if not menu_item:
            raise HTTPException(
                status_code=400,
                detail=f"Menu item not found: {item.menu_item_name}"
            )
        total_amount += menu_item.price * item.quantity
    
    # Create order
    order_id = str(uuid.uuid4())
    new_order = Order(
        id=order_id,
        store_id=store_id,
        items=order.items,
        buyer_name=order.buyer_name,
        contact_info=order.contact_info,
        total_amount=total_amount,
        status=OrderStatus.PENDING,
        created_at=datetime.utcnow(),
        notes=order.notes
    )
    
    orders[order_id] = new_order
    return new_order

@app.get("/store/{store_id}/orders")
async def get_store_orders(
    store_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get all orders for a store (only for store owner)
    """
    if store_id not in stores:
        raise HTTPException(status_code=404, detail="Store not found")
    
    store = stores[store_id]
    if store.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view these orders")
    
    store_orders = [
        order for order in orders.values()
        if order.store_id == store_id
    ]
    return store_orders

@app.put("/store/{store_id}/order/{order_id}")
async def update_order_status(
    store_id: str,
    order_id: str,
    status: OrderStatus,
    current_user: User = Depends(get_current_user)
):
    """
    Update order status (only for store owner)
    """
    if store_id not in stores or order_id not in orders:
        raise HTTPException(status_code=404, detail="Store or order not found")
    
    store = stores[store_id]
    if store.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this order")
    
    order = orders[order_id]
    if order.store_id != store_id:
        raise HTTPException(status_code=400, detail="Order does not belong to this store")
    
    order.status = status
    return order
