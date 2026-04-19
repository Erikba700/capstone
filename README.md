##################Architecture for MVP:#######################

🏗️ 2️⃣ SIMPLE ARCHITECTURE DIAGRAM

                🌐 Internet
                     │
                     ▼
               ┌───────────┐
               │  Nginx    │  (Reverse Proxy)
               └─────┬─────┘
                     │
        ┌────────────┼────────────┐
        ▼                           ▼
┌──────────────┐           ┌──────────────┐
│  FastAPI App │           │  Frontend    │ (optional)
└──────┬───────┘           └──────────────┘
       │
       │
       ▼
┌──────────────┐
│ PostgreSQL   │  (Database)
└──────────────┘

       │
       ▼
┌──────────────┐
│ Redis        │  (Broker)
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ Celery Worker│  (Background jobs)
└──────────────┘

🔁 3️⃣ HOW EVERYTHING WORKS 

🟢 User Request
User → EC2 Public IP
      ↓
Nginx
      ↓
FastAPI

🔐 Authentication

FastAPI → verifies user → returns JWT

⏰ Create Reminder

User → POST /reminders
        ↓
FastAPI:
   - saves to PostgreSQL
   - schedules Celery task

⚙️ Background Execution

Celery Worker:
   waits → executes at scheduled time
        ↓
Sends notification (email / telegram)
        ↓
Stores notification in DB

🐳 4️⃣ DOCKER COMPOSE STRUCTURE

docker-compose.yml
│
├── app (FastAPI)
├── db (PostgreSQL)
├── redis
├── celery_worker
├── nginx

##################System Flow:#######################

🔐 STEP 1 — Authentication
User registers → email + password
        ↓
Password hashed (bcrypt)
        ↓
Stored in DB

Login:

User logs in
        ↓
Backend verifies password
        ↓
JWT token issued

Every request:

Client → Authorization: Bearer JWT
        ↓
FastAPI dependency extracts user_id

👤 STEP 2 — User & Group System

Flow:
User creates group
        ↓
User invites others via email
        ↓
Invitation link generated
        ↓
User joins group

⏰ STEP 3 — Creating a Reminder
User creates reminder
        ↓
Request contains:
   - title
   - scheduled_time
   - group_id (optional)
   - assignees

Backend:

1. Validate user permissions
2. Save reminder in PostgreSQL
3. Save assignees

⚙️ STEP 4 — Scheduling

After saving reminder:
        ↓
Backend calculates delay
        ↓
Calls Celery:
    apply_async(eta=scheduled_time)

🔁 STEP 5 — Celery Worker Execution

At the correct time:

Celery Worker wakes up
        ↓
Fetch reminder from DB
        ↓
Fetch assignees

🔔 STEP 6 — Sending Notifications

Flow:
For each user:
    ↓
Create Notification record (DB)
    ↓
Send:
   - Email (SMTP)
   - OR Telegram Bot API

📬 STEP 7 — Notification Storage

notifications table updated

This allows:

history
UI display
unread tracking

🔍 STEP 9 — Search & Invitations

User types user's email to invite
        ↓
Backend checks if user exists
        ↓
If yes → send invitation
If no → send invite email anyway

##########################API Endpoints:#############################

🧠 1️⃣ API DESIGN OVERVIEW

We split endpoints into domains:

/auth
/users
/reminders
/notifications
/groups (optional but strong for capstone)

🔐 2️⃣ AUTH ENDPOINTS

✅ Register
POST /auth/register
Request:
{
  "email": "user@example.com",
  "name": "Erik",
  "password": "123456"
}

What happens:
1. Validate email format
2. Hash password (bcrypt)
3. Save user in DB
4. Return success

✅ Login
POST /auth/login
Request:
{
  "email": "user@example.com",
  "password": "123456"
}
Response:
{
  "access_token": "JWT_TOKEN",
  "token_type": "bearer"
}

What happens:

1. Find user by email
2. Verify password
3. Generate JWT (user_id inside)
4. Return token

👤 3️⃣ USER ENDPOINTS (Dependency for auth)

✅ Get Current User
What happens:
1. Extract user_id from JWT
2. Return user info

⏰ 4️⃣ REMINDER ENDPOINTS (CORE)

✅ Create Reminder
POST /reminders
Authorization: Bearer <JWT>
Request:
{
  "title": "Buy bread",
  "description": "From supermarket",
  "scheduled_time": "2026-03-25T18:00:00",
  "assignee_ids": [2, 3],   // optional (future)
  "group_id": 1             // optional
}

🔥 What happens internally:
1. Extract user_id from JWT
2. Validate:
   - scheduled_time > now
   - user has access to group (if provided)
3. Create reminder in DB
4. Create reminder_assignees (if needed)
5. Schedule Celery task:
   send_reminder.apply_async(eta=scheduled_time)
6. Return created reminder

✅ Get All Reminders of the user
POST /reminders/search
Query params:
?from=2026-03-25
?to=2026-03-30
?completed=false
What happens:
1. Extract user_id
2. Query reminders where:
   - owner_id = user_id
   OR
   - user is assignee
3. Apply filters
4. Return list
✅ Get One Reminder
GET /reminders/{id}
1. Check ownership/access
2. Return reminder
✅ Update Reminder
PUT /reminders/{id}
What happens:
1. Validate ownership
2. Update DB fields
3. Reschedule Celery task

👉 (advanced: revoke old task — optional bonus)

✅ Delete Reminder
DELETE /reminders/{id}
1. Check ownership
2. Delete reminder
3. (optional) cancel Celery task
✅ Mark as Completed
PATCH /reminders/{id}/complete
1. Set is_completed = true

🔔 5️⃣ NOTIFICATION ENDPOINTS

✅ Get Notifications
GET /notifications
Query params:
?unread=true
What happens:
1. Extract user_id
2. Query notifications where user_id
3. Return sorted by created_at DESC

✅ Mark Notification as Read
PATCH /notifications/{id}/read
1. Update is_read = true

👥 6️⃣ GROUP ENDPOINTS (VERY GOOD FOR CAPSTONE)

✅ Create Group
POST /groups
1. Create group
2. Add creator as admin

✅ Invite User
POST /groups/{id}/invite
Request:
{
  "email": "friend@example.com"
}

What happens:
1. Generate invitation token
2. Save invitation in DB
3. Send email with link

✅ Accept Invitation
POST /groups/invitations/{token}/accept
1. Validate token
2. Add user to group

⚙️ 7️⃣ BACKGROUND TASK (IMPORTANT)

Celery Task
send_reminder(reminder_id)

What happens:
1. Load reminder
2. Get assignees (or owner)
3. For each user:
    - create notification in DB
    - send email / telegram

4. Mark reminder completed (optional)

🔄 8️⃣ FULL FLOW (END-TO-END)

🟢 User Flow
Register → Login → Get JWT
        ↓
Create Reminder
        ↓
Stored in DB
        ↓
Celery scheduled
        ↓
Time comes
        ↓
Worker runs
        ↓
Notifications created
        ↓
User fetches notifications

##################Missing Pieces You Should Add:#######################


These will upgrade your project significantly:

⭐ 1. Celery Beat (VERY IMPORTANT)

Instead of scheduling everything individually:

Celery Beat runs every minute
        ↓
Checks DB for due reminders
        ↓
Triggers tasks

👉 This solves:

lost jobs
system restarts
reliability
⭐ 2. Retry Mechanism
If notification fails:
    retry (Celery built-in)

👉 Looks very professional

⭐ 3. Status Tracking

Add fields:

notifications.status = sent | failed
⭐ 4. Timezone Handling

Very important:

Store everything in UTC
Convert on frontend
⭐ 5. Validation
Cannot create reminder in the past

explore uvicorn, nginx
make diagram of architecture
CI/CD pipeline
jwt token

##################Business logic:#######################
Notify one user:

User creates reminder, if you want to notify itself or other user you 
add a link to notification_recipients table which will have a 
id of the reminder, whom should it be sent and when should it be sent.
Notification worker will check this table every minute and send notifications
to users when the time comes. After sending notification, it will update the status 
of the notification_recipients of sent_at to the current time.

Notify group of users:
Creating a group of users