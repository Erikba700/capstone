#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}   Reminder App - Quick Start Check${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check Node.js
echo -e "${YELLOW}Checking Node.js...${NC}"
if command -v node &> /dev/null; then
    NODE_VERSION=$(node -v)
    echo -e "${GREEN}✓ Node.js installed: $NODE_VERSION${NC}"
else
    echo -e "❌ Node.js not found. Please install Node.js 18+"
    exit 1
fi

# Check npm
echo -e "${YELLOW}Checking npm...${NC}"
if command -v npm &> /dev/null; then
    NPM_VERSION=$(npm -v)
    echo -e "${GREEN}✓ npm installed: $NPM_VERSION${NC}"
else
    echo -e "❌ npm not found."
    exit 1
fi

echo ""
echo -e "${YELLOW}Checking project structure...${NC}"

# Check key files exist
FILES=(
    "package.json"
    "src/App.tsx"
    "src/main.tsx"
    "src/index.css"
    "src/api/client.ts"
    "src/api/auth.ts"
    "src/api/reminders.ts"
    "src/components/Navbar.tsx"
    "src/components/ProtectedRoute.tsx"
    "src/components/ReminderCard.tsx"
    "src/components/ReminderModal.tsx"
    "src/components/LoadingSpinner.tsx"
    "src/pages/Login.tsx"
    "src/pages/Register.tsx"
    "src/pages/Dashboard.tsx"
    "src/context/store.ts"
    "src/types/index.ts"
    "tailwind.config.js"
    ".env"
)

MISSING=0
for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✓${NC} $file"
    else
        echo -e "❌ $file (missing)"
        MISSING=$((MISSING + 1))
    fi
done

echo ""

if [ $MISSING -eq 0 ]; then
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}✓ All files present!${NC}"
    echo -e "${GREEN}========================================${NC}"
else
    echo -e "❌ $MISSING file(s) missing"
    exit 1
fi

echo ""
echo -e "${YELLOW}Checking dependencies...${NC}"

if [ -d "node_modules" ]; then
    echo -e "${GREEN}✓ node_modules exists${NC}"
else
    echo -e "${YELLOW}⚠ node_modules not found. Run: npm install${NC}"
fi

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}   Ready to Start!${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo ""
echo -e "1. Make sure backend is running:"
echo -e "   ${GREEN}cd /Users/erikbadalyan/PycharmProjects/capstone${NC}"
echo -e "   ${GREEN}make dev${NC}"
echo ""
echo -e "2. Start frontend (in this directory):"
echo -e "   ${GREEN}npm run dev${NC}"
echo ""
echo -e "3. Open browser:"
echo -e "   ${GREEN}http://localhost:5173${NC}"
echo ""
echo -e "${BLUE}========================================${NC}"

