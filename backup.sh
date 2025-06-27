#!/bin/bash

# Backup script for Instagram Bot

BACKUP_DIR="./backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="instagram_bot_backup_$DATE"

echo "🔄 Starting backup process..."

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Function to backup database
backup_database() {
    echo "🗄️ Backing up PostgreSQL database..."

    if docker-compose exec -T postgres pg_isready -U instagram_bot > /dev/null 2>&1; then
        docker-compose exec -T postgres pg_dump -U instagram_bot instagram_bot > "$BACKUP_DIR/${BACKUP_NAME}_database.sql"

        if [ $? -eq 0 ]; then
            echo "✅ Database backup completed: ${BACKUP_NAME}_database.sql"

            # Compress database backup
            gzip "$BACKUP_DIR/${BACKUP_NAME}_database.sql"
            echo "📦 Database backup compressed"
        else
            echo "❌ Database backup failed"
            return 1
        fi
    else
        echo "❌ Database is not accessible"
        return 1
    fi
}

# Function to backup application files
backup_files() {
    echo "📁 Backing up application files..."

    # Create temporary directory for this backup
    TEMP_BACKUP_DIR="$BACKUP_DIR/temp_$DATE"
    mkdir -p "$TEMP_BACKUP_DIR"

    # Backup important directories
    if [ -d "./sessions" ]; then
        cp -r ./sessions "$TEMP_BACKUP_DIR/"
        echo "✅ Sessions backed up"
    fi

    if [ -d "./logs" ]; then
        cp -r ./logs "$TEMP_BACKUP_DIR/"
        echo "✅ Logs backed up"
    fi

    # Backup configuration files
    cp .env "$TEMP_BACKUP_DIR/" 2>/dev/null || echo "⚠️ .env file not found"
    cp docker-compose.yml "$TEMP_BACKUP_DIR/" 2>/dev/null
    cp requirements.txt "$TEMP_BACKUP_DIR/" 2>/dev/null

    # Create tar archive
    tar -czf "$BACKUP_DIR/${BACKUP_NAME}_files.tar.gz" -C "$BACKUP_DIR" "temp_$DATE"

    # Remove temporary directory
    rm -rf "$TEMP_BACKUP_DIR"

    echo "✅ Application files backup completed: ${BACKUP_NAME}_files.tar.gz"
}

# Function to backup Docker volumes
backup_volumes() {
    echo "🐳 Backing up Docker volumes..."

    # Get volume names
    POSTGRES_VOLUME=$(docker volume ls --format "table {{.Name}}" | grep postgres_data)
    REDIS_VOLUME=$(docker volume ls --format "table {{.Name}}" | grep redis_data)

    if [ ! -z "$POSTGRES_VOLUME" ]; then
        docker run --rm -v "${POSTGRES_VOLUME}:/data" -v "$(pwd)/$BACKUP_DIR:/backup" alpine tar czf "/backup/${BACKUP_NAME}_postgres_volume.tar.gz" -C /data .
        echo "✅ PostgreSQL volume backed up"
    fi

    if [ ! -z "$REDIS_VOLUME" ]; then
        docker run --rm -v "${REDIS_VOLUME}:/data" -v "$(pwd)/$BACKUP_DIR:/backup" alpine tar czf "/backup/${BACKUP_NAME}_redis_volume.tar.gz" -C /data .
        echo "✅ Redis volume backed up"
    fi
}

# Function to create backup manifest
create_manifest() {
    echo "📋 Creating backup manifest..."

    MANIFEST_FILE="$BACKUP_DIR/${BACKUP_NAME}_manifest.txt"

    cat > "$MANIFEST_FILE" << EOF
Instagram Bot Backup Manifest
=============================
Backup Date: $(date)
Backup Name: $BACKUP_NAME

Files included:
EOF

    # List all backup files
    ls -la "$BACKUP_DIR"/${BACKUP_NAME}_* >> "$MANIFEST_FILE"

    echo "" >> "$MANIFEST_FILE"
    echo "System Information:" >> "$MANIFEST_FILE"
    echo "OS: $(uname -a)" >> "$MANIFEST_FILE"
    echo "Docker version: $(docker --version)" >> "$MANIFEST_FILE"
    echo "Docker Compose version: $(docker-compose --version)" >> "$MANIFEST_FILE"

    echo "" >> "$MANIFEST_FILE"
    echo "Application Status:" >> "$MANIFEST_FILE"
    docker-compose ps >> "$MANIFEST_FILE"

    echo "✅ Manifest created: ${BACKUP_NAME}_manifest.txt"
}

# Function to cleanup old backups
cleanup_old_backups() {
    echo "🧹 Cleaning up old backups..."

    # Keep only last 7 days of backups
    find "$BACKUP_DIR" -name "instagram_bot_backup_*" -mtime +7 -delete

    REMAINING_BACKUPS=$(ls "$BACKUP_DIR"/instagram_bot_backup_* 2>/dev/null | wc -l)
    echo "✅ Cleanup completed. $REMAINING_BACKUPS backup sets remaining."
}

# Function to verify backup integrity
verify_backup() {
    echo "🔍 Verifying backup integrity..."

    # Check database backup
    if [ -f "$BACKUP_DIR/${BACKUP_NAME}_database.sql.gz" ]; then
        if gzip -t "$BACKUP_DIR/${BACKUP_NAME}_database.sql.gz"; then
            echo "✅ Database backup integrity verified"
        else
            echo "❌ Database backup integrity check failed"
            return 1
        fi
    fi

    # Check files backup
    if [ -f "$BACKUP_DIR/${BACKUP_NAME}_files.tar.gz" ]; then
        if tar -tzf "$BACKUP_DIR/${BACKUP_NAME}_files.tar.gz" > /dev/null 2>&1; then
            echo "✅ Files backup integrity verified"
        else
            echo "❌ Files backup integrity check failed"
            return 1
        fi
    fi

    return 0
}

# Function to show backup status
show_backup_status() {
    echo "📊 Backup Status:"
    echo "=================="

    if [ -d "$BACKUP_DIR" ]; then
        BACKUP_COUNT=$(ls "$BACKUP_DIR"/instagram_bot_backup_* 2>/dev/null | wc -l)
        BACKUP_SIZE=$(du -sh "$BACKUP_DIR" 2>/dev/null | cut -f1)

        echo "📁 Backup directory: $BACKUP_DIR"
        echo "📦 Total backups: $BACKUP_COUNT"
        echo "💾 Total size: $BACKUP_SIZE"
        echo ""

        if [ $BACKUP_COUNT -gt 0 ]; then
            echo "📋 Recent backups:"
            ls -lt "$BACKUP_DIR"/instagram_bot_backup_*_manifest.txt 2>/dev/null | head -5 | while read line; do
                file=$(echo $line | awk '{print $9}')
                date=$(echo $line | awk '{print $6, $7, $8}')
                backup_name=$(basename "$file" _manifest.txt)
                echo "   $backup_name ($date)"
            done
        else
            echo "❌ No backups found"
        fi
    else
        echo "❌ Backup directory does not exist"
    fi
}

# Function to restore from backup
restore_backup() {
    local backup_name=$1

    if [ -z "$backup_name" ]; then
        echo "❌ Please specify backup name to restore"
        echo "Available backups:"
        ls "$BACKUP_DIR"/instagram_bot_backup_*_manifest.txt 2>/dev/null | sed 's/_manifest.txt//' | sed 's/.*\///'
        return 1
    fi

    echo "🔄 Restoring from backup: $backup_name"
    echo "⚠️ This will stop current services and restore data"
    read -p "Are you sure? (y/N): " -n 1 -r
    echo

    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ Restore cancelled"
        return 1
    fi

    # Stop services
    echo "🛑 Stopping services..."
    docker-compose down

    # Restore database
    if [ -f "$BACKUP_DIR/${backup_name}_database.sql.gz" ]; then
        echo "🗄️ Restoring database..."

        # Start only postgres
        docker-compose up -d postgres
        sleep 10

        # Drop and recreate database
        docker-compose exec -T postgres psql -U instagram_bot -c "DROP DATABASE IF EXISTS instagram_bot;"
        docker-compose exec -T postgres psql -U instagram_bot -c "CREATE DATABASE instagram_bot;"

        # Restore data
        gunzip -c "$BACKUP_DIR/${backup_name}_database.sql.gz" | docker-compose exec -T postgres psql -U instagram_bot instagram_bot

        echo "✅ Database restored"
    fi

    # Restore files
    if [ -f "$BACKUP_DIR/${backup_name}_files.tar.gz" ]; then
        echo "📁 Restoring application files..."

        # Extract to temporary directory
        TEMP_RESTORE_DIR="/tmp/restore_$DATE"
        mkdir -p "$TEMP_RESTORE_DIR"
        tar -xzf "$BACKUP_DIR/${backup_name}_files.tar.gz" -C "$TEMP_RESTORE_DIR"

        # Restore sessions
        if [ -d "$TEMP_RESTORE_DIR/temp_*/sessions" ]; then
            rm -rf ./sessions
            cp -r "$TEMP_RESTORE_DIR"/temp_*/sessions ./
            echo "✅ Sessions restored"
        fi

        # Restore environment (with confirmation)
        if [ -f "$TEMP_RESTORE_DIR/temp_*/.env" ]; then
            read -p "Restore .env file? (y/N): " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                cp "$TEMP_RESTORE_DIR"/temp_*/.env ./
                echo "✅ Environment file restored"
            fi
        fi

        # Cleanup
        rm -rf "$TEMP_RESTORE_DIR"
    fi

    # Start all services
    echo "🚀 Starting services..."
    docker-compose up -d

    echo "✅ Restore completed"
}

# Main function
main() {
    case "${1:-backup}" in
        "backup"|"")
            echo "🔄 Starting full backup..."
            backup_database && backup_files && backup_volumes && create_manifest && verify_backup
            if [ $? -eq 0 ]; then
                echo "✅ Backup completed successfully: $BACKUP_NAME"
                cleanup_old_backups
            else
                echo "❌ Backup failed"
                exit 1
            fi
            ;;
        "status")
            show_backup_status
            ;;
        "restore")
            restore_backup "$2"
            ;;
        "verify")
            if [ -z "$2" ]; then
                echo "❌ Please specify backup name to verify"
                exit 1
            fi
            BACKUP_NAME="$2"
            verify_backup
            ;;
        "cleanup")
            cleanup_old_backups
            ;;
        "help"|"-h"|"--help")
            echo "Usage: $0 [command] [options]"
            echo ""
            echo "Commands:"
            echo "  backup          Create full backup (default)"
            echo "  status          Show backup status"
            echo "  restore <name>  Restore from backup"
            echo "  verify <name>   Verify backup integrity"
            echo "  cleanup         Remove old backups"
            echo "  help            Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                                    # Create backup"
            echo "  $0 status                             # Show backup status"
            echo "  $0 restore instagram_bot_backup_20231201_120000  # Restore backup"
            exit 0
            ;;
        *)
            echo "❌ Unknown command: $1"
            echo "Use '$0 help' for usage information"
            exit 1
            ;;
    esac
}

# Check dependencies
if ! command -v docker &> /dev/null || ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker and Docker Compose are required"
    exit 1
fi

# Run main function
main "$@"