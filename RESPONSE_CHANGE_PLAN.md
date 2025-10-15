# Architectural Plan: Allow Invitees to Change Responses

This document outlines the architectural plan for implementing the feature that allows both registered and guest invitees to change their response after their initial choice, with notifications sent to the organizer.

## 1. Frontend Changes

### 1.1. `InviteeActivitySummary.tsx`

- **Objective**: Add a "Change Response" button to this page, which is displayed to invitees after they have submitted their response.
- **Changes**:
    - Add a new button with the label "Change Response" to the main card, next to the "Back to Dashboard" button.
    - When this button is clicked, the user will be navigated back to the `InviteeResponse.tsx` page.
    - The `activity` data will be passed in the navigation state to pre-fill the form.

### 1.2. `GuestResponse.tsx`

- **Objective**: This page will be updated to handle both initial submissions and response changes for guest users.
- **Changes**:
    - The page will check if a response has already been submitted for the given activity and guest email.
    - If a response exists, the form will be pre-filled with the existing data.
    - The submit button text will change from "Submit Response" to "Update Response".

### 1.3. `InviteeResponse.tsx`

- **Objective**: This page will be updated to handle both initial submissions and response changes for registered users.
- **Changes**:
    - The page will check if a response has already been submitted for the given activity and user.
    - If a response exists, the form will be pre-filled with the existing data.
    - The submit button text will change from "Submit Response" to "Update Response".

### 1.4. `api.ts`

- **Objective**: Add a new API service function to handle the response update.
- **Changes**:
    - A new function, `updateUserResponse`, will be added to send a `PUT` request to the new backend endpoint.

## 2. Backend Changes

### 2.1. `routes/activities.py`

- **Objective**: Add a new endpoint to handle response updates and modify the existing response submission logic.
- **Changes**:
    - A new `PUT` endpoint, `/{activity_id}/respond`, will be created to handle response updates.
    - The existing `POST` endpoint, `/{activity_id}/respond`, will be modified to check for existing responses. If a response already exists, it will call the update logic.
    - The `submit_user_response` function will be updated to:
        - Find the invitee in the `activity` document.
        - Store the previous response before updating it.
        - Trigger a new notification service function to send a "response changed" notification.

### 2.2. `models/activity.py`

- **Objective**: Update the `Invitee` model to store the previous response.
- **Changes**:
    - A new optional field, `previous_response: Optional[InviteeResponse]`, will be added to the `Invitee` model.

### 2.3. `services/notifications.py`

- **Objective**: Add a new function to send a "response changed" notification.
- **Changes**:
    - A new function, `send_activity_response_changed_notification_email`, will be created.
    - This function will generate an email that clearly states the user's name, the activity title, and the change in their response (e.g., "John Doe changed their response from Yes to Maybe").
    - A new in-app notification will also be created with a similar message.

## 3. Data Flow for Response Change

1.  **User Action**: The invitee clicks the "Change Response" button on the `InviteeActivitySummary.tsx` page.
2.  **Navigation**: The user is navigated to the `InviteeResponse.tsx` page with the activity data.
3.  **Form Submission**: The user modifies their response and clicks "Update Response".
4.  **API Request**: The frontend sends a `PUT` request to the `/activities/{activity_id}/respond` endpoint with the updated response data.
5.  **Backend Processing**:
    - The backend finds the activity and the invitee.
    - It stores the current response in the `previous_response` field.
    - It updates the invitee's response with the new data.
    - It calls the `NotificationService` to send a "response changed" notification to the organizer.
6.  **Notification**: The organizer receives an email and an in-app notification about the change.
7.  **UI Update**: The user is redirected to the `InviteeActivitySummary.tsx` page, which now displays the updated response.

## 4. Security Considerations

- **Guest Users**: The guest response flow will continue to rely on the unique link sent to their email, which contains the activity ID and their email address. This ensures that only the original recipient can change the response.
- **Registered Users**: The existing authentication and authorization mechanisms will ensure that only the logged-in user can change their own response. The backend will verify that the user is an invitee for the specified activity before allowing any changes.

This plan provides a comprehensive overview of the changes required to implement the response change feature.