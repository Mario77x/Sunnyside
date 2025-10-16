# Google Calendar Integration Testing Guide

## 🚀 Application Status

### ✅ Current Setup
- **Backend**: Running on `http://localhost:8000` (Process ID: 6914)
- **Frontend**: Running on `http://localhost:5137`
- **Database**: MongoDB with secrets management
- **Google Calendar**: Enhanced integration implemented

## 🧪 Testing Checklist

### 1. Basic Application Access
- [ ] **Frontend loads**: Navigate to `http://localhost:5137`
- [ ] **Backend health**: Verify `http://localhost:8000/healthz` responds
- [ ] **Authentication**: Test user signup/login flow
- [ ] **Database connection**: Verify user data persistence

### 2. Google Calendar Integration Testing

#### 2.1 Onboarding Flow (Enhanced)
**Test Steps:**
1. Navigate to onboarding (`/onboarding`)
2. Complete steps 1-3 (Basic Info, Location, Preferences)
3. **Step 4 - Calendar Integration:**
   - [ ] Calendar connection UI displays properly
   - [ ] "Connect Google Calendar" button works
   - [ ] Loading states show during connection
   - [ ] Success/error messages display correctly
   - [ ] "Skip for now" option works
   - [ ] Privacy information is clear and comprehensive

**Expected Enhancements:**
- Real-time connection status tracking
- Enhanced error handling with retry options
- Better visual indicators for connection states
- Comprehensive benefits and privacy information

#### 2.2 Account Settings Calendar Management
**Test Steps:**
1. Navigate to Account Settings (`/account`)
2. Locate "Google Calendar Integration" section
3. **Test Features:**
   - [ ] Connection status displays correctly
   - [ ] Connect/disconnect functionality works
   - [ ] Loading states during operations
   - [ ] Error handling and user feedback
   - [ ] Benefits explanation is clear

**Expected Features:**
- Visual status indicators (connected/disconnected)
- One-click connect/disconnect
- Clear benefits and privacy information
- Proper error recovery options

#### 2.3 Weather Planning Enhanced Calendar Display
**Test Steps:**
1. Create a new activity
2. Navigate to Weather Planning page
3. Select a date for the activity
4. **Test Calendar Features:**
   - [ ] Calendar availability loads automatically
   - [ ] Availability score displays (0-100%)
   - [ ] Detailed availability analytics show
   - [ ] Free time slots are visualized
   - [ ] Busy times are clearly marked
   - [ ] Recommended times are suggested

**Expected Enhancements:**
- Availability score with color coding
- Visual busy/free time indicators
- Comprehensive availability statistics
- Integration with weather planning decisions

#### 2.4 Invitee Response Smart Suggestions
**Test Steps:**
1. Access an activity invitation (as invitee)
2. Navigate to response page
3. **Test Calendar Features:**
   - [ ] Smart calendar suggestions load
   - [ ] Availability score shows
   - [ ] Free time slots preview displays
   - [ ] Conflict detection works
   - [ ] Custom availability notes work

**Expected Enhancements:**
- AI-powered availability suggestions
- Real-time calendar conflict detection
- Visual free time slot previews
- Intelligent time recommendations

### 3. New Components Testing

#### 3.1 Calendar Availability Overlay
**Component Location:** `frontend/src/components/CalendarAvailabilityOverlay.tsx`

**Test Features:**
- [ ] Visual calendar grid displays
- [ ] Busy/free times are color-coded
- [ ] Interactive time slot selection
- [ ] Activity duration consideration
- [ ] Week/day view options
- [ ] Real-time availability updates

#### 3.2 Real-time Availability Hooks
**Hook Location:** `frontend/src/hooks/useCalendarAvailability.ts`

**Test Features:**
- [ ] Auto-refresh functionality
- [ ] Real-time conflict detection
- [ ] Intelligent caching
- [ ] Error handling and recovery
- [ ] Multiple hook variants work

### 4. Backend API Testing

#### 4.1 Enhanced Calendar Endpoints
**Test Endpoints:**
```bash
# Calendar status
curl -H "Authorization: Bearer <token>" http://localhost:8000/api/v1/calendar/status

# Basic availability
curl -H "Authorization: Bearer <token>" "http://localhost:8000/api/v1/calendar/availability?start_date=2024-01-01T00:00:00Z&end_date=2024-01-07T23:59:59Z"

# Detailed availability (NEW)
curl -H "Authorization: Bearer <token>" "http://localhost:8000/api/v1/calendar/detailed-availability?start_date=2024-01-01T00:00:00Z&end_date=2024-01-07T23:59:59Z"

# OAuth initiation
curl -H "Authorization: Bearer <token>" http://localhost:8000/api/v1/calendar/auth/google

# Disconnect calendar
curl -X DELETE -H "Authorization: Bearer <token>" http://localhost:8000/api/v1/calendar/integration
```

#### 4.2 Smart Scheduling Integration
**Test Features:**
- [ ] Enhanced participant availability analysis
- [ ] Improved conflict detection
- [ ] Better scoring algorithms
- [ ] Integration with detailed calendar data

### 5. Error Handling Testing

#### 5.1 Network Errors
- [ ] Test with no internet connection
- [ ] Test with slow network
- [ ] Test API timeout scenarios
- [ ] Verify graceful degradation

#### 5.2 Authentication Errors
- [ ] Test expired OAuth tokens
- [ ] Test invalid credentials
- [ ] Test permission denied scenarios
- [ ] Verify token refresh mechanism

#### 5.3 Calendar API Errors
- [ ] Test Google API rate limits
- [ ] Test calendar access denied
- [ ] Test malformed calendar data
- [ ] Verify fallback behaviors

### 6. Performance Testing

#### 6.1 Calendar Data Loading
- [ ] Test with large calendar datasets
- [ ] Verify loading performance
- [ ] Test caching effectiveness
- [ ] Monitor memory usage

#### 6.2 Real-time Updates
- [ ] Test auto-refresh intervals
- [ ] Verify update frequency
- [ ] Test concurrent user scenarios
- [ ] Monitor API call efficiency

## 🔧 Troubleshooting Guide

### Common Issues and Solutions

#### Frontend Loading Issues
**Problem:** Frontend stuck on loading screen
**Solutions:**
1. Check backend connectivity: `curl http://localhost:8000/healthz`
2. Verify MongoDB connection
3. Check browser console for errors
4. Clear browser cache and localStorage

#### Backend Connection Issues
**Problem:** Backend not responding
**Solutions:**
1. Check if backend is running: `ps aux | grep uvicorn`
2. Restart backend: `cd backend && python run.py`
3. Check port availability: `lsof -i :8000`
4. Verify environment variables

#### Calendar Integration Issues
**Problem:** Google Calendar not connecting
**Solutions:**
1. Verify Google OAuth credentials in MongoDB secrets
2. Check redirect URI configuration
3. Verify Google Calendar API is enabled
4. Check browser popup blockers

#### Database Issues
**Problem:** MongoDB connection errors
**Solutions:**
1. Verify MongoDB URI in environment
2. Check MongoDB service status
3. Verify database permissions
4. Check secrets encryption key

## 📋 Pre-Testing Setup Checklist

### Environment Setup
- [ ] MongoDB running and accessible
- [ ] Environment variables configured
- [ ] Google OAuth credentials set up
- [ ] Secrets properly stored in MongoDB
- [ ] Backend dependencies installed
- [ ] Frontend dependencies installed

### Google Calendar API Setup
- [ ] Google Cloud Project created
- [ ] Calendar API enabled
- [ ] OAuth 2.0 credentials configured
- [ ] Redirect URIs properly set
- [ ] Test Google account available

### Application Configuration
- [ ] Backend running on port 8000
- [ ] Frontend running on port 5137
- [ ] CORS properly configured
- [ ] API endpoints accessible
- [ ] Authentication working

## 🎯 Testing Scenarios

### Scenario 1: New User Onboarding
1. New user signs up
2. Completes onboarding with calendar connection
3. Creates first activity
4. Views calendar integration in weather planning
5. Invites friends to activity

### Scenario 2: Existing User Calendar Connection
1. Existing user logs in
2. Goes to account settings
3. Connects Google Calendar
4. Tests calendar features in activity planning
5. Verifies availability suggestions

### Scenario 3: Invitee Response with Calendar
1. User receives activity invitation
2. Opens invitation link
3. Views smart calendar suggestions
4. Responds with availability information
5. Verifies calendar conflict detection

### Scenario 4: Smart Scheduling Integration
1. Organizer creates activity with multiple invitees
2. System analyzes participant calendars
3. Provides optimal time suggestions
4. Considers weather and preferences
5. Generates AI-powered recommendations

## 📊 Success Metrics

### Functional Metrics
- [ ] All calendar endpoints respond correctly
- [ ] OAuth flow completes successfully
- [ ] Calendar data loads and displays properly
- [ ] Real-time updates work as expected
- [ ] Error handling provides good user experience

### Performance Metrics
- [ ] Calendar data loads within 3 seconds
- [ ] UI remains responsive during operations
- [ ] Memory usage stays within acceptable limits
- [ ] API calls are optimized and efficient

### User Experience Metrics
- [ ] Calendar connection process is intuitive
- [ ] Availability suggestions are helpful
- [ ] Visual calendar overlay is clear
- [ ] Error messages are actionable
- [ ] Overall flow feels seamless

## 🚀 Ready for Testing

The enhanced Google Calendar integration is now ready for comprehensive testing. Both backend and frontend are running, and all enhanced features have been implemented according to the specifications.

**Next Steps:**
1. Follow this testing guide systematically
2. Report any issues found during testing
3. Verify all enhanced features work as expected
4. Test edge cases and error scenarios
5. Validate performance under load

**Support:**
- Backend logs: Check terminal running `python run.py`
- Frontend logs: Check browser developer console
- Database logs: Check MongoDB logs
- API testing: Use provided curl commands