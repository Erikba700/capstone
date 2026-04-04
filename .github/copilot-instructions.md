# Copilot Instructions — capstone Backend

## Commands

```shell
# project dependencies
uv add ...

# Run the app locally
make dev

# Alembic migrations
uv run alembic -c migrations/alembic_migrations/alembic.ini upgrade head
uv run alembic -c migrations/alembic_migrations/alembic.ini revision --autogenerate -m "description"
```

### Four-layer structure

| Layer | Location | Responsibility |
|---|---|---|
| **Presentation** | `app/api/` | FastAPI routers, HTTP request/response handling |
| **Application** | `app/services/`, `app/schemas/` | Business logic orchestration, request/response validation |
| **Domain** | `app/entities/` | Core domain objects with business rules |
| **Infrastructure** | `app/db/`, `app/repos/`, `app/models/`, `app/rest/`, `app/config.py` | Database access, external API clients, configuration |

### Data flow

```
HTTP Request → Schema (validation) → Service (orchestration) → Repo → Model → Database
HTTP Response ← Schema (serialization) ← Service ← Entity ← Repo
```

### Four types of Pydantic models

- **Entities** (`app/entities/`): Domain objects with business logic (e.g., `ProtocolEntity.create_new()`). Inherit from `DomainEntity` which has `id`, `created_at`, `updated_at`.
- **Models** (`app/models/`): SQLAlchemy ORM models for PostgreSQL. Inherit from `DomainSqlModel` (domain tables) or `SqlModel` (association tables).
- **Schemas** (`app/schemas/`): HTTP request/response validation. Naming: `{Entity}CreateRequestSchema`, `{Entity}UpdateRequestSchema`, `{Entity}ResponseSchema`. Inherit from `BaseSchema` (frozen by default).
- **Structs** (`app/structs/`): Internal data structures not tied to HTTP or DB (e.g., `PaginationParams`, `ErrorMessage`).

### Dependency injection

Two factory classes provide dependencies to route handlers:

- **`RepoFactory`** (`app/repos/__init__.py`): Creates repo instances for both PostgreSQL and Neo4j. Injected via `get_repos` or `get_shared_tx_repos` (transactional, auto-commits/rolls-back both DBs).
- **`ClientFactory`** (`app/rest/__init__.py`): Creates HTTP client instances (Graph API, S3, NICE, Cerberus, LDT).

Services are instantiated per-request inside route handlers, receiving `RepoFactory` and `ClientFactory`.

### Repo pattern

Each repo gets a database session and a separate **queries class** that builds SQLAlchemy statements. This separation makes query logic independently testable.

```python
class ProtocolPgsqlRepo:
    def __init__(self, session, queries=ProtocolPgsqlQueries): ...

class ProtocolPgsqlQueries:
    @staticmethod
    def insert_protocol_query(data: dict) -> ReturningInsert: ...
```

### Router registration

Two tiers in `app/main.py`:
- `api_router`: Public routes (health check, auth) — no authentication
- `api_v1_router`: Protected routes under `/v1` — requires `HTTPBearer` + `get_authenticated_user`

## Conventions

### Method naming by layer

| Layer | Create | Read | Update | Delete |
|---|---|---|---|---|
| Infrastructure (repos) | `insert` | `find`, `list` | `update` | `delete` |
| Domain (entities) | `create` | `find` | `update` | `remove` |
| Application (services) | `create` | `fetch`, `view` | `update` | `remove` |
| Presentation (API) | `post` | `get` | `put`/`patch` | `delete` |

### Code style

- **Ruff** for linting and formatting (line length 79, single quotes, Google-style docstrings)
- **mypy** for type checking (strict mode off, Python 3.14)
- All ruff rules are explicitly configured in `pyproject.toml` under `[tool.ruff.lint]`
- Tests are exempt from return-type annotations, `assert` warnings, and docstring requirements

### Tests

- No tests being used


### Configuration

All settings via environment variables (case-insensitive), read once at startup into a global `Settings` singleton (`app/config.py`).

### Database models diagram

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
 ├──< notifications
 │
 └──< devices