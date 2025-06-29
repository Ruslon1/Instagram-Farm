#!/bin/bash

echo "🗄️ Fixing Database Issues..."

# Check database connection
echo "📡 Testing database connection..."
docker-compose exec postgres pg_isready -U instagram_bot && echo "✅ Database connection OK" || echo "❌ Database connection failed"

# Check if database exists
echo "🔍 Checking if database exists..."
DB_EXISTS=$(docker-compose exec -T postgres psql -U instagram_bot -lqt | cut -d \| -f 1 | grep -w instagram_bot | wc -l)
if [ "$DB_EXISTS" -eq 1 ]; then
    echo "✅ Database 'instagram_bot' exists"
else
    echo "❌ Database 'instagram_bot' does not exist"
    echo "🔨 Creating database..."
    docker-compose exec -T postgres createdb -U instagram_bot instagram_bot
fi

# Initialize database tables
echo "🏗️ Initializing database tables..."
docker-compose exec app python -c "
try:
    from modules.database import init_database
    init_database()
    print('✅ Database initialized successfully')
except Exception as e:
    print(f'❌ Database initialization failed: {e}')
    import traceback
    traceback.print_exc()
"

# Test database content
echo "📋 Checking database tables..."
docker-compose exec -T postgres psql -U instagram_bot -d instagram_bot -c "\dt" 2>/dev/null || echo "❌ Cannot list tables"

# Check if tables have expected structure
echo "🔍 Verifying table structure..."
docker-compose exec -T postgres psql -U instagram_bot -d instagram_bot -c "
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY table_name;
" 2>/dev/null || echo "❌ Cannot query table info"

# Test stats query manually
echo "📊 Testing stats query..."
docker-compose exec app python -c "
try:
    from modules.database import get_database_connection
    with get_database_connection() as conn:
        cursor = conn.cursor()

        # Test each part of the stats query
        print('Testing accounts count...')
        cursor.execute('SELECT COUNT(*) FROM accounts WHERE CASE WHEN active IS NULL THEN TRUE ELSE active END = TRUE')
        accounts = cursor.fetchone()[0]
        print(f'Active accounts: {accounts}')

        print('Testing videos count...')
        cursor.execute('SELECT COUNT(*) FROM videos WHERE CASE WHEN status IS NULL THEN \'pending\' ELSE status END = \'pending\'')
        videos = cursor.fetchone()[0]
        print(f'Pending videos: {videos}')

        print('Testing publications count...')
        cursor.execute('SELECT COUNT(*) FROM publicationhistory WHERE DATE(created_at) = CURRENT_DATE')
        posts = cursor.fetchone()[0]
        print(f'Posts today: {posts}')

        print('✅ All stats queries work')

except Exception as e:
    print(f'❌ Stats query failed: {e}')
    import traceback
    traceback.print_exc()
"

# Restart app to ensure clean state
echo "🔄 Restarting app..."
docker-compose restart app

echo "⏳ Waiting for app to restart..."
sleep 10

# Test the stats endpoint
echo "🌐 Testing stats API endpoint..."
curl -s http://94.131.86.226:8000/api/stats | jq '.' 2>/dev/null || curl -s http://94.131.86.226:8000/api/stats

echo ""
echo "🎯 Manual test commands:"
echo "  curl http://94.131.86.226:8000/api/stats"
echo "  docker-compose logs app"
echo "  docker-compose exec app python -c \"from modules.database import get_database_connection; print('DB works')\""