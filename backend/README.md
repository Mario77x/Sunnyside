# Sunnyside Backend

FastAPI backend for the Sunnyside social planning application.

## Setup

1. Install Python 3.12 or higher
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Server

### Option 1: Using the run script (recommended for development)
```bash
python run.py
```

### Option 2: Using uvicorn directly
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Option 3: Using the main module
```bash
python main.py
```

The server will start on `http://localhost:8000`

## API Endpoints

- `GET /` - Root endpoint
- `GET /healthz` - Health check endpoint (includes database connectivity status)
- `GET /api/v1/*` - API v1 endpoints (to be implemented in future sprints)

## Database

The backend connects to MongoDB Atlas using the connection string specified in the development plan.

## CORS Configuration

CORS is configured to allow requests from the frontend running on `http://localhost:5173`.

## Development

The server runs with auto-reload enabled when using `python run.py`, so changes to the code will automatically restart the server.