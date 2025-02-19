import os
from celery import Celery
from datetime import datetime, timedelta
import pytz
import sqlite3
import json
from pathlib import Path
from social_media_manager import SocialMediaManager
import logging
from typing import Dict, List, Any

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scheduler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('cat_content_scheduler')

# Initialize Celery
celery_app = Celery('cat_content_scheduler',
                    broker='redis://localhost:6379/0',
                    backend='redis://localhost:6379/0')

# Celery configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max runtime
    worker_max_tasks_per_child=200,
    worker_prefetch_multiplier=1
)

class SchedulerService:
    def __init__(self):
        self.social_media_manager = SocialMediaManager()
        self.db_path = 'cat_content.db'
        
    def get_db_connection(self):
        """Get a database connection."""
        return sqlite3.connect(self.db_path)

    def get_pending_posts(self) -> List[Dict[str, Any]]:
        """Get all pending posts from the database."""
        with self.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    ph.id,
                    ca.file_path,
                    ca.caption,
                    ca.hashtags,
                    ph.platform,
                    ph.posted_at,
                    ca.media_type
                FROM posting_history ph
                JOIN content_analysis ca ON ph.analysis_id = ca.id
                WHERE ph.status = 'scheduled'
                AND datetime(ph.posted_at) <= datetime('now', '+1 hour')
                ORDER BY ph.posted_at ASC
            """)
            posts = cursor.fetchall()
            
            return [{
                'id': post[0],
                'file_path': post[1],
                'caption': post[2],
                'hashtags': post[3],
                'platform': post[4],
                'scheduled_time': post[5],
                'media_type': post[6]
            } for post in posts]

    def update_post_status(self, post_id: int, status: str, error_message: str = None):
        """Update the status of a post in the database."""
        with self.get_db_connection() as conn:
            cursor = conn.cursor()
            if error_message:
                cursor.execute("""
                    UPDATE posting_history
                    SET status = ?, error_message = ?, updated_at = datetime('now')
                    WHERE id = ?
                """, (status, error_message, post_id))
            else:
                cursor.execute("""
                    UPDATE posting_history
                    SET status = ?, updated_at = datetime('now')
                    WHERE id = ?
                """, (status, post_id))
            conn.commit()

@celery_app.task(bind=True, name='schedule_service.process_pending_posts')
def process_pending_posts(self):
    """Celery task to process pending posts."""
    scheduler = SchedulerService()
    pending_posts = scheduler.get_pending_posts()
    
    for post in pending_posts:
        try:
            # Check if media file exists
            if not os.path.exists(post['file_path']):
                raise FileNotFoundError(f"Media file not found: {post['file_path']}")
            
            # Post to the specified platform
            success = False
            if post['platform'] == 'instagram':
                success = scheduler.social_media_manager.post_to_instagram(
                    post['file_path'], post['caption'], post['hashtags']
                )
            elif post['platform'] == 'twitter':
                success = scheduler.social_media_manager.post_to_twitter(
                    post['file_path'], post['caption'], post['hashtags']
                )
            elif post['platform'] == 'facebook':
                success = scheduler.social_media_manager.post_to_facebook(
                    post['file_path'], post['caption'], post['hashtags']
                )
            elif post['platform'] == 'tiktok' and post['media_type'] == 'video':
                success = scheduler.social_media_manager.post_to_tiktok(
                    post['file_path'], post['caption'], post['hashtags']
                )
            
            # Update post status
            if success:
                scheduler.update_post_status(post['id'], 'success')
                logger.info(f"Successfully posted to {post['platform']}: {post['file_path']}")
            else:
                scheduler.update_post_status(
                    post['id'], 
                    'failed',
                    f"Failed to post to {post['platform']}"
                )
                logger.error(f"Failed to post to {post['platform']}: {post['file_path']}")
            
        except Exception as e:
            error_message = f"Error posting to {post['platform']}: {str(e)}"
            scheduler.update_post_status(post['id'], 'failed', error_message)
            logger.error(error_message, exc_info=True)

@celery_app.task(bind=True, name='schedule_service.cleanup_old_media')
def cleanup_old_media(self):
    """Celery task to clean up old media files."""
    temp_dir = Path("temp")
    if temp_dir.exists():
        current_time = datetime.now()
        for temp_file in temp_dir.glob("temp_*"):
            try:
                file_age = current_time - datetime.fromtimestamp(temp_file.stat().st_mtime)
                if file_age > timedelta(days=7):  # Keep files for 7 days
                    temp_file.unlink()
                    logger.info(f"Cleaned up old media file: {temp_file}")
            except Exception as e:
                logger.error(f"Error cleaning up {temp_file}: {e}")

@celery_app.task(bind=True, name='schedule_service.backup_database')
def backup_database(self):
    """Celery task to backup the database."""
    try:
        backup_dir = Path("backups")
        backup_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = backup_dir / f"cat_content_backup_{timestamp}.db"
        
        # Create database backup
        with sqlite3.connect('cat_content.db') as src, sqlite3.connect(str(backup_path)) as dst:
            src.backup(dst)
        
        # Keep only last 7 backups
        backups = sorted(backup_dir.glob("cat_content_backup_*.db"))
        for old_backup in backups[:-7]:
            old_backup.unlink()
        
        logger.info(f"Database backup created: {backup_path}")
    except Exception as e:
        logger.error(f"Error creating database backup: {e}", exc_info=True)

# Schedule periodic tasks
@celery_app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    # Check for pending posts every 5 minutes
    sender.add_periodic_task(
        300.0,
        process_pending_posts.s(),
        name='check_pending_posts'
    )
    
    # Clean up old media files daily at 3 AM
    sender.add_periodic_task(
        crontab(hour=3, minute=0),
        cleanup_old_media.s(),
        name='cleanup_old_media'
    )
    
    # Backup database daily at 2 AM
    sender.add_periodic_task(
        crontab(hour=2, minute=0),
        backup_database.s(),
        name='backup_database'
    )

if __name__ == '__main__':
    celery_app.start() 