#!/bin/bash

# Monitoring script for Instagram Bot

echo "📊 Instagram Bot Monitoring Dashboard"
echo "======================================="

# Function to check service health
check_service_health() {
    local service_name=$1
    local health_url=$2

    if curl -f "$health_url" > /dev/null 2>&1; then
        echo "✅ $service_name: Healthy"
        return 0
    else
        echo "❌ $service_name: Unhealthy"
        return 1
    fi
}

# Function to check container status
check_container_status() {
    echo ""
    echo "🐳 Container Status:"
    echo "-------------------"
    docker-compose ps --format "table {{.Name}}\t{{.State}}\t{{.Status}}"
}

# Function to show resource usage
show_resource_usage() {
    echo ""
    echo "💾 Resource Usage:"
    echo "------------------"

    # System resources
    echo "🖥️ System:"
    echo "   CPU: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)% used"
    echo "   Memory: $(free -h | awk 'NR==2{printf "   %s/%s (%.1f%%)", $3,$2,$3*100/$2}')"
    echo "   Disk: $(df -h / | awk 'NR==2{printf "%s/%s (%s used)", $3,$2,$5}')"

    echo ""
    echo "🐳 Docker containers:"
    docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}"
}

# Function to show recent logs
show_recent_logs() {
    echo ""
    echo "📋 Recent Logs (last 10 lines):"
    echo "--------------------------------"

    echo "📱 App logs:"
    docker-compose logs --tail=5 app | tail -5

    echo ""
    echo "⚡ Celery logs:"
    docker-compose logs --tail=5 celery | tail -5
}

# Function to check database
check_database() {
    echo ""
    echo "🗄️ Database Status:"
    echo "-------------------"

    if docker-compose exec -T postgres pg_isready -U instagram_bot > /dev/null 2>&1; then
        echo "✅ PostgreSQL: Connected"

        # Get database stats
        DB_SIZE=$(docker-compose exec -T postgres psql -U instagram_bot -d instagram_bot -t -c "SELECT pg_size_pretty(pg_database_size('instagram_bot'));" 2>/dev/null | xargs)
        ACCOUNT_COUNT=$(docker-compose exec -T postgres psql -U instagram_bot -d instagram_bot -t -c "SELECT COUNT(*) FROM accounts;" 2>/dev/null | xargs)
        VIDEO_COUNT=$(docker-compose exec -T postgres psql -U instagram_bot -d instagram_bot -t -c "SELECT COUNT(*) FROM videos;" 2>/dev/null | xargs)

        echo "   Database size: $DB_SIZE"
        echo "   Accounts: $ACCOUNT_COUNT"
        echo "   Videos: $VIDEO_COUNT"
    else
        echo "❌ PostgreSQL: Disconnected"
    fi

    # Check Redis
    if docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; then
        echo "✅ Redis: Connected"
        REDIS_MEMORY=$(docker-compose exec -T redis redis-cli info memory | grep used_memory_human | cut -d: -f2 | tr -d '\r')
        echo "   Memory usage: $REDIS_MEMORY"
    else
        echo "❌ Redis: Disconnected"
    fi
}

# Function to show task status
show_task_status() {
    echo ""
    echo "📋 Task Status:"
    echo "---------------"

    # Check if app is responding
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        # Get task stats from API
        TASK_STATS=$(curl -s http://localhost:8000/api/stats 2>/dev/null)
        if [ $? -eq 0 ]; then
            echo "🏃 Running tasks: $(echo $TASK_STATS | jq -r '.running_tasks // "N/A"')"
            echo "📊 Posts today: $(echo $TASK_STATS | jq -r '.posts_today // "N/A"')"
            echo "📱 Active accounts: $(echo $TASK_STATS | jq -r '.active_accounts // "N/A"')"
            echo "📼 Pending videos: $(echo $TASK_STATS | jq -r '.pending_videos // "N/A"')"
        else
            echo "⚠️ Unable to fetch task statistics"
        fi
    else
        echo "❌ API not responding"
    fi
}

# Function to check for errors
check_for_errors() {
    echo ""
    echo "🚨 Recent Errors:"
    echo "-----------------"

    ERROR_COUNT=$(docker-compose logs --since=1h 2>/dev/null | grep -i "error\|exception\|failed" | wc -l)
    if [ "$ERROR_COUNT" -gt 0 ]; then
        echo "⚠️ Found $ERROR_COUNT errors in the last hour"
        echo "Recent errors:"
        docker-compose logs --since=1h 2>/dev/null | grep -i "error\|exception\|failed" | tail -3
    else
        echo "✅ No errors found in the last hour"
    fi
}

# Function to show disk usage
check_disk_usage() {
    echo ""
    echo "💽 Storage Usage:"
    echo "-----------------"

    echo "📁 Application directories:"
    if [ -d "./videos" ]; then
        VIDEOS_SIZE=$(du -sh ./videos 2>/dev/null | cut -f1)
        VIDEOS_COUNT=$(find ./videos -name "*.mp4" 2>/dev/null | wc -l)
        echo "   Videos: $VIDEOS_SIZE ($VIDEOS_COUNT files)"
    fi

    if [ -d "./sessions" ]; then
        SESSIONS_SIZE=$(du -sh ./sessions 2>/dev/null | cut -f1)
        SESSIONS_COUNT=$(find ./sessions -name "*.session" 2>/dev/null | wc -l)
        echo "   Sessions: $SESSIONS_SIZE ($SESSIONS_COUNT files)"
    fi

    if [ -d "./logs" ]; then
        LOGS_SIZE=$(du -sh ./logs 2>/dev/null | cut -f1)
        echo "   Logs: $LOGS_SIZE"
    fi

    echo ""
    echo "🐳 Docker usage:"
    echo "   Images: $(docker images --format 'table {{.Size}}' | tail -n +2 | awk '{sum += $1} END {print sum "MB"}')"
    echo "   Volumes: $(docker system df --format 'table {{.Type}}\t{{.Size}}' | grep 'Volumes' | awk '{print $2}')"
}

# Main monitoring function
main() {
    # Parse command line arguments
    case "${1:-status}" in
        "status"|"")
            check_container_status
            check_service_health "Backend API" "http://localhost:8000/health"
            check_service_health "Frontend" "http://localhost:3000"
            check_database
            show_task_status
            ;;
        "resources"|"res")
            show_resource_usage
            ;;
        "logs")
            show_recent_logs
            ;;
        "errors"|"err")
            check_for_errors
            ;;
        "disk"|"storage")
            check_disk_usage
            ;;
        "full"|"all")
            check_container_status
            check_service_health "Backend API" "http://localhost:8000/health"
            check_service_health "Frontend" "http://localhost:3000"
            check_database
            show_task_status
            show_resource_usage
            check_disk_usage
            check_for_errors
            ;;
        "help"|"-h"|"--help")
            echo "Usage: $0 [command]"
            echo ""
            echo "Commands:"
            echo "  status    Show service status (default)"
            echo "  resources Show resource usage"
            echo "  logs      Show recent logs"
            echo "  errors    Check for recent errors"
            echo "  disk      Show disk usage"
            echo "  full      Show all information"
            echo "  help      Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0           # Show basic status"
            echo "  $0 full      # Show detailed information"
            echo "  $0 logs      # Show recent logs"
            exit 0
            ;;
        *)
            echo "❌ Unknown command: $1"
            echo "Use '$0 help' for usage information"
            exit 1
            ;;
    esac

    echo ""
    echo "🕐 Last updated: $(date)"
    echo ""
    echo "💡 Quick commands:"
    echo "   View logs: docker-compose logs -f [service]"
    echo "   Restart service: docker-compose restart [service]"
    echo "   Full restart: docker-compose down && docker-compose up -d"
}

# Check if jq is installed (for JSON parsing)
if ! command -v jq &> /dev/null; then
    echo "⚠️ jq not found. Installing..."
    if command -v apt-get &> /dev/null; then
        sudo apt-get update && sudo apt-get install -y jq
    elif command -v yum &> /dev/null; then
        sudo yum install -y jq
    else
        echo "❌ Could not install jq. Some features may not work."
    fi
fi

# Run main function
main "$@"