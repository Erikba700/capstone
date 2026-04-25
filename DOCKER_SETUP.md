# 🐳 Docker Compose Setup Guide

## What Was Added

The frontend service has been added to `docker-compose.yml` so you can run the **entire application** (backend + frontend + database) with a single command!

---

## 🚀 Quick Start

### Start Everything
```bash
cd /Users/erikbadalyan/PycharmProjects/capstone
docker compose up
```

### Stop Everything
```bash
docker compose down
```

### Rebuild After Changes
```bash
docker compose up --build
```

---

## 📦 Services Included

### 1. **postgres_capstone**
- PostgreSQL 17 database
- Port: `5432`
- Healthcheck enabled

### 2. **app_capstone** (Backend)
- FastAPI backend
- Port: `8000`
- URL: http://localhost:8000
- API Docs: http://localhost:8000/docs

### 3. **frontend** (NEW! ✨)
- React + Vite frontend
- Port: `5173`
- URL: http://localhost:5173
- Hot reload enabled

---

## 🎯 Access Points

After running `docker compose up`:

| Service | URL | Description |
|---------|-----|-------------|
| **Frontend** | http://localhost:5173 | Main app UI |
| **Backend API** | http://localhost:8000 | API endpoints |
| **API Docs** | http://localhost:8000/docs | Swagger UI |
| **Database** | localhost:5432 | PostgreSQL |

---

## 📁 Files Created

### 1. `frontend/Dockerfile`
```dockerfile
FROM node:20-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
```

### 2. `frontend/.dockerignore`
Excludes:
- node_modules
- dist
- logs
- coverage

### 3. Updated `docker-compose.yml`
Added frontend service with:
- Volume mounting for hot reload
- Node modules caching
- Environment variables
- Dependency on backend

---

## 🔧 Frontend Service Configuration

```yaml
frontend:
  build:
    context: ./frontend
    dockerfile: Dockerfile
  ports:
    - '5173:5173'
  networks:
    - mp_net
  volumes:
    - ./frontend:/app:rw           # Hot reload
    - /app/node_modules             # Cache node_modules
  environment:
    - VITE_API_BASE_URL=http://localhost:8000/api
  depends_on:
    - app_capstone
  stdin_open: true
  tty: true
```

### Key Features:
- ✅ **Hot reload** - Changes auto-reload
- ✅ **Volume mounting** - Live code updates
- ✅ **Node modules cached** - Fast rebuilds
- ✅ **Waits for backend** - Starts after backend is ready

---

## 📋 Running the Application

### Full Stack (Recommended)
```bash
# Start all services
docker compose up

# Or run in background
docker compose up -d

# View logs
docker compose logs -f

# View frontend logs only
docker compose logs -f frontend
```

### Stop Services
```bash
# Stop all
docker compose down

# Stop and remove volumes (fresh start)
docker compose down -v
```

### Rebuild After Changes
```bash
# Rebuild all
docker compose up --build

# Rebuild specific service
docker compose up --build frontend
```

---

## 🧪 Testing

### 1. Start Services
```bash
docker compose up
```

Wait for output:
```
postgres_capstone | database system is ready to accept connections
app_capstone      | INFO:     Application startup complete
frontend          | ➜  Local:   http://localhost:5173/
```

### 2. Open Browser
http://localhost:5173

### 3. Use the App
- Register a new user
- Login
- Create reminders
- Toggle dark mode 🌙
- Everything works!

---

## 🔍 Troubleshooting

### Port Already in Use
```bash
# Kill processes on ports
lsof -ti:5173 | xargs kill -9
lsof -ti:8000 | xargs kill -9
lsof -ti:5432 | xargs kill -9

# Or use different ports in docker-compose.yml
```

### Frontend Not Loading
```bash
# Check logs
docker compose logs frontend

# Rebuild
docker compose up --build frontend
```

### Database Issues
```bash
# Reset database
docker compose down -v
docker compose up
```

### CORS Errors
Backend CORS is already configured to allow `localhost:5173`

---

## 🔄 Development Workflow

### With Docker (Full Stack)
```bash
docker compose up
```
- ✅ Everything runs together
- ✅ No need to manage multiple terminals
- ✅ Consistent environment
- ✅ Easy to share with team

### Without Docker (Manual)
```bash
# Terminal 1: Backend
make dev

# Terminal 2: Frontend
cd frontend && npm run dev
```

---

## 📝 Environment Variables

### Frontend (.env)
```env
VITE_API_BASE_URL=http://localhost:8000/api
```

### Backend (docker-compose.yml)
```yaml
environment:
  PGSQL_HOST: postgres_capstone
  PGSQL_PORT: 5432
  PGSQL_USER: postgres
  PGSQL_PASSWORD: postgres
  PGSQL_DB_NAME: postgres_capstone
```

---

## 🎯 Production Deployment

For production, you'll want to:

### 1. Build Frontend for Production
```bash
cd frontend
npm run build
```
This creates optimized files in `dist/`

### 2. Serve Static Files
Use nginx or another web server to serve the `dist/` folder

### 3. Update Environment
Change `VITE_API_BASE_URL` to your production API URL

---

## ✅ Benefits of Docker Setup

✅ **One command** - Start everything with `docker compose up`  
✅ **Consistent** - Same environment everywhere  
✅ **Isolated** - Services in containers  
✅ **Hot reload** - Frontend auto-updates on code changes  
✅ **Easy cleanup** - `docker compose down`  
✅ **Team friendly** - Everyone gets same setup  

---

## 📊 Service Dependencies

```
postgres_capstone (starts first)
       ↓
app_capstone (waits for postgres health check)
       ↓
frontend (waits for backend)
```

This ensures services start in the correct order!

---

## 🎊 Complete!

Your docker-compose.yml now includes:
- ✅ PostgreSQL database
- ✅ FastAPI backend
- ✅ React frontend (NEW!)
- ✅ Networking configured
- ✅ Volume mounting for hot reload
- ✅ Health checks
- ✅ Proper dependencies

**Run with**: `docker compose up`

**Access at**: http://localhost:5173

---

## Quick Commands Reference

```bash
# Start all services
docker compose up

# Start in background
docker compose up -d

# Stop all
docker compose down

# View logs
docker compose logs -f

# Rebuild
docker compose up --build

# Fresh start (remove volumes)
docker compose down -v && docker compose up

# Restart specific service
docker compose restart frontend
```

---

**Status**: ✅ COMPLETE - Frontend added to Docker Compose!

