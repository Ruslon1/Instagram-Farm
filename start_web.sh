#!/bin/bash

echo "🚀 Starting Instagram Bot Web Interface..."

# Check if Redis is running
if ! pgrep redis-server > /dev/null; then
    echo "📡 Starting Redis..."
    if command -v brew &> /dev/null; then
        brew services start redis
    else
        redis-server --daemonize yes
    fi
    sleep 2
fi

# Check Redis connection
if redis-cli ping > /dev/null 2>&1; then
    echo "✅ Redis is running"
else
    echo "❌ Redis connection failed"
    exit 1
fi

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Create directories
mkdir -p videos sessions static logs

# Initialize database
echo "🗄️ Initializing database..."
python3 -c "from modules.database import init_database; init_database()"

# Start Celery worker in background
echo "⚡ Starting Celery worker..."
nohup celery -A celery_app worker --loglevel=info --pool=solo > logs/celery.log 2>&1 &
CELERY_PID=$!

sleep 3

# Check Celery
if ps -p $CELERY_PID > /dev/null; then
    echo "✅ Celery worker is running (PID: $CELERY_PID)"
    echo $CELERY_PID > celery.pid
else
    echo "❌ Celery worker failed to start"
    exit 1
fi

# Start FastAPI server
echo "🌐 Starting FastAPI server..."
echo "📱 Web interface will be available at:"
echo "   Backend API: http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo "🔴 Press Ctrl+C to stop all services"

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Stopping all services..."

    # Stop Celery
    if [ -f celery.pid ]; then
        CELERY_PID=$(cat celery.pid)
        kill $CELERY_PID 2>/dev/null
        rm -f celery.pid
    fi

    # Stop any remaining processes
    pkill -f "celery worker" 2>/dev/null

    echo "✅ All services stopped"
    exit 0
}

# Set trap for cleanup
trap cleanup SIGINT SIGTERM

# Start FastAPI (this will block)
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload