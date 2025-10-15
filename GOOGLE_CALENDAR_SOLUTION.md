# Google Calendar Integration - Complete Solution

## 🚨 Problem Summary

**Issue**: Users are getting a **503 Service Unavailable** error when trying to access Google Calendar integration.

**Error Message**:
```json
{
  "error": "Google Calendar integration is not available",
  "reason": "Missing configuration or dependencies", 
  "setup_required": true
}
```

**Root Cause**: Google OAuth credentials (`GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET`) are not configured in the environment variables.

## ✅ Complete Solution

### Option 1: Quick Setup (Recommended)

1. **Run the automated setup script**:
   ```bash
   python scripts/setup_google_calendar.py
   ```

2. **Follow the prompts** to enter your Google Cloud credentials

3. **Restart your backend server**:
   ```bash
   # Stop the current server (Ctrl+C) then restart
   python -m uvicorn backend.main:app --reload --port 8000
   ```

### Option 2: Manual Setup

1. **Get Google Cloud Credentials**:
   - Go to [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
   - Create or select a project
   - Enable Google Calendar API
   - Create OAuth 2.0 credentials (Web application)
   - Add redirect URI: `http://localhost:8000/api/v1/calendar/auth/google/callback`

2. **Update your `.env` file**:
   ```env
   # Uncomment and replace with your actual credentials
   GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
   GOOGLE_CLIENT_SECRET=your-client-secret
   GOOGLE_REDIRECT_URI=http://localhost:8000/api/v1/calendar/auth/google/callback
   ```

3. **Restart your backend server**

## 🔍 Verification

Run the verification script to confirm everything is working:

```bash
python scripts/verify_google_calendar_setup.py
```

**Expected output when properly configured**:
```
✅ PASS Environment File
✅ PASS Environment Variables  
✅ PASS Python Dependencies
✅ PASS Google Calendar Service
✅ PASS API Endpoint

🎉 SUCCESS: Google Calendar integration is properly configured!
```

## 📁 Files Created/Modified

### New Files:
- [`scripts/setup_google_calendar.py`](scripts/setup_google_calendar.py) - Interactive setup script
- [`scripts/verify_google_calendar_setup.py`](scripts/verify_google_calendar_setup.py) - Verification script
- `GOOGLE_CALENDAR_SOLUTION.md` - This solution document

### Modified Files:
- [`GOOGLE_CALENDAR_SETUP.md`](GOOGLE_CALENDAR_SETUP.md) - Enhanced with troubleshooting and detailed instructions
- [`.env`](.env) - Added Google Calendar credential templates (commented out)

## 🧪 Testing the Fix

1. **Before Fix** - API returns 503:
   ```bash
   curl http://localhost:8000/api/v1/calendar/auth/google
   # Returns: 503 Service Unavailable
   ```

2. **After Fix** - API returns 401/403 (expected without authentication):
   ```bash
   curl http://localhost:8000/api/v1/calendar/auth/google  
   # Returns: 401 Unauthorized (this is correct!)
   ```

## 🔧 Troubleshooting

### Common Issues:

1. **Still getting 503 after setup**:
   - Verify credentials are uncommented in `.env`
   - Restart backend server
   - Run verification script

2. **"redirect_uri_mismatch" error**:
   - Check Google Cloud Console redirect URI matches exactly
   - Ensure using correct port (8000)

3. **"invalid_client" error**:
   - Verify Client ID and Secret are correct
   - Ensure OAuth client is "Web application" type

4. **"access_denied" error**:
   - Add your email as test user in OAuth consent screen
   - Verify Calendar API is enabled

## 📚 Documentation

- **Full Setup Guide**: [`GOOGLE_CALENDAR_SETUP.md`](GOOGLE_CALENDAR_SETUP.md)
- **Integration Plan**: [`GOOGLE_CALENDAR_INTEGRATION_PLAN.md`](GOOGLE_CALENDAR_INTEGRATION_PLAN.md)
- **API Routes**: [`backend/routes/calendar.py`](backend/routes/calendar.py)
- **Service Implementation**: [`backend/services/google_calendar.py`](backend/services/google_calendar.py)

## 🎯 Next Steps

1. **Get Google Cloud credentials** from the console
2. **Run the setup script**: `python scripts/setup_google_calendar.py`
3. **Verify the setup**: `python scripts/verify_google_calendar_setup.py`
4. **Test the integration** in your application

## 📞 Support

If you encounter issues:

1. Run the verification script for detailed diagnostics
2. Check the enhanced troubleshooting section in `GOOGLE_CALENDAR_SETUP.md`
3. Review Google Cloud Console settings
4. Check backend server logs for specific error messages

---

**Setup Time**: ~10-15 minutes  
**Difficulty**: Beginner-friendly with provided scripts  
**Dependencies**: All required packages are already installed