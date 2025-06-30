#!/bin/bash

# Setup cron job for automatic log cleanup
# This script adds a daily cron job to clean up old log files

echo "Setting up automatic log cleanup..."

# Get the current directory
CURRENT_DIR=$(pwd)

# Create the cron job entry (run daily at 2 AM)
CRON_JOB="0 2 * * * cd $CURRENT_DIR && ./cleanup_logs.sh >> cleanup.log 2>&1"

# Add to crontab
(crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -

echo "Cron job added successfully!"
echo "Log cleanup will run daily at 2:00 AM"
echo "To view cron jobs: crontab -l"
echo "To remove cron job: crontab -e" 