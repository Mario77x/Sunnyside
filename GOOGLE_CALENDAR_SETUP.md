# Google Calendar Integration Setup

This document provides comprehensive step-by-step instructions for setting up Google Calendar integration in the Sunnyside application.

## 🚨 Quick Fix for Current Error

If you're seeing the **503 Service Unavailable** error, you need to add Google Calendar credentials to your `.env` file:

```bash
# Add these lines to your .env file
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8000/api/v1/calendar/auth/google/callback
```

**Use the quick setup script below to get started immediately!**

## 🚀 Quick Setup Script

Run this command to set up your environment variables quickly:

```bash
# Run the quick setup script
python scripts/setup_google_calendar.py
```

Or manually add the credentials to your `.env` file using the template provided.

## Prerequisites

1. A Google Cloud Platform (GCP) project
2. Google Calendar API enabled
3. OAuth 2.0 credentials configured
4. Python dependencies installed

## Detailed Google Cloud Setup

### 1. Create a Google Cloud Project

1. **Navigate to Google Cloud Console**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Sign in with your Google account

2. **Create or Select Project**
   - Click the project dropdown at the top
   - Click "New Project" or select an existing one
   - Give it a meaningful name like "Sunnyside-Calendar-Integration"
   - Note your **Project ID** (you'll need this)

### 2. Enable Google Calendar API

1. **Access API Library**
   - In the Google Cloud Console, click the hamburger menu (☰)
   - Navigate to "APIs & Services" > "Library"

2. **Enable Calendar API**
   - Search for "Google Calendar API"
   - Click on "Google Calendar API" from the results
   - Click the blue "Enable" button
   - Wait for the API to be enabled (usually takes a few seconds)

### 3. Configure OAuth Consent Screen

**⚠️ This step is crucial and often skipped!**

1. **Navigate to OAuth Consent Screen**
   - Go to "APIs & Services" > "OAuth consent screen"

2. **Choose User Type**
   - Select "External" (unless you have a Google Workspace account)
   - Click "Create"

3. **Fill Required Information**
   - **App name**: "Sunnyside Calendar Integration"
   - **User support email**: Your email address
   - **App logo**: Optional (can skip for development)
   - **App domain**: Leave blank for development
   - **Developer contact information**: Your email address
   - Click "Save and Continue"

4. **Add Scopes**
   - Click "Add or Remove Scopes"
   - Search for "calendar" in the filter
   - Select: `https://www.googleapis.com/auth/calendar.readonly`
   - Click "Update"
   - Click "Save and Continue"

5. **Add Test Users** (Important for development)
   - Click "Add Users"
   - Add your email address and any other test accounts
   - Click "Save and Continue"

### 4. Create OAuth 2.0 Credentials

1. **Navigate to Credentials**
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth client ID"

2. **Configure OAuth Client**
   - **Application type**: Select "Web application"
   - **Name**: "Sunnyside Web Client"

3. **Add Authorized Redirect URIs** (Critical Step)
   - Click "Add URI" under "Authorized redirect URIs"
   - Add: `http://localhost:8000/api/v1/calendar/auth/google/callback`
   - For production, also add: `https://yourdomain.com/api/v1/calendar/auth/google/callback`

4. **Save and Download**
   - Click "Create"
   - **Copy the Client ID and Client Secret** (you'll need these immediately)
   - Optionally download the JSON file for backup

## Backend Configuration

### 1. Install Dependencies

The required Google Calendar dependencies should already be in `requirements.txt`. If not, install them:

```bash
cd backend
pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
```

Or install all dependencies:
```bash
pip install -r requirements.txt
```

### 2. Environment Variables Setup

**Option A: Use the Quick Setup Script**
```bash
python scripts/setup_google_calendar.py
```

**Option B: Manual Setup**

Add these lines to your `.env` file (replace with your actual credentials):

```env
# Google Calendar Integration
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8000/api/v1/calendar/auth/google/callback
```

**⚠️ Important Notes:**
- Replace `your-client-id` and `your-client-secret` with actual values from Google Cloud Console
- The redirect URI must match exactly what you configured in Google Cloud Console
- No quotes needed around the values in the .env file

### 3. Verify Your Setup

Run the verification script to check if everything is configured correctly:

```bash
python scripts/verify_google_calendar_setup.py
```

### 4. Database Migration (If Needed)

The User model has been extended with Google Calendar fields. If you're using an existing database, you may need to update existing user documents:

```javascript
// MongoDB shell command to add new fields to existing users
db.users.updateMany(
  {},
  {
    $set: {
      google_calendar_integrated: false,
      google_calendar_credentials: null
    }
  }
)
```

**Or use the Python script:**
```bash
python scripts/update_user_schema.py
```

## Frontend Configuration

No additional configuration is needed for the frontend. The integration is automatically available in:

1. **Onboarding Flow**: Step 4 offers optional Google Calendar connection
2. **Weather Planning**: Shows availability when organizer has calendar integrated
3. **Invitee Response**: Provides calendar-based suggestions for registered users

## API Endpoints

The following endpoints are available for Google Calendar integration:

### Authentication
- `GET /api/v1/calendar/auth/google` - Initiate OAuth flow
- `GET /api/v1/calendar/auth/google/callback` - Handle OAuth callback

### Calendar Data
- `GET /api/v1/calendar/availability` - Get user's calendar availability
- `GET /api/v1/calendar/status` - Check integration status
- `DELETE /api/v1/calendar/integration` - Disconnect integration

## Testing the Integration

### 1. Start the Backend

```bash
cd backend
python run.py
```

### 2. Start the Frontend

```bash
cd frontend
npm run dev
```

### 3. Test the Flow

1. Create a new account or log in
2. During onboarding, try connecting Google Calendar
3. Create an activity and select a date to see availability
4. Invite someone and check if calendar suggestions appear

## Security Considerations

1. **Token Storage**: OAuth tokens are stored encrypted in the database
2. **Scope Limitation**: Only read-only calendar access is requested
3. **Token Refresh**: Access tokens are automatically refreshed when needed
4. **Error Handling**: Calendar failures don't break core functionality

## Troubleshooting

### 🔧 Common Issues and Solutions

#### 1. **503 Service Unavailable Error**
```json
{"error":"Google Calendar integration is not available","reason":"Missing configuration or dependencies","setup_required":true}
```

**Solution:**
- Check if `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` are in your `.env` file
- Run: `python scripts/verify_google_calendar_setup.py`
- Restart your backend server after adding credentials

#### 2. **"redirect_uri_mismatch" Error**
```
Error 400: redirect_uri_mismatch
```

**Solution:**
- Ensure the redirect URI in Google Cloud Console matches exactly: `http://localhost:8000/api/v1/calendar/auth/google/callback`
- Check for trailing slashes and protocol (http vs https)
- Verify you're using the correct port (8000 for backend)

#### 3. **"invalid_client" Error**
```
Error 401: invalid_client
```

**Solution:**
- Verify `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` are correct (copy-paste from Google Cloud Console)
- Ensure the OAuth client is configured as "Web application"
- Check that the credentials are from the same project where you enabled the Calendar API

#### 4. **"access_denied" Error**
```
Error: access_denied
```

**Solution:**
- Make sure you added your email as a test user in the OAuth consent screen
- Verify the OAuth consent screen is properly configured
- Check that the Calendar API scope is added: `https://www.googleapis.com/auth/calendar.readonly`

#### 5. **Calendar Data Not Loading**

**Solution:**
- Check browser console for API errors (F12 → Console)
- Verify the user has granted calendar permissions during OAuth flow
- Ensure the Google Calendar API is enabled in your project
- Test with: `curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8000/api/v1/calendar/status`

#### 6. **Token Refresh Issues**

**Solution:**
- The refresh token is only provided on the first authorization
- If testing repeatedly, revoke access in your Google Account settings and re-authorize
- Go to: https://myaccount.google.com/permissions → Remove Sunnyside app → Try again

#### 7. **Dependencies Missing**

**Solution:**
```bash
pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
```

### 🐛 Debug Mode

Enable detailed logging to troubleshoot issues:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Or set in your `.env` file:
```env
DEBUG=true
```

### 🧪 Testing Your Setup

1. **Check Environment Variables:**
```bash
python -c "import os; print('CLIENT_ID:', os.getenv('GOOGLE_CLIENT_ID', 'NOT SET')); print('CLIENT_SECRET:', 'SET' if os.getenv('GOOGLE_CLIENT_SECRET') else 'NOT SET')"
```

2. **Test API Endpoint:**
```bash
curl -X GET "http://localhost:8000/api/v1/calendar/auth/google" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

3. **Check Service Status:**
```bash
python -c "from backend.services.google_calendar import google_calendar_service; print('Enabled:', google_calendar_service.enabled)"
```

## Privacy and Compliance

- Users can disconnect their calendar at any time
- Only calendar event times and titles are accessed (read-only)
- No calendar events are created, modified, or deleted
- Calendar data is used only for availability suggestions
- Users are informed about data usage during the connection process

## Production Deployment

1. Update redirect URIs in Google Cloud Console for production domain
2. Use HTTPS for all OAuth flows
3. Set appropriate CORS origins
4. Monitor API quotas and usage
5. Implement proper error logging and monitoring

## 📊 API Quotas and Limits

Google Calendar API has the following default quotas:
- **1,000,000 requests per day** (per project)
- **100 requests per 100 seconds per user**
- **10 requests per second** (per project)

### Monitoring Usage
- Check usage in Google Cloud Console → APIs & Services → Quotas
- Set up alerts for quota usage
- For production applications with many users, request quota increases

## 🔒 Security Best Practices

1. **Environment Variables**
   - Never commit `.env` files to version control
   - Use different credentials for development/production
   - Rotate credentials periodically

2. **OAuth Scopes**
   - Only request `calendar.readonly` scope (minimal permissions)
   - Never request more permissions than needed

3. **Token Storage**
   - Tokens are encrypted in the database
   - Implement proper token refresh logic
   - Handle token expiration gracefully

## 📱 Production Deployment Checklist

- [ ] Update redirect URIs for production domain
- [ ] Use HTTPS for all OAuth flows
- [ ] Set appropriate CORS origins
- [ ] Monitor API quotas and usage
- [ ] Implement proper error logging
- [ ] Set up health checks for calendar integration
- [ ] Configure rate limiting
- [ ] Set up monitoring and alerts

## 🆘 Getting Help

If you're still having issues:

1. **Run the verification script:** `python scripts/verify_google_calendar_setup.py`
2. **Check the logs:** Look for errors in your backend console
3. **Test step by step:** Use the testing commands provided above
4. **Review Google Cloud Console:** Ensure all settings match this guide

**Common Setup Time:** 10-15 minutes for first-time setup
**Common Issues:** 90% are related to redirect URI mismatches or missing test users