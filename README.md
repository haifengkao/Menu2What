# Menu2What API

A FastAPI-based service that processes menu images and creates structured menu data using OpenAI's Vision API.

## Setup

1. Clone the repository
2. Create a `.env` file in the root directory with your OpenAI API key:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the server:
   ```bash
   uvicorn storeapi.main:app --reload
   ```

## Security Notes

- Never commit the `.env` file to version control
- Keep your API keys secure and rotate them periodically
- The `.env` file is included in `.gitignore` to prevent accidental commits

## API Endpoints

- `POST /upload-menu`: Upload a menu image for processing
- `GET /stores`: Get all stored menus
- `GET /store/{store_name}`: Get menu for a specific store

## Development

- The server runs in development mode with auto-reload enabled
- API documentation is available at `/docs` when the server is running
