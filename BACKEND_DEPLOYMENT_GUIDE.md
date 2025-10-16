# Backend Deployment Guide

## ✅ Issue Resolution Summary

**Problem**: Backend initialization timing conflict where `RiskAssessmentService` was instantiated at module import time, requiring `MISTRAL_API_KEY` before secrets were loaded from MongoDB.

**Solution**: Implemented lazy initialization pattern to defer service creation until first use.

## 🔧 Fixes Applied

### 1. Lazy Initialization Pattern
- **File**: [`backend/services/risk_assessment.py`](backend/services/risk_assessment.py:244)
- **Change**: Replaced immediate instantiation with lazy getter function
- **Before**: `risk_assessment_service = RiskAssessmentService()`
- **After**: 
  ```python
  risk_assessment_service = None
  
  def get_risk_assessment_service():
      global risk_assessment_service
      if risk_assessment_service is None:
          risk_assessment_service = RiskAssessmentService()
      return risk_assessment_service
  ```

### 2. Updated Service Usage
- **Files**: 
  - [`backend/services/llm.py`](backend/services/llm.py:11)
  - [`backend/routes/llm.py`](backend/routes/llm.py:5)
- **Change**: Updated all imports and usage to use the lazy getter function
- **Pattern**: `get_risk_assessment_service()` instead of direct `risk_assessment_service` access

## 🚀 Reliable Deployment Sequence

### Prerequisites
1. Ensure MongoDB is running and accessible
2. Ensure no processes are using port 8000: `lsof -ti:8000 | xargs kill -9`
3. Ensure Python environment is activated

### Deployment Steps

#### Step 1: Clean Environment
```bash
# Kill any existing backend processes
lsof -ti:8000 | xargs kill -9 2>/dev/null || echo "Port 8000 is free"

# Verify no Python backend processes are running
ps aux | grep "python backend/run.py" | grep -v grep
```

#### Step 2: Start Backend
```bash
# From project root directory
PYTHONPATH=. python backend/run.py
```

**Alternative (Background Mode)**:
```bash
# Start in background with logging
PYTHONPATH=. python backend/run.py > backend_startup.log 2>&1 &
```

#### Step 3: Verify Deployment
```bash
# Wait for startup (3-5 seconds)
sleep 5

# Test health endpoint
curl -s http://localhost:8000/healthz

# Expected response: {"status":"ok","db_status":"connected"}
```

#### Step 4: Monitor Logs
```bash
# If running in background, check logs
cat backend_startup.log

# Look for these success indicators:
# - "INFO: Uvicorn running on http://0.0.0.0:8000"
# - "INFO: Application startup complete."
# - No MISTRAL_API_KEY errors during startup
```

## 🧪 Testing the Fix

A test script is available to verify the lazy initialization:

```bash
python test_lazy_initialization.py
```

**Expected Output**:
```
🧪 Testing lazy initialization fix...
📦 Importing risk assessment service...
✅ Risk assessment service imported successfully
📦 Importing main app...
✅ Main app imported successfully
✅ Service is properly lazy (None until first use)

🎉 SUCCESS: Lazy initialization is working!
```

## 🔍 Troubleshooting

### Port Already in Use
```bash
# Find and kill process using port 8000
lsof -ti:8000 | xargs kill -9

# Or find specific process
lsof -i:8000
kill -9 <PID>
```

### Module Import Errors
- Ensure you're running from the project root directory
- Use `PYTHONPATH=. python backend/run.py` to set the Python path correctly
- Verify all dependencies are installed: `pip install -r backend/requirements.txt`

### Service Initialization Errors
- The lazy initialization should prevent MISTRAL_API_KEY errors at startup
- Services will only initialize when first used (after secrets are loaded)
- Check MongoDB connection if database-related errors occur

## 📋 Health Check Endpoints

- **Main Health**: `GET /healthz` - Returns `{"status":"ok","db_status":"connected"}`
- **API v1 Health**: `GET /api/v1/health` - API version health check
- **Weather Service**: `GET /weather/health` - Weather service health
- **LLM Service**: `GET /llm/health` - LLM service health

## 🎯 Success Criteria

✅ **Backend starts without MISTRAL_API_KEY errors**  
✅ **Health endpoint returns successful response**  
✅ **Database connection established**  
✅ **Services use lazy initialization pattern**  
✅ **No zombie processes blocking port 8000**  

## 🔄 Integration with Google Calendar Testing

With the backend now stable and healthy, you can proceed with Google Calendar integration testing as documented in [`GOOGLE_CALENDAR_TESTING_GUIDE.md`](GOOGLE_CALENDAR_TESTING_GUIDE.md).

The backend deployment issues that were blocking the Google Calendar testing have been resolved.