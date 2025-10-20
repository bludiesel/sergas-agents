#!/bin/bash
# Quick start script - Launches both backend and frontend

set -e

echo "🚀 Sergas Account Manager - Quick Start"
echo "========================================"
echo ""

# Check if we're in the right directory
if [ ! -f "src/main.py" ]; then
    echo "❌ Error: Must run from project root"
    echo "Run: cd /Users/mohammadabdelrahman/Projects/sergas_agents"
    exit 1
fi

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 not found"
    exit 1
fi

# Check Node
if ! command -v node &> /dev/null; then
    echo "❌ Error: Node.js not found"
    exit 1
fi

echo "✅ Prerequisites checked"
echo ""

# Install backend dependencies
echo "📦 Installing backend dependencies..."
if [ -d "venv" ]; then
    source venv/bin/activate
fi
pip install -q fastapi uvicorn httpx structlog pydantic anthropic 2>/dev/null || true

# Install frontend dependencies
echo "📦 Installing frontend dependencies..."
if [ ! -d "frontend/node_modules" ]; then
    cd frontend
    npm install --silent
    cd ..
fi

# Check .env.local
if [ ! -f "frontend/.env.local" ]; then
    echo "📝 Creating frontend/.env.local..."
    cat > frontend/.env.local << EOF
NEXT_PUBLIC_API_URL=http://localhost:8008
NEXT_PUBLIC_API_TOKEN=your-auth-token-here
EOF
fi

echo ""
echo "🎯 Starting services..."
echo ""

# Start backend in background
echo "▶️  Starting backend (FastAPI) on http://localhost:8008..."
nohup python3 -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8008 > backend.log 2>&1 &
BACKEND_PID=$!
echo "   Backend PID: $BACKEND_PID"
echo "   Logs: tail -f backend.log"

# Wait for backend to start
echo "⏳ Waiting for backend to be ready..."
for i in {1..30}; do
    if curl -s http://localhost:8008/health > /dev/null 2>&1; then
        echo "   ✅ Backend is ready!"
        break
    fi
    sleep 1
    if [ $i -eq 30 ]; then
        echo "   ❌ Backend failed to start. Check backend.log"
        kill $BACKEND_PID 2>/dev/null
        exit 1
    fi
done

# Start frontend in background
echo ""
echo "▶️  Starting frontend (Next.js) on http://localhost:7007..."
cd frontend
PORT=7007 nohup npm run dev > ../frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..
echo "   Frontend PID: $FRONTEND_PID"
echo "   Logs: tail -f frontend.log"

# Wait for frontend to start
echo "⏳ Waiting for frontend to be ready..."
for i in {1..60}; do
    if curl -s http://localhost:7007 > /dev/null 2>&1; then
        echo "   ✅ Frontend is ready!"
        break
    fi
    sleep 1
    if [ $i -eq 60 ]; then
        echo "   ⚠️  Frontend is taking longer than expected..."
        echo "   Check frontend.log for details"
    fi
done

echo ""
echo "======================================"
echo "✅ All services started successfully!"
echo "======================================"
echo ""
echo "🌐 Access the interface:"
echo "   Frontend: http://localhost:7007"
echo "   Backend:  http://localhost:8008"
echo "   Health:   http://localhost:8008/health"
echo ""
echo "📊 Monitor logs:"
echo "   Backend:  tail -f backend.log"
echo "   Frontend: tail -f frontend.log"
echo ""
echo "🛑 To stop all services:"
echo "   ./scripts/stop_all.sh"
echo "   Or manually: kill $BACKEND_PID $FRONTEND_PID"
echo ""
echo "💡 Tips:"
echo "   - Open browser to http://localhost:7007"
echo "   - Try: 'Analyze account ACC-001'"
echo "   - Watch agent status in left sidebar"
echo ""

# Save PIDs for stop script
echo "$BACKEND_PID" > .backend.pid
echo "$FRONTEND_PID" > .frontend.pid

echo "🎉 Ready to analyze accounts!"
