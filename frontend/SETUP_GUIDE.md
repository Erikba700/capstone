# Frontend Setup and Running Guide

## Quick Start

### 1. Start Backend API First
```bash
cd /Users/erikbadalyan/PycharmProjects/capstone
make dev
```

The backend will run on `http://localhost:8000`

### 2. Start Frontend
```bash
cd /Users/erikbadalyan/PycharmProjects/capstone/frontend
npm install  # if not already done
npm run dev
```

The frontend will run on `http://localhost:5173`

### 3. Open in Browser
Navigate to: `http://localhost:5173`

---

## Features Implemented

### Pages
1. **Login** (`/login`) - User authentication
2. **Register** (`/register`) - New user registration
3. **Dashboard** (`/`) - Main reminders management (protected route)

### Functionality
- ✅ User registration with validation
- ✅ User login with JWT tokens
- ✅ Protected routes (redirect to login if not authenticated)
- ✅ Create new reminders
- ✅ View all reminders
- ✅ Filter reminders (All / Upcoming / Completed)
- ✅ Edit existing reminders
- ✅ Mark reminders as complete/incomplete
- ✅ Delete reminders
- ✅ Dark mode toggle
- ✅ Responsive design
- ✅ Toast notifications for user feedback
- ✅ Loading states
- ✅ Error handling

---

## Tech Stack

- **React 18** with TypeScript
- **Vite** for fast builds and HMR
- **TailwindCSS** for styling
- **Zustand** for state management
- **React Router** for navigation
- **Axios** for API calls
- **React Toastify** for notifications
- **date-fns** for date formatting

---

## Project Structure

```
frontend/
├── src/
│   ├── api/                    # API clients
│   │   ├── client.ts           # Axios instance with interceptors
│   │   ├── auth.ts             # Auth API calls
│   │   └── reminders.ts        # Reminders API calls
│   ├── components/             # Reusable components
│   │   ├── LoadingSpinner.tsx
│   │   ├── Navbar.tsx
│   │   ├── ProtectedRoute.tsx
│   │   ├── ReminderCard.tsx
│   │   └── ReminderModal.tsx
│   ├── pages/                  # Page components
│   │   ├── Login.tsx
│   │   ├── Register.tsx
│   │   └── Dashboard.tsx
│   ├── context/                # State management
│   │   └── store.ts            # Zustand stores
│   ├── types/                  # TypeScript types
│   │   └── index.ts
│   ├── App.tsx                 # Main app with routing
│   ├── main.tsx                # Entry point
│   └── index.css               # Global TailwindCSS styles
├── .env                        # Environment variables
├── tailwind.config.js
├── postcss.config.js
├── vite.config.ts
└── package.json
```

---

## API Integration

The frontend connects to these backend endpoints:

### Authentication
- `POST /api/signup` - Register new user
- `POST /api/login` - Login user (returns JWT tokens)
- `GET /api/user` - Get current authenticated user

### Reminders
- `POST /api/reminders` - Create new reminder
- `POST /api/reminders/search` - Get reminders with filters
- `PATCH /api/reminders/{id}` - Update reminder
- `DELETE /api/reminders/{id}` - Delete reminder

---

## State Management

### Auth Store (`useAuthStore`)
- `user`: Current user object
- `isAuthenticated`: Boolean flag
- `isLoading`: Loading state
- `login()`: Login and store tokens
- `logout()`: Clear tokens and user
- `loadUser()`: Fetch current user from API

### Reminders Store (`useRemindersStore`)
- `reminders`: Array of reminders
- `isLoading`: Loading state
- `error`: Error message
- `fetchReminders()`: Get all reminders
- `createReminder()`: Create new reminder
- `updateReminder()`: Update existing reminder
- `deleteReminder()`: Delete reminder

---

## Styling

The app uses TailwindCSS with custom utility classes:

- `.btn-primary` - Primary blue button
- `.btn-secondary` - Secondary gray button
- `.btn-danger` - Red danger button
- `.input-field` - Styled input field
- `.card` - Card container with shadow

Dark mode is supported via Tailwind's `dark:` prefix and toggled by adding/removing the `dark` class to the `<html>` element.

---

## Testing the App

### 1. Register a New User
1. Go to `http://localhost:5173/register`
2. Fill in name, email, and password
3. Click "Sign Up"
4. You'll be redirected to login

### 2. Login
1. Go to `http://localhost:5173/login`
2. Enter email and password
3. Click "Sign In"
4. You'll be redirected to the dashboard

### 3. Create Reminders
1. On the dashboard, click "+ New Reminder"
2. Fill in title and optional description
3. Click "Create"
4. The reminder appears in the list

### 4. Manage Reminders
- **Mark as complete**: Click the checkbox
- **Edit**: Click "Edit" button
- **Delete**: Click "Delete" button (with confirmation)
- **Filter**: Use tabs (All / Upcoming / Completed)

### 5. Dark Mode
Click the sun/moon icon in the navbar to toggle dark mode

---

## Troubleshooting

### Port 5173 already in use
```bash
# Kill the process using port 5173
lsof -ti:5173 | xargs kill -9
```

### Backend not connecting
- Ensure backend is running on `http://localhost:8000`
- Check CORS settings in backend (`app/main.py`)
- Verify `.env` file has correct API URL

### Build errors
```bash
# Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
```

---

## Production Build

```bash
npm run build
```

This creates an optimized production build in the `dist/` directory.

To preview the production build:
```bash
npm run preview
```

---

## Environment Variables

File: `.env`

```env
VITE_API_BASE_URL=http://localhost:8000/api
```

For production, update this to your production API URL.

---

## Next Steps / Future Enhancements

- [ ] Add notification polling (every 30 seconds)
- [ ] Add notification page/component
- [ ] Add due dates/times for reminders
- [ ] Add reminder categories/tags
- [ ] Add search functionality
- [ ] Add sorting options
- [ ] Add pagination for large lists
- [ ] Add user profile page
- [ ] Add password reset functionality
- [ ] Add email verification
- [ ] Add reminder sharing between users
- [ ] Add reminder priority levels
- [ ] Add bulk operations
- [ ] Add export/import reminders
- [ ] Add keyboard shortcuts
- [ ] Add animations and transitions
- [ ] Add PWA support
- [ ] Add offline mode

---

## License

MIT

