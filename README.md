# Sunnyside - Social Activity Planning Platform

A full-stack web application for planning activities with friends and family using AI-powered recommendations, weather intelligence, and seamless coordination.

## 🚀 Features

- **Weather-First Planning**: Get optimal day suggestions based on weather forecasts
- **Smart Coordination**: AI-powered group coordination with guest access
- **Personalized Suggestions**: Activity recommendations tailored to your group's preferences
- **Multi-Channel Notifications**: Email, SMS, and WhatsApp support
- **Guest Response System**: No-registration required for invitees

## 🏗️ Architecture

- **Frontend**: React + TypeScript + Vite + Tailwind CSS
- **Backend**: FastAPI + Python + MongoDB
- **Authentication**: JWT-based authentication
- **Database**: MongoDB Atlas

## 🔧 Setup Instructions

### Prerequisites

- Python 3.9+
- Node.js 18+
- MongoDB Atlas account (or local MongoDB)

### 1. Clone and Setup

```bash
git clone <repository-url>
cd Sunnyside
```

### 2. Backend Setup

```bash
# Create and activate virtual environment
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Configuration

⚠️ **IMPORTANT**: Never commit secrets to version control!

```bash
# Copy the example environment file
cp .env.example .env

# Update .env with your actual values (see SECURITY.md for details)
```

**Required Environment Variables:**
- `MONGODB_URI`: Your MongoDB connection string
- `JWT_SECRET`: Secure random string for JWT signing
- `CORS_ORIGINS`: Allowed frontend URLs

### 4. Secure Secret Management

Use the provided script to securely set your MongoDB URI:

```bash
python scripts/update_env.py
```

Or manually edit `.env` file with your secrets.

### 5. Start the Backend

```bash
cd backend
source venv/bin/activate
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

### 6. Frontend Setup

```bash
# In a new terminal
cd frontend
npm install
npm run dev
```

The application will be available at:
- Frontend: http://localhost:5137
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

## 🔐 Security

This application implements secure secret management:

- ✅ No hardcoded secrets in source code
- ✅ Environment variables for all sensitive data
- ✅ Proper `.gitignore` configuration
- ✅ Security documentation and guidelines

**See [SECURITY.md](SECURITY.md) for detailed security information.**

## 📁 Project Structure

```
Sunnyside/
├── backend/                 # FastAPI backend
│   ├── main.py             # Application entry point
│   ├── auth.py             # Authentication logic
│   ├── models/             # Pydantic models
│   └── routes/             # API route handlers
├── frontend/               # React frontend
│   ├── src/
│   │   ├── components/     # Reusable UI components
│   │   ├── pages/          # Page components
│   │   ├── services/       # API service layer
│   │   └── contexts/       # React contexts
├── scripts/                # Utility scripts
├── .env.example           # Environment template
├── .gitignore            # Git ignore rules
└── SECURITY.md           # Security guidelines
```

## 🔄 Development Workflow

1. **Start both servers** (backend and frontend)
2. **Make changes** to your code
3. **Test the integration** using the web interface
4. **Commit changes** (secrets are automatically excluded)

## 🚀 Deployment

### Environment Variables for Production

Set these environment variables in your hosting platform:

- `MONGODB_URI`: Production MongoDB connection string
- `JWT_SECRET`: Strong, unique secret for production
- `CORS_ORIGINS`: Your production frontend URL(s)
- `APP_ENV`: Set to `production`

### Recommended Hosting

- **Backend**: Heroku, Railway, or AWS
- **Frontend**: Vercel, Netlify, or AWS S3/CloudFront
- **Database**: MongoDB Atlas

## 🧪 API Endpoints

### Authentication
- `POST /api/v1/auth/signup` - User registration
- `POST /api/v1/auth/login` - User login
- `GET /api/v1/auth/me` - Get current user

### Activities
- `GET /api/v1/activities` - List user activities
- `POST /api/v1/activities` - Create new activity
- `GET /api/v1/activities/{id}` - Get activity details
- `PUT /api/v1/activities/{id}` - Update activity
- `POST /api/v1/activities/{id}/invite` - Send invitations

### Guest Responses
- `GET /api/v1/invites/{id}` - Get public activity info
- `POST /api/v1/invites/{id}/respond` - Submit guest response

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Ensure no secrets are committed
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

For security concerns, see [SECURITY.md](SECURITY.md).
For other issues, please create a GitHub issue.