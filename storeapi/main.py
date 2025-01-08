from fastapi import FastAPI, UploadFile, File, HTTPException
from openai import OpenAI
import base64
import json
from typing import Dict, List
from pydantic import BaseModel
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI()

# Load configuration
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

# Pydantic models for request/response validation
class MenuItem(BaseModel):
    name: str
    price: float
    description: str
    category: str

class Menu(BaseModel):
    store_name: str
    items: List[MenuItem]

@app.get("/")
async def root():
    return {"message": "Menu2What API Service"}

@app.post("/upload-menu")
async def upload_menu(file: UploadFile = File(...)):
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
        
        # Parse the response and validate it
        try:
            menu_data = json.loads(response.choices[0].message.content)
            menu = Menu(**menu_data)
            
            # Save the menu data to store.json
            store_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'store.json')
            try:
                with open(store_path, 'r') as f:
                    stores = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                stores = []
            
            # Add or update store
            store_exists = False
            for store in stores:
                if store['store_name'] == menu.store_name:
                    store['items'] = [item.dict() for item in menu.items]
                    store_exists = True
                    break
            
            if not store_exists:
                stores.append({
                    'store_name': menu.store_name,
                    'items': [item.dict() for item in menu.items]
                })
            
            # Save updated stores
            with open(store_path, 'w') as f:
                json.dump(stores, f, indent=2)
            
            return {
                "message": "Menu processed successfully",
                "data": menu.dict()
            }
            
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Failed to parse menu data from image")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid menu data format: {str(e)}")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing menu: {str(e)}")

@app.get("/stores")
async def get_stores():
    """
    Get list of all stores and their menus
    """
    try:
        store_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'store.json')
        with open(store_path, 'r') as f:
            stores = json.load(f)
        return stores
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading stores: {str(e)}")

@app.get("/store/{store_name}")
async def get_store(store_name: str):
    """
    Get menu for a specific store
    """
    try:
        store_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'store.json')
        with open(store_path, 'r') as f:
            stores = json.load(f)
        
        for store in stores:
            if store['store_name'] == store_name:
                return store
        
        raise HTTPException(status_code=404, detail="Store not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading store data: {str(e)}")

@app.post("/analyze-image")
async def analyze_image(file: UploadFile = File(...)):
    # Read the image file
    image_content = await file.read()
    
    # Encode the image to base64
    base64_image = base64.b64encode(image_content).decode('utf-8')
    
    # Call OpenAI Vision API
    response = client.chat.completions.create(
        model="gpt-4-vision-preview",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "What's in this image? Please describe in detail."},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        max_tokens=300
    )
    
    return {"analysis": response.choices[0].message.content}

completion = client.chat.completions.create(
  model="gpt-4o-mini",
  store=True,
  messages=[
    {"role": "user", "content": "write a haiku about ai"}
  ]
)

print(completion.choices[0].message);
