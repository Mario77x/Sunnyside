# Google Calendar Integration Setup

This document provides step-by-step instructions for setting up Google Calendar integration in the Sunnyside application.

## Prerequisites

1. A Google Cloud Platform (GCP) project
2. Google Calendar API enabled
3. OAuth 2.0 credentials configured

## Google Cloud Setup

### 1. Create a Google Cloud Project

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Note your project ID

### 2. Enable Google Calendar API

1. In the Google Cloud Console, navigate to "APIs & Services" > "Library"
2. Search for "Google Calendar API"
3. Click on it and press "Enable"

### 3. Create OAuth 2.0 Credentials

1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth client ID"
3. If prompted, configure the OAuth consent screen:
   - Choose "External" for user type
   - Fill in the required fields (App name, User support email, Developer contact)
   - Add scopes: `https://www.googleapis.com/auth/calendar.readonly`
   - Add test users if needed
4. For Application type, select "Web application"
5. Add authorized redirect URIs:
   - For development: `http://localhost:8000/api/v1/calendar/auth/google/callback`
   - For production: `https://yourdomain.com/api/v1/calendar/auth/google/callback`
6. Save and note the Client ID and Client Secret

## Backend Configuration

### 1. Install Dependencies

The required dependencies are already added to `requirements.txt`:

```bash
cd backend
pip install -r requirements.txt
```

### 2. Environment Variables

Add the following to your `.env` file:

```env
GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-google-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8000/api/v1/calendar/auth/google/callback
```

### 3. Database Migration

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

### Common Issues

1. **"redirect_uri_mismatch" Error**
   - Ensure the redirect URI in Google Cloud Console matches exactly
   - Check for trailing slashes and protocol (http vs https)

2. **"invalid_client" Error**
   - Verify GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET are correct
   - Ensure the OAuth client is for a "Web application"

3. **Calendar Data Not Loading**
   - Check browser console for API errors
   - Verify the user has granted calendar permissions
   - Ensure the Google Calendar API is enabled

4. **Token Refresh Issues**
   - The refresh token is only provided on the first authorization
   - If testing, you may need to revoke access and re-authorize

### Debug Mode

Enable debug logging in the backend:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
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

## API Quotas

Google Calendar API has the following default quotas:
- 1,000,000 requests per day
- 100 requests per 100 seconds per user

For production applications with many users, you may need to request quota increases.