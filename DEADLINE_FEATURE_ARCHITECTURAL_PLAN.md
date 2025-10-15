# Architectural Plan: Deadline and Notification Feature

This document outlines the architectural design for implementing deadlines in invites and sending notifications to organizers when deadlines are due.

## 1. Backend Modifications

### 1.1. Data Model Changes

The `Activity` model in [`backend/models/activity.py`](backend/models/activity.py) will be updated to include a `deadline` field.

- **Field**: `deadline`
- **Type**: `datetime`
- **Description**: Stores the deadline for invite responses.

### 1.2. API Endpoint Changes

The following endpoints in [`backend/routes/activities.py`](backend/routes/activities.py) will be modified:

- **`POST /activities`**: The `create_activity` endpoint will be updated to accept a `deadline` in the request body. This value will be saved to the new `deadline` field in the `Activity` model.
- **`GET /activities/{activity_id}`**: The `get_activity` endpoint will be updated to include the `deadline` in the response.

### 1.3. Notification System

A new scheduled task will be created to handle deadline notifications. This task will:

- Run periodically (e.g., once a day).
- Query the database for activities with deadlines that are approaching or have passed.
- For each activity, it will trigger a notification to the organizer.

The existing notification service in [`backend/services/notifications.py`](backend/services/notifications.py) will be extended to support deadline-related notifications.

## 2. Frontend Modifications

### 2.1. API Service Changes

The `createActivity` function in [`frontend/src/services/api.ts`](frontend/src/services/api.ts) will be updated to include the `deadline` in the payload when creating a new activity.

### 2.2. Component Changes

The following components will be updated to integrate the deadline feature:

- **[`frontend/src/pages/CreateActivity.tsx`](frontend/src/pages/CreateActivity.tsx)**: A date picker will be added to the form to allow organizers to set a deadline when creating an activity.
- **[`frontend/src/pages/ActivitySummary.tsx`](frontend/src/pages/ActivitySummary.tsx)**: The deadline will be displayed on the activity summary page.
- **[`frontend/src/pages/InviteeResponse.tsx`](frontend/src/pages/InviteeResponse.tsx)**: The deadline will be displayed to invitees.
- **[`frontend/src/pages/GuestResponse.tsx`](frontend/src/pages/GuestResponse.tsx)**: The deadline will be displayed to guests.

## 3. Deadline Calculation

The deadline will be set by the organizer during activity creation. The frontend will provide a date picker, and the selected date will be sent to the backend. The [`frontend/src/utils/deadlineCalculator.ts`](frontend/src/utils/deadlineCalculator.ts) will not be used for this feature, as the deadline is set manually.

## 4. Notification Triggers and Content

- **Triggers**: Notifications will be triggered when a deadline is approaching (e.g., 24 hours before) and when it has passed.
- **Content**: The notification will inform the organizer that the deadline for a specific activity is approaching or has passed.

This plan provides a comprehensive overview of the required changes. Once approved, it can be handed off to the development team for implementation.