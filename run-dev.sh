#!/bin/bash
echo "🏠 Starting Home Broker Trading Simulator in Development Mode"
echo "============================================================"

# Function to cleanup background processes
cleanup() {
    echo "Stopping servers..."
    kill $(jobs -p) 2>/dev/null
    exit
}

# Trap Ctrl+C
trap cleanup INT

# Start backend in background
echo "🚀 Starting backend server..."
cd backend && python3 main.py &
BACKEND_PID=$!

# Wait a bit for backend to start
sleep 3

# Start frontend in background
echo "🚀 Starting frontend server..."
cd frontend && npm start &
FRONTEND_PID=$!

# Wait for both processes
wait
