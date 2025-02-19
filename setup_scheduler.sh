#!/bin/bash

# Create necessary directories
mkdir -p logs backups

# Install Redis if not already installed
if ! command -v redis-server &> /dev/null; then
    echo "Installing Redis..."
    brew install redis
fi

# Start Redis if not running
if ! pgrep redis-server > /dev/null; then
    echo "Starting Redis..."
    brew services start redis
fi

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Create and set permissions for log files
touch logs/scheduler.log logs/scheduler.error.log
chmod 644 logs/scheduler.log logs/scheduler.error.log

# Copy launch daemon plist
echo "Installing launch daemon..."
sudo cp com.bugzthecat.scheduler.plist /Library/LaunchDaemons/
sudo chown root:wheel /Library/LaunchDaemons/com.bugzthecat.scheduler.plist
sudo chmod 644 /Library/LaunchDaemons/com.bugzthecat.scheduler.plist

# Load the launch daemon
echo "Loading scheduler service..."
sudo launchctl unload /Library/LaunchDaemons/com.bugzthecat.scheduler.plist 2>/dev/null
sudo launchctl load /Library/LaunchDaemons/com.bugzthecat.scheduler.plist

# Check service status
echo "Checking service status..."
sleep 2
if pgrep -f "celery.*scheduler_service" > /dev/null; then
    echo "✅ Scheduler service is running!"
    echo "You can view logs at:"
    echo "  - Main log: $(pwd)/logs/scheduler.log"
    echo "  - Error log: $(pwd)/logs/scheduler.error.log"
else
    echo "❌ Service failed to start. Check logs for details."
fi

# Print management commands
echo "
Management commands:
------------------
Start service:   sudo launchctl load /Library/LaunchDaemons/com.bugzthecat.scheduler.plist
Stop service:    sudo launchctl unload /Library/LaunchDaemons/com.bugzthecat.scheduler.plist
View logs:       tail -f logs/scheduler.log
View errors:     tail -f logs/scheduler.error.log
" 