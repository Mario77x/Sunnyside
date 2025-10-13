# Project Blueprint: Sunnyside

## Phase 1: High-Level Architectural Decisions

### 1.1. Architecture Pattern Selection

*   **Decision:** Modular Monolith
*   **Rationale:** For a solo developer, a well-structured monolith maximizes development speed and reduces operational complexity. A modular approach will ensure a clean separation of concerns, making the application maintainable and scalable without the overhead of a microservices architecture.

### 1.2. Technology Stack Selection

All versions are the latest stable releases as of October 2025.

*   **Frontend Framework & UI:**
    *   **Framework:** Next.js
    *   **Version:** ~16.0.0
    *   **Rationale:** Next.js provides a powerful and flexible framework for building modern React applications. The App Router will be used for its improved data fetching and layout capabilities.
    *   **UI Components:** shadcn/ui
    *   **Version:** ~0.9.5
    *   **Rationale:** shadcn/ui offers accessible and unstyled components that can be easily customized, avoiding lock-in to a specific design system.

*   **Backend Runtime & Framework:**
    *   **Runtime:** Python
    *   **Version:** ~3.14
    *   **Rationale:** Python's readability, extensive libraries, and strong community support make it a solid foundation for the backend.
    *   **Framework:** FastAPI
    *   **Version:** ~0.119.0
    *   **Rationale:** FastAPI is a high-performance web framework for Python. Its automatic interactive documentation and Pydantic-based data validation will significantly speed up development.

*   **Primary Database:**
    *   **Database:** MongoDB Atlas (Free Tier)
    *   **Rationale:** A NoSQL document database like MongoDB provides the flexibility needed for agile development where data models can evolve.

### 1.3. Core Infrastructure & Services (Local Development Focus)

*   **Local Development:** The project will be run using simple command-line instructions (`npm run dev` for frontend, `uvicorn main:app --reload` for backend). No containerization is needed for local development.
*   **File Storage:** A local, git-ignored `./uploads` directory will be used for any file uploads.
*   **Job Queues:** Celery will be used for any asynchronous background processing.
*   **Authentication:** A library-based approach with JWTs (JSON Web Tokens) will be used.
*   **External Services:**
    *   **Weather:** KNMI OpenAPI (Note: This service is specific to the Netherlands).
    *   **LLM:** Mistral AI
    *   **Email:** EmailJS (Note: Primarily a client-side service; backend integration will be done via its REST API).
    *   **SMS/WhatsApp:** Twilio
    *   **Calendar:** Google Calendar API

### 1.4. Integration and API Strategy

*   **API Style:** REST, with all APIs versioned from the start (e.g., `/api/v1/...`).
*   **Standard Formats:** A standard JSON structure will be defined for success and error responses.

## Phase 2: Detailed Module Architecture

### 2.1. Module Identification

*   **Domain Modules:**
    *   `UserModule`: Manages user authentication, profiles, and settings.
    *   `ActivityModule`: Manages activity creation, updates, and retrieval.
    *   `InviteModule`: Manages sending and tracking invitations.
    *   `RecommendationModule`: Generates activity recommendations using Mistral AI.
    *   `NotificationModule`: Manages in-app, email (EmailJS), and SMS/WhatsApp (Twilio) notifications.
    *   `IntegrationModule`: Manages external service integrations like Google Calendar.
*   **Infrastructure Modules:**
    *   `DatabaseModule`: Handles all MongoDB interactions.
    *   `WeatherModule`: Fetches and processes weather data from KNMI.
    *   `LLMModule`: Interacts with the Mistral AI API.
    *   `RiskAssessmentModule`: Assesses user input for harmful intent.
*   **Shared Module:**
    *   Contains shared UI components, utilities, and type definitions.

### 2.2. Module Responsibilities and Contracts (High-Level)

*   **UserModule:**
    *   **Responsibilities:** User registration, login, password management, profile updates.
    *   **Interface Contract:** `registerUser()`, `loginUser()`, `updateProfile()`, `getUserProfile()`.
*   **ActivityModule:**
    *   **Responsibilities:** Create, read, update, and delete activities.
    *   **Interface Contract:** `createActivity()`, `getActivity()`, `updateActivity()`, `deleteActivity()`.
*   **RecommendationModule:**
    *   **Responsibilities:** Generate activity recommendations based on user preferences, availability, and weather.
    *   **Interface Contract:** `getRecommendations()`.

### 2.3. Key Module Design

*   **Folder Structure:**
    *   **Backend:** A modular structure with each module having its own `routes`, `services`, and `models` directories.
    *   **Frontend:** Organized by feature, with each feature having its own `components`, `pages`, and `services` directories.
*   **Key Patterns:**
    *   **Repository Pattern:** Used for data access to decouple business logic from the database.
    *   **Dependency Injection:** FastAPI's dependency injection will be used to manage dependencies.

## Phase 3: Tactical Sprint-by-Sprint Plan

### Sprint S0: Project Foundation & Setup

*   **Goal:** Establish a fully configured, runnable project skeleton.
*   **Tasks:**
    1.  **Developer Onboarding & Repository Setup:** Get the developer's empty GitHub repository URL.
    2.  **Collect Secrets & Configuration:** Get MongoDB, KNMI, Mistral AI, EmailJS, and Twilio credentials, plus UI theme colors.
    3.  **Project Scaffolding:** Create a monorepo with `frontend` and `backend` directories, initialize Git, and create a `.gitignore` file.
    4.  **Backend Setup (Python/FastAPI):** Set up a virtual environment, install dependencies, create a basic file structure, and configure `.env` files.
    5.  **Frontend Setup (Next.js & shadcn/ui):** Scaffold the app, initialize shadcn/ui, configure `tailwind.config.js`, and create `.env` files.
    6.  **Documentation:** Create a `README.md` with project context and setup instructions.
    7.  **"Hello World" Verification:** Create a `/api/v1/health` endpoint and a frontend page to fetch from it.
    8.  **Final Commit:** Commit and push the initial project structure.

### Sprint S1: Weather API Integration (KNMI)

*   **Goal:** Integrate the KNMI API to display weather information.
*   **Tasks:**
    1.  **Backend:** Create a `WeatherModule` and an endpoint to expose weather data from the KNMI API.
    2.  **Frontend:** Create and integrate a `WeatherWidget` component to display the weather.
    3.  **User Test:** Verify correct weather data display for locations in the Netherlands.
    4.  **Final Commit:** Commit and push changes.

### Sprint S2: LLM Integration for Intent Parsing (Mistral AI)

*   **Goal:** Integrate Mistral AI to parse user intent from text input.
*   **Tasks:**
    1.  **Backend:** Create an `LLMModule` and an endpoint for intent parsing with Mistral AI.
    2.  **Frontend:** Create an input form and display the parsed intent.
    3.  **User Test:** Test intent parsing with various inputs.
    4.  **Final Commit:** Commit and push changes.

### Sprint S3: RAG for Activity Recommendations

*   **Goal:** Implement a RAG system using Mistral AI for activity recommendations.
*   **Tasks:**
    1.  **Backend:** Set up a vector database, implement a RAG pipeline, and create a recommendations endpoint.
    2.  **Frontend:** Display the recommendations.
    3.  **User Test:** Test the recommendation system.
    4.  **Final Commit:** Commit and push changes.

### Sprint S4: Risk Assessment

*   **Goal:** Implement a risk assessment module for user input.
*   **Tasks:**
    1.  **Backend:** Create and integrate a `RiskAssessmentModule`.
    2.  **User Test:** Test the module with various inputs.
    3.  **Final Commit:** Commit and push changes.

### Sprint S5: Email Service (EmailJS) and In-App Notifications

*   **Goal:** Implement email and in-app notifications.
*   **Tasks:**
    1.  **Backend:** Integrate EmailJS via its REST API and implement an in-app notification system.
    2.  **Frontend:** Display in-app notifications.
    3.  **User Test:** Test both notification systems.
    4.  **Final Commit:** Commit and push changes.

### Sprint S6: Calendar Integration (Google Calendar)

*   **Goal:** Integrate with the Google Calendar API.
*   **Tasks:**
    1.  **Backend:** Implement OAuth 2.0 and a service to manage calendar events.
    2.  **Frontend:** Add a button to add activities to Google Calendar.
    3.  **User Test:** Test the integration.
    4.  **Final Commit:** Commit and push changes.

### Sprint S7: WhatsApp and SMS Integration (Twilio)

*   **Goal:** Integrate with Twilio for WhatsApp and SMS notifications.
*   **Tasks:**
    1.  **Backend:** Integrate the Twilio API and create a messaging service.
    2.  **User Test:** Test the integration.
    3.  **Final Commit:** Commit and push changes.