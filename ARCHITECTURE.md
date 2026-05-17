# Remindly — System Architecture & Design Description

## 1. Project Overview

**Remindly** is a full-stack collaborative reminder management web application. It allows users to
create personal reminders, form groups, assign reminders to group members, and receive email
notifications — including interactive email action links that let recipients acknowledge or complete
a reminder directly from their inbox without logging in.

---

## 2. Technology Stack

### Backend

| Technology | Role |
|---|---|
| **Python 3.14** | Primary backend language |
| **FastAPI** | Async REST API framework (ASGI) |
| **Uvicorn + uvloop** | ASGI server with high-performance event loop |
| **SQLAlchemy 2.0** (async) | ORM with async session support |
| **asyncpg / psycopg** | Async PostgreSQL drivers |
| **PostgreSQL 17** | Primary relational database |
| **Alembic** | Database schema migration tool |
| **Pydantic v2 + pydantic-settings** | Data validation, schema definitions, config management |
| **python-jose** | JWT token creation and validation |
| **passlib + bcrypt** | Password hashing |
| **Celery 5** | Distributed task queue for background jobs |
| **Redis 7** | Celery message broker and result backend |
| **structlog** | Structured JSON/console logging |
| **uv** | Fast Python package manager and virtual environment tool |

### Frontend

| Technology | Role |
|---|---|
| **React 19** | UI framework |
| **TypeScript 6** | Type-safe JavaScript |
| **Vite 8** | Dev server and build tool |
| **Tailwind CSS v4** | Utility-first CSS framework |
| **Axios** | HTTP client for API calls |
| **Zustand** | Lightweight global state management |
| **React Router DOM v7** | Client-side routing |
| **React Toastify** | Toast notifications |
| **date-fns** | Date formatting |

### Infrastructure

| Technology | Role |
|---|---|
| **Docker + Docker Compose** | Containerized multi-service deployment |
| **Ruff** | Python linting and formatting |
| **mypy** | Static type checking |

---

## 3. Backend Architecture — Four-Layer Pattern

The backend strictly follows a **four-layer Clean Architecture**:

```
HTTP Request
  → API Layer        (app/api/)       — FastAPI routers, HTTP handling
  → Schema Layer     (app/schemas/)   — Pydantic validation/serialization
  → Service Layer    (app/services/)  — Business logic orchestration
  → Repository Layer (app/repos/)     — Database access abstraction
  → Model Layer      (app/models/)    — SQLAlchemy ORM models
  → PostgreSQL Database
```

### 3.1 Presentation Layer — `app/api/`

FastAPI routers. Each module handles one domain area:

| File | Domain |
|---|---|
| `root.py` | Health check, version, actuator info |
| `users.py` | Signup, login, profile update |
| `reminders.py` | Personal reminder CRUD |
| `groups.py` | Group CRUD, member management, user search, email invitations |
| `group_reminders.py` | Jira-style collaborative reminder actions (assign, notify, update) |
| `reminder_assignees.py` | Assignment management + public email callback endpoint |
| `friends.py` | Friend request send/accept/reject/list |
| `debug.py` | Dev-only echo/crash endpoints |

Route handlers:
- Accept validated Pydantic schemas as request bodies
- Use FastAPI `Depends()` for dependency injection (session, auth, repos)
- Instantiate services per-request
- Return dicts or domain entities (serialized via `response_model`)

### 3.2 Application Layer — `app/services/`

Business logic. Services receive a `RepoFactory`, never deal with HTTP concerns.

| Service | Responsibility |
|---|---|
| `UserService` | User creation, lookup, profile update |
| `ReminderService` | Reminder CRUD, assignee sync, notification triggering |
| `GroupService` | Group CRUD, member management, invitation emails |
| `GroupReminderService` | Role-based collaborative reminder logic (assign, self-assign, notify) |
| `FriendshipService` | Friend request lifecycle |
| `NotificationService` | Notification creation, email send (plain + HTML with action buttons) |

Method naming convention by layer:

| Layer | Create | Read | Update | Delete |
|---|---|---|---|---|
| **Repos** | `insert` | `find`, `list` | `update` | `delete` |
| **Entities** | `create_new` | `find` | `update` | `remove` |
| **Services** | `create` | `fetch`, `view` | `update` | `remove` |
| **API** | `post` | `get` | `put`/`patch` | `delete` |

### 3.3 Domain Layer — `app/entities/`

Pure Pydantic models with business rules. All inherit from `DomainEntity` which provides `id`,
`created_at`, `updated_at`, `generate_id()`, and `generate_current_timestamp()`.

| Entity | Key fields / methods |
|---|---|
| `UserEntity` | name, email, hashed_password, timezone; `create_new()`, `update()` |
| `ReminderEntity` | title, description, owner_id, group_id, status (enum); `create_new()`, `update()` |
| `ReminderAssigneeEntity` | reminder_id, user_id, assigned_by, acknowledged_at, completed_at; `acknowledge()`, `complete()` |
| `NotificationEntity` | user_id, reminder_id, message, scheduled_time, sent_at, is_read_at |
| `GroupEntity` | name, description, owner_id |
| `GroupMembersEntity` | group_id, user_id, role (owner/admin/member), joined_at |
| `FriendshipEntity` | requester_id, addressee_id, status (pending/accepted/rejected/cancelled) |

Key domain enums:
- `ReminderStatus` (StrEnum): `pending`, `in_progress`, `completed`, `overdue`
- `MemberRoles` (StrEnum): `owner`, `admin`, `member`
- `FriendshipStatus` (StrEnum): `pending`, `accepted`, `rejected`, `cancelled`

### 3.4 Infrastructure Layer

**`app/models/`** — SQLAlchemy ORM models for PostgreSQL:
- `DomainSqlModel` base: all domain tables have `id (UUID PK)`, `created_at`, `updated_at`
- Tables: `users`, `reminders`, `notification_recipients`, `reminder_assignees`, `groups`,
  `group_members`, `friendships`

**`app/repos/`** — Repository pattern:
- Each repo gets a SQLAlchemy `AsyncSession`
- Repo class handles I/O; a sibling `Queries` class builds SQLAlchemy statements
- `RepoFactory` lazily instantiates all repos from a shared session

**`app/config.py`** — `pydantic-settings` `Settings` singleton. All config from environment
variables (case-insensitive). Key fields: DB credentials, Redis, JWT secrets, email credentials,
`frontend_url`.

---

## 4. Database Schema

```
users
 │
 ├──< group_members >── groups
 │                          │
 │                          └──< reminders
 │                                   │
 │                                   └──< reminder_assignees >── users
 │
 ├──< reminders (owner)
 │
 ├──< notification_recipients
 │
 └──< friendships (self-referential)
```

Key columns of note:

- `reminders.group_id` — NULL for personal reminders, FK to `groups` for group reminders
- `reminder_assignees.acknowledged_at TIMESTAMP NULL` — set when assignee acknowledges
- `reminder_assignees.completed_at TIMESTAMP NULL` — set when completed
- `notification_recipients.is_read_at TIMESTAMP NULL` — replaced old `is_read BOOLEAN`
- `notification_recipients.scheduled_time` — NULL = send immediately; non-NULL = Celery picks up

**Migrations** are managed with **Alembic** (13 versioned migration files). The migration history
covers: users → reminders → notifications → timestamps → group/assignee tables → friendships →
is_read_at/acknowledged_at.

---

## 5. Dependency Injection & Transaction Management

FastAPI's `Depends()` system is used for all cross-cutting concerns:

```python
# Two repo injection modes:
get_repo             → plain session (read-only operations)
get_shared_tx_repo   → transactional session (auto commit/rollback)

# Auth dependency:
get_current_user     → decodes JWT Bearer token → returns UserEntity

# Role guard factories (return membership entity):
require_group_member(group_id)
require_group_admin(group_id)
require_group_owner(group_id)
```

`transaction_context` is an `asynccontextmanager` that wraps `AsyncSession.begin()` — automatically
commits on success and rolls back on any exception.

---

## 6. Authentication & Security

- **JWT Bearer tokens** — access token (15 min TTL) + refresh token (7 days TTL), both HS256-signed
  with separate secret keys
- **bcrypt** password hashing via passlib
- **Callback tokens** — separate HMAC-signed JWTs (7-day TTL) embedded in email action links.
  Payload: `{sub: assignment_id, uid: user_id, act: "acknowledge"|"complete", exp: ...}`.
  Validated in the public `/reminder-assignments/callback` endpoint — no login required.

---

## 7. Notification & Email System

### Email Provider

`EmailNotificationProvider` uses Python's `smtplib` over SMTP (Gmail, TLS port 587). Supports
plain text and HTML multipart emails. A `TelegramNotificationProvider` stub exists for future
extensibility. The `NotificationProvider` abstract base class enables the Strategy pattern.

### Notification Flow

1. When a reminder is created with `notify_assignees=True` and no `assignee_scheduled_time`, an
   immediate email is sent synchronously during the HTTP request.
2. When `assignee_scheduled_time` is set, a `NotificationEntity` is persisted with `scheduled_time`
   set and `sent_at = NULL`. Celery Beat picks it up within 1 minute.

### HTML Action Emails

Every notification sent to an assignee includes two CTA buttons:
- **"✅ I've Seen This Reminder"** — links to `GET /reminder-assignments/callback?token=<ack_token>`
- **"✓ Mark As Completed"** — links to `GET /reminder-assignments/callback?token=<complete_token>`

When clicked, the backend:
1. Decodes and validates the signed token
2. Checks idempotency (already done → redirects with `?status=already_done`)
3. Updates `acknowledged_at` and/or `completed_at` on the assignment
4. Stamps `is_read_at` on all unread notifications for that user + reminder
5. Sends a plain email notification back to the assigner
6. Redirects to `{frontend_url}/reminder-callback?status=success&action=...`

### Celery Background Task

- **Celery Beat** runs `send_scheduled_notifications` every minute (`crontab(minute='*')`)
- Task queries `notification_recipients` where `scheduled_time <= now AND sent_at IS NULL`
- For each due notification: looks up user, reminder, and assignment
- If assignment found → HTML email with action buttons; otherwise → plain text email
- Marks `sent_at` on success

---

## 8. Role-Based Access Control

### Group Roles

Three roles: `owner > admin > member`

| Action | Required Role |
|---|---|
| Create/delete group | Owner |
| Update group, add/remove members, assign reminders | Admin or Owner |
| View group and reminders | Any member |
| Edit reminder (all fields) | Admin, Owner, or reminder creator |
| Edit reminder (status only) | Any assignee |
| Delete reminder | Admin, Owner, or reminder creator |
| Self-assign reminder | Admin or Owner |

### Friend-based Reminders

Personal reminders can only be assigned to users who are accepted friends.

---

## 9. Complete API Endpoint Reference

### Users (`/`)
| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/signup` | — | Register a new user (name, email, password, timezone) |
| POST | `/login` | — | Authenticate; returns access + refresh JWT tokens |
| GET | `/user` | ✓ | Get authenticated user's profile |
| PATCH | `/user/profile` | ✓ | Update name, timezone, or password |

### Reminders (`/reminders`)
| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/reminders` | ✓ | Create reminder (optional group_id, assignee_ids, notify_assignees) |
| POST | `/reminders/search` | ✓ | List reminders with filters (status, include_assigned) |
| PATCH | `/reminders/{id}` | ✓ | Update reminder fields |
| DELETE | `/reminders/{id}` | ✓ | Delete reminder |

### Groups (`/groups`)
| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/groups` | ✓ | Create group; creator becomes owner |
| GET | `/groups` | ✓ | List all groups the caller belongs to |
| GET | `/groups/{id}` | ✓ | Get group details (member only) |
| PATCH | `/groups/{id}` | ✓ Admin | Update group name/description |
| DELETE | `/groups/{id}` | ✓ Owner | Delete group |
| GET | `/groups/{id}/reminders` | ✓ Member | List all group reminders |
| GET | `/groups/{id}/members/search` | ✓ Member | ilike user search, excludes existing members |
| GET | `/groups/{id}/members` | ✓ Member | List all members with roles |
| POST | `/groups/{id}/members` | ✓ Admin | Add member by email |
| POST | `/groups/{id}/members/invite` | ✓ Admin | Email invite to non-registered user |
| PATCH | `/groups/{id}/members/{uid}` | ✓ Admin | Change member role |
| DELETE | `/groups/{id}/members/{uid}` | ✓ Admin | Remove member |

### Group Reminders (collaborative)
| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/reminders/{id}/assign` | ✓ Admin | Assign group member to reminder |
| POST | `/reminders/{id}/assign-to-me` | ✓ Admin | Self-assign reminder |
| POST | `/reminders/{id}/notify` | ✓ Member | Notify current assignees |
| POST | `/reminders/{id}/notify-all` | ✓ Admin | Notify all group members |
| PATCH | `/reminders/{id}/group-update` | ✓ Member | Role-gated update with assignee sync |

### Reminder Assignments
| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/reminder-assignments/callback` | — (token) | Email callback: acknowledge or complete via signed token |
| GET | `/reminders/{id}/assignees` | ✓ | List all assignees for a reminder |
| POST | `/reminders/{id}/assignees` | ✓ | Add assignee to reminder |
| POST | `/reminder-assignments/{id}/acknowledge` | ✓ | Acknowledge assignment (seen → in_progress) |
| POST | `/reminder-assignments/{id}/complete` | ✓ | Mark assignment completed |
| PATCH | `/reminder-assignments/{id}` | ✓ | Toggle completed flag |
| DELETE | `/reminder-assignments/{id}` | ✓ Admin/Owner | Remove assignment |

### Friends
| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/users/search` | ✓ | Search users by name/email (ilike, paginated) |
| POST | `/friends/requests` | ✓ | Send friend request |
| GET | `/friends/requests/incoming` | ✓ | List pending incoming requests |
| GET | `/friends/requests/outgoing` | ✓ | List pending outgoing requests |
| PATCH | `/friends/requests/{id}` | ✓ | Accept or reject request |
| DELETE | `/friends/requests/{id}` | ✓ | Cancel outgoing request |
| GET | `/friends` | ✓ | List all accepted friends |
| DELETE | `/friends/{uid}` | ✓ | Unfriend a user |

### System
| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/health` | — | Health check (204) |
| GET | `/version` | — | App version |
| GET | `/actuator/info` | — | App name + version JSON |

---

## 10. Frontend Architecture

### Folder Structure

```
frontend/src/
  api/           — Axios API clients (auth.ts, reminders.ts, groups.ts, friends.ts, client.ts)
  context/       — Zustand auth store (token + user persistence)
  hooks/         — Custom hooks (useDarkMode)
  pages/         — Full-page React components
  components/    — Shared components (Navbar, ReminderCard, ReminderModal, ProtectedRoute, LoadingSpinner)
  types/         — TypeScript interfaces matching backend response schemas
```

### Pages

| Page | Purpose |
|---|---|
| `Login.tsx` | JWT login form with error display |
| `Register.tsx` | User signup with timezone selection |
| `Dashboard.tsx` | Personal reminders — create, edit, delete, filter by status |
| `Groups.tsx` | List all groups, create new group |
| `GroupDetail.tsx` | Full group page: member management, Jira-style reminder board, inline forms, assignee checkboxes, role-gated actions, email invite with non-registered user detection |
| `Friends.tsx` | Friend search, send/accept/reject requests, friend list |
| `Profile.tsx` | Update name, timezone, password |
| `ReminderCallback.tsx` | Public page for email callback links — shows success/already-done/error state with auto-redirect countdown (8s) |

### State Management

- **Zustand** `useAuthStore` — JWT token persistence in localStorage, user object, login/logout
- Local `useState` for per-page data (reminders, members, etc.)
- `axios` interceptor automatically attaches `Authorization: Bearer <token>` to all requests

### Routing

React Router DOM v7. Public routes: `/login`, `/register`, `/reminder-callback`. All other routes
are wrapped in `<ProtectedRoute>` which redirects unauthenticated users to `/login`.

### Dark Mode

`useDarkMode` hook reads system preference (`prefers-color-scheme`). All pages use computed color
variables applied via inline `style` props for precise theme control.

---

## 11. Full Folder Structure

```
capstone/
├── app/
│   ├── api/                    # FastAPI routers (presentation layer)
│   │   ├── debug.py
│   │   ├── friends.py
│   │   ├── group_reminders.py
│   │   ├── groups.py
│   │   ├── reminder_assignees.py
│   │   ├── reminders.py
│   │   ├── root.py
│   │   └── users.py
│   ├── db/                     # Async PostgreSQL pool, transaction context
│   │   ├── async_pgsql_pool.py
│   │   └── transaction_context.py
│   ├── entities/               # Domain entities (Pydantic + business logic)
│   │   ├── domain_entity.py
│   │   ├── friendship.py
│   │   ├── group.py
│   │   ├── group_members.py
│   │   ├── notification.py
│   │   ├── reminder.py
│   │   ├── reminder_assignee.py
│   │   └── user.py
│   ├── middlewares/            # Logging middleware (request/response timing)
│   ├── models/                 # SQLAlchemy ORM models
│   │   ├── base.py
│   │   ├── friendships.py
│   │   ├── group_members.py
│   │   ├── groups.py
│   │   ├── notification_recipients.py
│   │   ├── reminder.py
│   │   ├── reminder_assignees.py
│   │   └── users.py
│   ├── repos/                  # Repository classes + query builders + RepoFactory
│   │   ├── __init__.py         # RepoFactory
│   │   ├── friendship_pgsql_repo.py
│   │   ├── group_member_pgsql_repo.py
│   │   ├── group_pgsql_repo.py
│   │   ├── notifications_pgsql_repo.py
│   │   ├── reminder_assignee_pgsql_repo.py
│   │   ├── reminder_pgsql_repo.py
│   │   └── user_pgsql_repo.py
│   ├── schemas/                # HTTP request/response Pydantic schemas
│   │   ├── base_schemas.py
│   │   ├── friendship_schemas.py
│   │   ├── group_schemas.py
│   │   ├── reminder_schemas.py
│   │   └── user_schemas.py
│   ├── services/               # Application / business logic
│   │   ├── app_service.py
│   │   ├── friendship_service.py
│   │   ├── group_reminder_service.py
│   │   ├── group_service.py
│   │   ├── notification_providers.py
│   │   ├── notifications_service.py
│   │   ├── reminder_service.py
│   │   └── user_service.py
│   ├── structs/                # Internal data structures (error messages, pagination)
│   ├── utils/                  # Shared utilities
│   │   ├── __init__.py         # JWT helpers, password hashing, timezone conversion
│   │   └── callback_tokens.py  # Signed JWT tokens for email action links
│   ├── celery_app.py           # Celery + Beat configuration
│   ├── config.py               # pydantic-settings global Settings singleton
│   ├── dependencies.py         # FastAPI dependency functions
│   ├── exceptions.py           # Domain exception hierarchy
│   ├── main.py                 # FastAPI app factory, Uvicorn server factory, CLI
│   └── tasks.py                # Celery tasks (scheduled/immediate notifications)
├── frontend/
│   ├── src/
│   │   ├── api/                # Axios API modules per domain
│   │   ├── components/         # Shared React components
│   │   ├── context/            # Zustand stores
│   │   ├── hooks/              # Custom React hooks
│   │   ├── pages/              # Page-level components
│   │   └── types/              # TypeScript type definitions
│   ├── index.html
│   ├── package.json
│   ├── tailwind.config.js
│   └── vite.config.ts
├── migrations/
│   └── versions/               # 13 Alembic migration files
├── docker-compose.yml          # 6 services orchestration
├── Makefile                    # dev, front, celery-worker, celery-beat, fmt, test
├── pyproject.toml              # uv/pip dependencies, Ruff config, mypy config
└── ARCHITECTURE.md             # This file
```

---

## 12. Key Design Patterns

| Pattern | Where Used |
|---|---|
| **Factory pattern** | `RepoFactory`, `FastApiAbstractFactory`, `UvicornFactory` |
| **Repository pattern** | `*PgsqlRepo` classes isolate all DB access from business logic |
| **Dependency Injection** | FastAPI `Depends()` for sessions, auth, repos, role guards |
| **Entity pattern** | Pydantic domain entities with `create_new()` factory methods and `update()` |
| **Strategy pattern** | `NotificationProvider` ABC with email and Telegram implementations |
| **Transaction context manager** | `transaction_context()` — ACID commit/rollback wrapping request handlers |
| **Clean Architecture (4 layers)** | Strict: API → Service → Entity ← Repo → Model |
| **CQRS-lite** | Query classes separated from repo classes (e.g. `ReminderPgsqlQueries`) |
| **Token-based callback security** | Signed JWTs in email links for stateless actions without login |
| **Idempotent design** | Email callback links check existing state; redirect gracefully if already processed |

---

## 13. Infrastructure & DevOps

Docker Compose orchestrates 6 services on a shared `capstone_net` bridge network:

| Service | Image / Build | Port |
|---|---|---|
| `app_capstone` | Custom Python image (dev.Dockerfile) | 8000 |
| `celery_worker` | Same image, runs `celery worker` | — |
| `celery_beat` | Same image, runs `celery beat` | — |
| `frontend` | Node image, Vite dev server | 5173 |
| `postgres_capstone` | `postgres:17` with health check | 5432 |
| `redis_capstone` | `redis:7-alpine` with AOF persistence | 6379 |

Health checks ensure the app and Celery only start after Postgres and Redis are ready.
Secrets (JWT keys, email credentials) are injected via environment variables.

Local development commands (via `make`):

```bash
make dev            # Run FastAPI dev server with hot-reload
make front          # Run Vite frontend dev server
make celery-worker  # Run Celery worker
make celery-beat    # Run Celery beat scheduler
make fmt            # ruff format + ruff check --fix + mypy + ruff check
```

Database migrations:

```bash
uv run alembic upgrade head                                    # Apply all migrations
uv run alembic revision --autogenerate -m "description"        # Generate new migration
```

---

## 14. Code Quality & Standards

- **Ruff** — linting + formatting (line-length 120, single quotes, Google-style docstrings,
  30+ rule categories: annotations, async, bugbear, pydocstyle, type checks, security, etc.)
- **mypy** — static type checking (non-strict mode, Python 3.14 target, covers `app/` package)
- **Strict method naming conventions** enforced per layer (see Section 3.2)
- All domain exceptions inherit from `DomainError` and are handled globally by a FastAPI exception
  handler, returning structured `{"detail": "..."}` JSON responses with correct HTTP status codes
- The `BaseSchema` Pydantic base class is frozen by default (immutable request/response schemas)

