# Todo List

- [ ] **Backend**: Update the `Activity` model in [`backend/models/activity.py`](backend/models/activity.py) to include a `deadline` field.
- [ ] **Backend**: Modify the `create_activity` endpoint in [`backend/routes/activities.py`](backend/routes/activities.py) to accept and save the `deadline`.
- [ ] **Backend**: Update the `get_activity` endpoint in [`backend/routes/activities.py`](backend/routes/activities.py) to return the `deadline`.
- [ ] **Backend**: Implement a new endpoint in [`backend/routes/notifications.py`](backend/routes/notifications.py) to handle deadline-related notifications.
- [ ] **Backend**: Create a scheduled task to check for upcoming and past deadlines and trigger notifications.
- [ ] **Frontend**: Update the `createActivity` function in [`frontend/src/services/api.ts`](frontend/src/services/api.ts) to send the `deadline` to the backend.
- [ ] **Frontend**: Modify the `CreateActivity` page in [`frontend/src/pages/CreateActivity.tsx`](frontend/src/pages/CreateActivity.tsx) to include a date picker for setting the deadline.
- [ ] **Frontend**: Update the `ActivitySummary` page in [`frontend/src/pages/ActivitySummary.tsx`](frontend/src/pages/ActivitySummary.tsx) to display the deadline.
- [ ] **Frontend**: Update the `InviteeResponse` page in [`frontend/src/pages/InviteeResponse.tsx`](frontend/src/pages/InviteeResponse.tsx) to show the deadline to invitees.
- [ ] **Frontend**: Update the `GuestResponse` page in [`frontend/src/pages/GuestResponse.tsx`](frontend/src/pages/GuestResponse.tsx) to show the deadline to guests.