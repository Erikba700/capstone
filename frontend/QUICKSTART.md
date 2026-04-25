# 🚀 Quick Start Guide

## Prerequisites

✅ Node.js 18+ installed  
✅ Backend API running on `http://localhost:8000`  
✅ Database migrations completed

---

## Installation (One-Time Setup)

```bash
cd /Users/erikbadalyan/PycharmProjects/capstone/frontend
npm install
```

---

## Running the Application

### Option 1: Using npm (Recommended)

```bash
# In the frontend directory
npm run dev
```

### Option 2: Using the start script

```bash
./start.sh
```

### Option 3: Check setup first

```bash
./check-setup.sh  # Verify everything is set up
npm run dev       # Then start
```

The app will be available at: **http://localhost:5173**

---

## First Time Usage

### 1. Register a New User
- Go to http://localhost:5173/register
- Fill in:
  - Name: `Your Name`
  - Email: `your@email.com`
  - Password: `yourpassword`
- Click **Sign Up**

### 2. Login
- You'll be redirected to login
- Enter your email and password
- Click **Sign In**

### 3. Create Your First Reminder
- Click **+ New Reminder** button
- Enter:
  - Title: `My First Reminder`
  - Description: `This is a test` (optional)
- Click **Create**

### 4. Explore Features
- ✅ Mark reminders as complete (checkbox)
- ✏️ Edit reminders (Edit button)
- 🗑️ Delete reminders (Delete button)
- 🔍 Filter: All / Upcoming / Completed
- 🌙 Toggle dark mode (sun/moon icon)

---

## Troubleshooting

### ❌ "Cannot connect to server"

**Problem**: Backend not running

**Solution**:
```bash
cd /Users/erikbadalyan/PycharmProjects/capstone
make dev
```

### ❌ "Port 5173 already in use"

**Problem**: Another process using the port

**Solution**:
```bash
lsof -ti:5173 | xargs kill -9
npm run dev
```

### ❌ "Module not found" errors

**Problem**: Dependencies not installed

**Solution**:
```bash
rm -rf node_modules package-lock.json
npm install
```

### ❌ CORS errors

**Problem**: Backend CORS not configured

**Solution**: Already fixed in `app/main.py` - just restart backend

---

## Development

### Available Scripts

```bash
npm run dev      # Start development server
npm run build    # Build for production
npm run preview  # Preview production build
npm run lint     # Run ESLint
```

### Project Structure

```
frontend/
├── src/
│   ├── api/           # API client & endpoints
│   ├── components/    # Reusable components
│   ├── pages/         # Page components
│   ├── context/       # State management
│   ├── types/         # TypeScript types
│   ├── App.tsx        # Main app
│   └── main.tsx       # Entry point
├── public/            # Static assets
├── .env               # Environment variables
└── package.json       # Dependencies
```

---

## Environment Variables

File: `.env`

```env
VITE_API_BASE_URL=http://localhost:8000/api
```

Change this for production deployment.

---

## Documentation

- **SETUP_GUIDE.md** - Detailed setup instructions
- **IMPLEMENTATION_SUMMARY.md** - Complete feature list
- **README.md** - Project overview

---

## Tech Stack

- React 18 + TypeScript
- Vite (build tool)
- TailwindCSS (styling)
- Zustand (state management)
- React Router (routing)
- Axios (API calls)
- React Toastify (notifications)

---

## API Endpoints

All endpoints are under `/api`:

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/signup` | Register user |
| POST | `/login` | Login user |
| GET | `/user` | Get current user |
| POST | `/reminders` | Create reminder |
| POST | `/reminders/search` | List reminders |
| PATCH | `/reminders/{id}` | Update reminder |
| DELETE | `/reminders/{id}` | Delete reminder |

---

## Support

If you encounter issues:

1. Check that backend is running
2. Verify `.env` file exists and is correct
3. Clear browser cache
4. Check browser console for errors
5. Restart both frontend and backend

---

## Production Build

```bash
npm run build
```

Creates optimized build in `dist/` directory.

To test production build:
```bash
npm run preview
```

---

**Happy coding! 🎉**

