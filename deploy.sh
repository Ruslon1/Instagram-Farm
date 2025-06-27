#!/bin/bash

echo "🚀 Starting deployment to Yandex Cloud..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ .env file not found!"
    echo "📝 Please copy .env.production to .env and fill in your values"
    exit 1
fi

# Check if required environment variables are set
source .env
if [ -z "$TELEGRAM_TOKEN" ] || [ -z "$TELEGRAM_CHAT_ID" ] || [ -z "$SECRET_KEY" ]; then
    echo "❌ Required environment variables not set!"
    echo "📝 Please fill in TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, and SECRET_KEY in .env"
    exit 1
fi

# Stop existing containers
echo "🛑 Stopping existing containers..."
docker-compose down

# Remove old images (optional)
echo "🧹 Cleaning up old images..."
docker system prune -f

# Build and start services
echo "🔨 Building and starting services..."
docker-compose up -d --build

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 30

# Check health
echo "🔍 Checking service health..."
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Backend is healthy"
else
    echo "❌ Backend health check failed"
    docker-compose logs app
    exit 1
fi

if curl -f http://localhost:3000 > /dev/null 2>&1; then
    echo "✅ Frontend is healthy"
else
    echo "❌ Frontend health check failed"
    docker-compose logs frontend
    exit 1
fi

# Initialize database
echo "🗄️ Initializing database..."
docker-compose exec app python -c "from modules.database import init_database; init_database()"

echo "🎉 Deployment completed successfully!"
echo "📱 Frontend: http://localhost:3000"
echo "🔧 Backend API: http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"
echo ""
echo "📋 To check logs:"
echo "   docker-compose logs -f app"
echo "   docker-compose logs -f celery"
echo "   docker-compose logs -f frontend"
echo ""
echo "🛑 To stop:"
echo "   docker-compose down"