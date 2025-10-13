# Sunnyside - Social Activity Planning Platform

A full-stack web application for planning activities with friends and family using AI-powered recommendations, weather intelligence, and seamless coordination. Sunnyside simplifies the process of organizing social events, from suggesting the best days based on weather to coordinating with guests.

## Getting Started

Follow these instructions to set up and run the project locally for development.

### Prerequisites

*   Python 3.9+
*   Node.js 18+
*   A MongoDB Atlas account (or a local MongoDB instance)

### 1. Clone the Repository

```bash
git clone <repository-url>
cd Sunnyside
```

### 2. Backend Setup

```bash
# Navigate to the backend directory
cd backend

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`

# Install dependencies
pip install -r requirements.txt
```

### 3. Frontend Setup

```bash
# In a new terminal, navigate to the frontend directory
cd frontend

# Install dependencies
npm install
```

### 4. Environment Configuration

This project uses `.env` files for environment variables. A `.env.example` file is provided as a template.

```bash
# Create a .env file from the example
cp .env.example .env```

Now, open the `.env` file and add your configuration values for the following variables:

*   `MONGODB_URI`: Your MongoDB connection string.
*   `JWT_SECRET`: A secure, random string for signing JWTs.
*   `CORS_ORIGINS`: A comma-separated list of allowed frontend URLs (e.g., `http://localhost:5173,http://localhost:5137`).

### 5. Running the Development Servers

*   **Backend (FastAPI):**
    ```bash
    # From the backend directory with the virtual environment activated
    uvicorn main:app --reload
    ```
    The backend will be available at `http://localhost:8000`.

*   **Frontend (Vite):**
    ```bash
    # From the frontend directory
    npm run dev
    ```
    The frontend will be available at `http://localhost:5173` (or another port if 5173 is in use).

## Technology Stack

*   **Frontend:**
    *   React (~18.3.1)
    *   Vite (~6.3.4)
    *   TypeScript (~5.5.3)
    *   Tailwind CSS (~3.4.11)
    *   shadcn/ui
*   **Backend:**
    *   FastAPI (~0.104.1)
    *   Python (~3.14)
    *   MongoDB (with Motor ~3.3.2 for async access)
*   **Authentication:**
    *   JWT-based authentication

## Project Structure

This project is a monorepo with a clear separation between the frontend and backend.

```
Sunnyside/
├── backend/         # FastAPI backend application
│   ├── main.py      # Main application entry point
│   ├── models/      # Pydantic models for data structures
│   └── routes/      # API route handlers
├── frontend/        # React/Vite frontend application
│   ├── src/
│   │   ├── components/  # Reusable UI components
│   │   ├── pages/       # Page components
│   │   └── services/    # API service layer for frontend-backend communication
├── .env.example     # Template for environment variables
└── README.md        # This file