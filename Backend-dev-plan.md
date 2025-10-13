# 1) Executive Summary
This document outlines the backend development plan for Sunnyside, a social planning application. The backend will be a FastAPI application using MongoDB Atlas for the database, designed to support the features implemented in the existing frontend.

The plan adheres to the specified constraints:
- **Backend:** FastAPI (Python 3.12), async.
- **Database:** MongoDB Atlas with Motor and Pydantic v2.
- **No Docker.**
- **Testing:** Manual testing through the frontend.
- **Git:** Single `main` branch workflow.
- **API:** Base path `/api/v1/*`.

The development is broken down into a dynamic number of sprints, starting with environment setup and progressively adding features like authentication, activity management, and guest handling to match the frontend's capabilities.

# 2) In-scope & Success Criteria
- **In-scope:**
  - User onboarding and account management.
  - Full activity creation and management lifecycle (from idea to finalization).
  - Guest invitation and response flow.
  - Weather-based planning suggestions (mocked initially).
  - AI-powered activity recommendations (mocked initially).
- **Success criteria:**
  - All frontend features are fully supported by the backend.
  - Each sprint's deliverables pass manual UI-driven tests.
  - The backend is successfully deployed and connected to the frontend.
  - Code is pushed to the `main` branch on GitHub after each successful sprint.

# 3) API Design
- **Conventions:**
  - Base path: `/api/v1`.
  - Errors will return a consistent JSON object: `{"detail": "Error message"}`.
- **Endpoints:**

  - **Health Check**
    - `GET /healthz`: Checks API and database connectivity.
      - **Response:** `{"status": "ok", "db_status": "connected"}`

  - **Authentication**
    - `POST /api/v1/auth/signup`: Register a new user.
      - **Request:** `{ "name": "string", "email": "string", "password": "string", "location": "string", "preferences": ["string"] }`
      - **Response:** `{ "access_token": "string", "token_type": "bearer" }`
    - `POST /api/v1/auth/login`: Authenticate a user.
      - **Request:** `{ "username": "string", "password": "string" }` (using email as username)
      - **Response:** `{ "access_token": "string", "token_type": "bearer" }`
    - `GET /api/v1/auth/me`: Get current user details.
      - **Response:** `{ "id": "string", "name": "string", "email": "string", "location": "string", "preferences": ["string"] }`

  - **Activities**
    - `POST /api/v1/activities`: Create a new activity.
      - **Request:** `{ "title": "string", "description": "string", "timeframe": "string", "groupSize": "string", "activityType": "string", "weatherPreference": "string", "selectedDate": "date-time" }`
      - **Response:** The created activity object.
    - `GET /api/v1/activities`: Get all activities for the current user (both organized and invited).
      - **Response:** `[Activity]`
    - `GET /api/v1/activities/{activity_id}`: Get a single activity.
      - **Response:** `Activity`
    - `PUT /api/v1/activities/{activity_id}`: Update an activity (e.g., add weather data, invitees).
      - **Request:** Partial `Activity` object.
      - **Response:** The updated activity object.

  - **Invitations & Responses**
    - `POST /api/v1/activities/{activity_id}/invite`: Send invitations.
      - **Request:** `{ "invitees": [{"name": "string", "email": "string"}], "customMessage": "string" }`
      - **Response:** `{ "message": "Invitations sent" }`
    - `POST /api/v1/invites/{invite_id}/respond`: Submit a response (for guests).
      - **Request:** `{ "response": "string", "availabilityNote": "string", "preferences": {}, "venueSuggestion": "string" }`
      - **Response:** `{ "message": "Response submitted" }`
    - `GET /api/v1/invites/{invite_id}`: Get activity details for a guest.
      - **Response:** `Activity` (public version with limited info)

# 4) Data Model (MongoDB Atlas)
- **Collections:**

  - **`users`**
    - `_id`: ObjectId (auto-generated)
    - `name`: String, required
    - `email`: String, required, unique
    - `hashed_password`: String, required
    - `location`: String, optional
    - `preferences`: Array of strings, optional
    - `createdAt`: DateTime, default: now
    - **Example Document:**
      ```json
      {
        "_id": "634...",
        "name": "Alex",
        "email": "alex@example.com",
        "hashed_password": "...",
        "location": "Amsterdam",
        "preferences": ["outdoor", "drinks"],
        "createdAt": "2025-10-13T10:00:00Z"
      }
      ```

  - **`activities`**
    - `_id`: ObjectId (auto-generated)
    - `organizer_id`: ObjectId, ref: `users`
    - `title`: String, required
    - `description`: String, optional
    - `status`: String, required, default: 'planning'
    - `weatherPreference`: String, optional
    - `selectedDate`: DateTime, optional
    - `selectedDays`: Array of strings, optional
    - `weatherData`: Array of objects, optional
    - `invitees`: Array of embedded documents
      - `id`: ObjectId (can be user_id or new ObjectId for guest)
      - `name`: String
      - `email`: String
      - `response`: String, default: 'pending'
      - `availabilityNote`: String, optional
      - `preferences`: Object, optional
    - `createdAt`: DateTime, default: now
    - **Example Document:**
      ```json
      {
        "_id": "635...",
        "organizer_id": "634...",
        "title": "Weekend Brunch",
        "description": "Brunch with friends",
        "status": "invitations-sent",
        "weatherPreference": "outdoor",
        "selectedDate": "2025-10-18T11:00:00Z",
        "invitees": [
          { "id": "634...", "name": "Maria", "email": "maria@example.com", "response": "yes" },
          { "id": "636...", "name": "Guest User", "email": "guest@example.com", "response": "pending" }
        ],
        "createdAt": "2025-10-13T11:00:00Z"
      }
      ```

# 5) Frontend Audit & Feature Map
- **`Onboarding.tsx` & `Account.tsx`**
  - **Purpose:** User registration and profile management.
  - **Backend:** `POST /api/v1/auth/signup`, `GET /api/v1/auth/me`. Powered by the `users` model.
- **`Index.tsx`**
  - **Purpose:** Dashboard to view organized and invited activities.
  - **Backend:** `GET /api/v1/activities`. Powered by the `activities` model.
- **`CreateActivity.tsx`**
  - **Purpose:** Initial activity creation using a chat-like interface.
  - **Backend:** `POST /api/v1/activities`. Creates a new document in the `activities` collection.
- **`WeatherPlanning.tsx`**
  - **Purpose:** Select potential dates based on mock weather data.
  - **Backend:** `PUT /api/v1/activities/{activity_id}` to update the activity with selected days.
- **`InviteGuests.tsx`**
  - **Purpose:** Add invitees and send invitations.
  - **Backend:** `PUT /api/v1/activities/{activity_id}` to add invitees to the activity document.
- **`GuestResponse.tsx`**
  - **Purpose:** Allow non-registered users to respond to an invitation.
  - **Backend:** `GET /api/v1/invites/{invite_id}` to fetch activity details and `POST /api/v1/invites/{invite_id}/respond` to save the response. Updates the embedded invitee document in the `activities` collection.

# 6) Configuration & ENV Vars (core only)
- `APP_ENV`: `development`
- `PORT`: `8000`
- `MONGODB_URI`: `mongodb+srv://sunnyside_db_user:GCWkLShMGwJtwNTD@cluster0.rskmhym.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0`
- `JWT_SECRET`: A long, random string for signing JWTs.
- `JWT_EXPIRES_IN`: `3600` (1 hour)
- `CORS_ORIGINS`: The frontend URL (e.g., `http://localhost:5173`).

# 9) Testing Strategy (Manual via Frontend)
- **Policy:** All backend functionality will be tested manually by interacting with the connected frontend. The browser's developer tools (Network tab) will be used to inspect API requests and responses.
- **Per-sprint Manual Test Checklist (Frontend):** Each sprint will include a checklist of UI actions to perform to validate the implemented backend features.
- **User Test Prompt:** A short, clear prompt will be provided for a non-technical user to test the functionality of each sprint.
- **Post-sprint:** If all tests pass, the code will be committed and pushed to the `main` branch on GitHub.

# 10) Dynamic Sprint Plan & Backlog (S0…Sn)
- **S0 - Environment Setup & Frontend Connection**
  - **Objectives:**
    - Create a basic FastAPI application with `/api/v1` router.
    - Implement a `/healthz` endpoint that checks database connectivity.
    - Set up MongoDB connection using Motor.
    - Configure CORS to allow requests from the frontend.
    - Initialize a Git repository and push to GitHub.
  - **Definition of Done:**
    - The FastAPI server runs locally.
    - The `/healthz` endpoint returns a successful response including DB status.
    - The frontend can successfully make a request to the backend.
    - The project is on GitHub with the `main` branch.
  - **Manual Test Checklist (Frontend):**
    - Start the backend server.
    - Open the frontend application in the browser.
    - Verify that there are no CORS errors in the console.
    - Use a tool like `curl` or Postman to hit the `/healthz` endpoint and verify the response.
  - **User Test Prompt:**
    - "Please run the backend and frontend applications. Open the frontend in your browser and let me know if you see any errors in the developer console."
  - **Post-sprint:**
    - Commit changes and push to `main`.

- **S1 - Basic Auth (signup, login, logout)**
  - **Objectives:**
    - Implement user registration (`/signup`) with password hashing.
    - Implement user login (`/login`) that returns a JWT.
    - Create a protected endpoint (`/me`) that requires a valid JWT.
    - Connect the frontend's Onboarding and Index pages to these endpoints.
  - **Definition of Done:**
    - A new user can register through the frontend.
    - A registered user can log in and receive a token.
    - The user's name is displayed on the dashboard after login.
    - Logging out clears the user's session on the frontend.
  - **Manual Test Checklist (Frontend):**
    - Go to the onboarding page and create a new account.
    - Verify that you are redirected to the main dashboard.
    - Refresh the page and confirm you are still logged in.
    - Click the "Sign Out" button.
    - Verify you are returned to the landing page.
    - Try to log in with the credentials you just created.
  - **User Test Prompt:**
    - "Please create an account, log out, and log back in. Confirm that you can access your dashboard after logging in."
  - **Post-sprint:**
    - Commit changes and push to `main`.

- **S2 - Activity Creation & Listing**
  - **Objectives:**
    - Implement `POST /api/v1/activities` to create a new activity.
    - Implement `GET /api/v1/activities` to list activities for the logged-in user.
    - Connect the `CreateActivity` and `Index` pages to these endpoints.
  - **Definition of Done:**
    - A logged-in user can create a new activity.
    - The new activity appears in the "Organized" tab on the dashboard.
    - The dashboard correctly separates organized and invited activities.
  - **Manual Test Checklist (Frontend):**
    - Log in to the application.
    - Click "New Activity" and fill out the initial form.
    - After creating the activity, verify it appears on the dashboard.
    - Create a test invite for your user and verify it appears in the "Invited" tab.
  - **User Test Prompt:**
    - "Please log in, create a new activity, and confirm it shows up on your dashboard. Also, create a test invitation for yourself and check if it appears in the 'Invited' section."
  - **Post-sprint:**
    - Commit changes and push to `main`.

- **S3 - Guest Flow & Responses**
  - **Objectives:**
    - Implement `GET /api/v1/invites/{invite_id}` to provide public activity data.
    - Implement `POST /api/v1/invites/{invite_id}/respond` to handle guest responses.
    - Implement `PUT /api/v1/activities/{activity_id}` to update the activity with guest responses.
  - **Definition of Done:**
    - A guest can view a simplified version of the activity page.
    - A guest can submit a response (yes/no/maybe) and preferences.
    - The organizer can see the guest's response on the activity summary page.
  - **Manual Test Checklist (Frontend):**
    - Create an activity and invite a guest (using an email not registered with the app).
    - Open the guest invitation link in an incognito window.
    - Submit a response as the guest.
    - Log in as the organizer and verify that the guest's response is visible.
  - **User Test Prompt:**
    - "Please create an activity and invite a friend who doesn't have an account. Ask them to respond to the invitation, and then check if you can see their response."
  - **Post-sprint:**
    - Commit changes and push to `main`.