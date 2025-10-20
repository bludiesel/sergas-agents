#!/bin/bash
# Stop all services

echo "🛑 Stopping Sergas Account Manager services..."

# Kill by PID files if they exist
if [ -f ".backend.pid" ]; then
    BACKEND_PID=$(cat .backend.pid)
    echo "   Stopping backend (PID: $BACKEND_PID)..."
    kill $BACKEND_PID 2>/dev/null && echo "   ✅ Backend stopped" || echo "   ⚠️  Backend already stopped"
    rm .backend.pid
fi

if [ -f ".frontend.pid" ]; then
    FRONTEND_PID=$(cat .frontend.pid)
    echo "   Stopping frontend (PID: $FRONTEND_PID)..."
    kill $FRONTEND_PID 2>/dev/null && echo "   ✅ Frontend stopped" || echo "   ⚠️  Frontend already stopped"
    rm .frontend.pid
fi

# Also kill by port (backup method)
echo "   Checking ports..."
lsof -ti:8008 | xargs kill -9 2>/dev/null && echo "   ✅ Port 8008 freed" || true
lsof -ti:7007 | xargs kill -9 2>/dev/null && echo "   ✅ Port 7007 freed" || true

# Clean up log files
if [ -f "backend.log" ]; then
    echo "   Archived backend.log → backend.log.old"
    mv backend.log backend.log.old
fi

if [ -f "frontend.log" ]; then
    echo "   Archived frontend.log → frontend.log.old"
    mv frontend.log frontend.log.old
fi

echo ""
echo "✅ All services stopped"
echo ""
echo "To restart: ./scripts/start_all.sh"
