# EmailJS Integration Plan for Additional Notifications

## 1. Analysis of Current Notification System

The current notification system, implemented in `backend/services/notifications.py`, is a robust service that handles both email and in-app notifications. It uses `httpx` to send emails via the EmailJS REST API.

### Current Email Notifications:

- **`send_activity_invitation_email`**: Sent to registered users when they are invited to an activity.
- **`send_activity_invitation_email_to_guest`**: A more detailed invitation sent to non-registered users.
- **`send_contact_request_email`**: Sent when a user wants to connect with another user.
- **`send_account_invitation_email`**: Sent to non-users when they are invited to join the platform.
- **`send_welcome_email`**: Sent to new users upon registration. This is the only notification that currently uses a specific EmailJS template (`EMAILJS_WELCOME_TEMPLATE_ID`).
- **`send_activity_cancellation_email`**: Sent when an activity is canceled.
- **`send_activity_response_notification_email`**: Sent to the organizer when an invitee responds.
- **`send_activity_response_changed_notification_email`**: Sent to the organizer when an invitee changes their response.
- **`send_activity_finalization_email`**: Sent to attendees when an activity's details are finalized.
- **`send_deadline_reminder_email`**: Sent to organizers as a reminder of the response deadline for an activity.

### Strengths:

-   Comprehensive coverage of the core activity lifecycle.
-   Clear separation of concerns, with dedicated methods for each notification type.
-   Handles both registered and guest users.

### Weaknesses:

-   **Hardcoded HTML**: All email content is generated using f-strings within each function. This makes the emails difficult to maintain, update, and style consistently.
-   **Lack of Templating**: With the exception of the welcome email, all emails use a generic template, passing the entire HTML body as a single `message` parameter. This underutilizes EmailJS's templating capabilities.
-   **Styling Inconsistencies**: While there is some inline styling, it's not consistent across all emails, and making global style changes would be a tedious and error-prone process.

## 2. Identifying Missing Notification Scenarios & Enhancement Opportunities

Based on the current implementation and best practices for user engagement, the following areas are opportunities for new notifications or enhancements.

### Missing Scenarios:

1.  **Contact Request Accepted**: Currently, there's an email for a contact request, but not one to notify the original requester that their invitation was accepted.
2.  **Password Reset/Forgot Password**: A standard but crucial feature for any application with user accounts.
3.  **Activity Update Notification**: If an organizer changes the details of an activity (e.g., date, description), invitees should be notified.
4.  **Upcoming Activity Reminder**: A reminder sent to confirmed attendees 24 hours before an activity is scheduled to start.

### Enhancement Opportunities:

-   **Refactor all existing emails to use EmailJS templates.** This is the primary goal of this task. It will make the email content more manageable, consistent, and easier to style.

## 3. EmailJS Integration Plan

The plan is to create a dedicated EmailJS template for each of the existing and new notification types. This will involve modifying the `NotificationService` to use these templates.

### Step 1: Create EmailJS Templates

The following templates should be created in the EmailJS dashboard:

| Template Name                                | Template ID (in `.env`)                        | Purpose                                                              |
| -------------------------------------------- | ---------------------------------------------- | -------------------------------------------------------------------- |
| Activity Invitation                          | `EMAILJS_ACTIVITY_INVITATION_TEMPLATE_ID`      | For inviting registered users to an activity.                        |
| Guest Activity Invitation                    | `EMAILJS_GUEST_ACTIVITY_INVITATION_TEMPLATE_ID`| For inviting non-registered users to an activity.                    |
| Contact Request                              | `EMAILJS_CONTACT_REQUEST_TEMPLATE_ID`          | For notifying a user of a new contact request.                       |
| Contact Request Accepted (New)               | `EMAILJS_CONTACT_ACCEPTED_TEMPLATE_ID`         | For notifying a user that their contact request was accepted.        |
| Account Invitation                           | `EMAILJS_ACCOUNT_INVITATION_TEMPLATE_ID`       | For inviting new users to join the platform.                         |
| Activity Cancellation                        | `EMAILJS_ACTIVITY_CANCELLATION_TEMPLATE_ID`    | For notifying invitees that an activity has been canceled.           |
| Activity Response                            | `EMAILJS_ACTIVITY_RESPONSE_TEMPLATE_ID`        | For notifying an organizer of a new response.                        |
| Activity Response Changed                    | `EMAILJS_ACTIVITY_RESPONSE_CHANGED_TEMPLATE_ID`| For notifying an organizer that a response has changed.              |
| Activity Finalized                           | `EMAILJS_ACTIVITY_FINALIZED_TEMPLATE_ID`       | For notifying attendees that an activity has been finalized.         |
| Deadline Reminder                            | `EMAILJS_DEADLINE_REMINDER_TEMPLATE_ID`        | For reminding an organizer about an activity deadline.               |
| Activity Update (New)                        | `EMAILJS_ACTIVITY_UPDATE_TEMPLATE_ID`          | For notifying invitees of changes to an activity.                    |
| Upcoming Activity Reminder (New)             | `EMAILJS_UPCOMING_ACTIVITY_REMINDER_TEMPLATE_ID`| For reminding attendees about an upcoming activity.                  |
| Password Reset (New)                         | `EMAILJS_PASSWORD_RESET_TEMPLATE_ID`           | For sending a password reset link to a user.                         |

### Step 2: Update `.env.example`

Add all the new EmailJS template IDs to the `.env.example` file.

### Step 3: Refactor `NotificationService`

The `send_email` method will be updated to accept a `template_id` and a dictionary of `template_params`. Each of the specific `send_*_email` methods will be refactored to:
1.  Retrieve the appropriate `template_id` from the environment variables.
2.  Construct a `template_params` dictionary with the dynamic data required by the template.
3.  Call the `send_email` method with the `template_id` and `template_params`.

The hardcoded HTML generation will be removed from all `send_*_email` methods.

## 4. Template Design

All templates will share a common structure for consistency. They will be designed to be clean, responsive, and visually appealing.

### Base Template Structure (to be adapted in EmailJS):

```html
<!DOCTYPE html>
<html>
<head>
    <style>
        /* Basic styles for responsiveness and branding */
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <img src="path/to/sunnyside_logo.png" alt="Sunnyside Logo">
        </div>
        <div class="content">
            {{{content_body}}}
        </div>
        <div class="footer">
            <p>&copy; 2025 Sunnyside. All rights reserved.</p>
        </div>
    </div>
</body>
</html>```

### Example Template: `Activity Invitation`

**Template ID:** `EMAILJS_ACTIVITY_INVITATION_TEMPLATE_ID`

**Parameters:**
-   `to_name`
-   `organizer_name`
-   `activity_title`
-   `activity_description`
-   `custom_message`
-   `invite_link`
-   `date_info`
-   `weather_preference`
-   `group_size`

**Body (in EmailJS):**
```html
<h2 style="color: #2c5aa0;">You're Invited!</h2>
<p>Hi {{to_name}},</p>
<p>{{organizer_name}} has invited you to join an activity:</p>
<div class="activity-details">
    <h3>{{activity_title}}</h3>
    <p>{{activity_description}}</p>
    <p><strong>Date:</strong> {{date_info}}</p>
    <p><strong>Weather Preference:</strong> {{weather_preference}}</p>
    <p><strong>Group Size:</strong> {{group_size}}</p>
</div>
{{#if custom_message}}
<div class="personal-message">
    <p><strong>Personal message:</strong> {{custom_message}}</p>
</div>
{{/if}}
<a href="{{invite_link}}" class="button">Respond to Invitation</a>
```

This design pattern will be applied to all other templates.

## 5. Priority Ranking

Given that this is a "nice-to-have" feature, the implementation should be prioritized as follows:

1.  **High Priority (Core Functionality)**:
    -   Refactor existing invitation and notification emails (`send_activity_invitation_email`, `send_activity_invitation_email_to_guest`, `send_activity_response_notification_email`, `send_activity_finalization_email`). These are the most user-facing and critical emails.
2.  **Medium Priority (Important User Experience)**:
    -   Refactor other existing emails (`send_contact_request_email`, `send_account_invitation_email`, `send_activity_cancellation_email`, `send_deadline_reminder_email`).
    -   Implement **Password Reset**. This is a key functional gap.
3.  **Low Priority (Enhancements)**:
    -   Implement **Contact Request Accepted**, **Activity Update**, and **Upcoming Activity Reminder**. These are valuable for user engagement but not critical for core functionality.

This phased approach will allow for incremental implementation as time permits.