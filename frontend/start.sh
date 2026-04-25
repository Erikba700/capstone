#!/bin/bash

echo "Starting Reminder App Frontend..."
echo "================================="
echo ""
echo "Prerequisites:"
echo "1. Backend API must be running on http://localhost:8000"
echo "2. Database must be set up and migrations run"
echo ""
echo "Starting development server..."
echo ""

cd "$(dirname "$0")"
npm run dev

