"""
SQLite database service for analytics and historical data
Stores notification history, clicks, and periodic model snapshots
"""
import sqlite3
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class AnalyticsDatabase:
    """SQLite database for storing notification analytics and history"""
    
    def __init__(self, db_path: str = "data/analytics.db"):
        """
        Initialize analytics database
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        
        # Create data directory if it doesn't exist
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize database schema
        self._init_schema()
        
        logger.info(f"Analytics database initialized at {db_path}")
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            conn.close()
    
    def _init_schema(self):
        """Create database tables if they don't exist"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Notifications table - stores every notification sent
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS notifications (
                    notification_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    template TEXT NOT NULL,
                    channel TEXT NOT NULL,
                    title TEXT,
                    body TEXT,
                    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT
                )
            """)
            
            # Clicks table - stores user interactions
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS clicks (
                    click_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    notification_id TEXT NOT NULL,
                    clicked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    engagement REAL DEFAULT 1.0,
                    FOREIGN KEY (notification_id) REFERENCES notifications(notification_id)
                )
            """)
            
            # Model snapshots table - periodic backups of model stats
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS model_snapshots (
                    snapshot_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    snapshot_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    template_stats TEXT NOT NULL,
                    channel_stats TEXT NOT NULL,
                    total_pulls INTEGER,
                    total_selections INTEGER
                )
            """)
            
            # Performance metrics table - aggregated statistics
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS performance_metrics (
                    metric_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    metric_date DATE NOT NULL,
                    template TEXT NOT NULL,
                    channel TEXT NOT NULL,
                    total_sent INTEGER DEFAULT 0,
                    total_clicks INTEGER DEFAULT 0,
                    click_rate REAL DEFAULT 0.0,
                    avg_engagement REAL DEFAULT 0.0,
                    UNIQUE(metric_date, template, channel)
                )
            """)
            
            # Templates table - template definitions
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS templates (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    type TEXT NOT NULL,
                    channels TEXT NOT NULL,
                    title TEXT NOT NULL,
                    body TEXT NOT NULL,
                    email_html TEXT,
                    variables TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes for better query performance
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_notifications_user 
                ON notifications(user_id)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_notifications_sent 
                ON notifications(sent_at)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_clicks_notification 
                ON clicks(notification_id)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_clicks_timestamp 
                ON clicks(clicked_at)
            """)
            
            logger.info("Database schema initialized")
    
    def log_notification(
        self,
        notification_id: str,
        user_id: str,
        template: str,
        channel: str,
        title: str = None,
        body: str = None,
        metadata: Dict[str, Any] = None
    ) -> bool:
        """
        Log a sent notification
        
        Args:
            notification_id: Unique notification identifier
            user_id: User who received the notification
            template: Template used (FORMAL, URGENT, etc.)
            channel: Channel used (webpush, email, etc.)
            title: Notification title
            body: Notification body
            metadata: Additional metadata as dict
        
        Returns:
            True if logged successfully
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO notifications 
                    (notification_id, user_id, template, channel, title, body, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    notification_id,
                    user_id,
                    template,
                    channel,
                    title,
                    body,
                    json.dumps(metadata) if metadata else None
                ))
                
                logger.debug(f"Logged notification {notification_id} to database")
                return True
        
        except sqlite3.IntegrityError:
            logger.warning(f"Notification {notification_id} already exists in database")
            return False
        except Exception as e:
            logger.error(f"Failed to log notification: {e}")
            return False
    
    def log_click(
        self,
        notification_id: str,
        engagement: float = 1.0
    ) -> bool:
        """
        Log a notification click
        
        Args:
            notification_id: Notification that was clicked
            engagement: Engagement score (0.0 - 1.0)
        
        Returns:
            True if logged successfully
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO clicks (notification_id, engagement)
                    VALUES (?, ?)
                """, (notification_id, engagement))
                
                logger.debug(f"Logged click for notification {notification_id}")
                return True
        
        except Exception as e:
            logger.error(f"Failed to log click: {e}")
            return False
    
    def save_model_snapshot(
        self,
        template_stats: Dict[str, Any],
        channel_stats: Dict[str, Any]
    ) -> bool:
        """
        Save a snapshot of current model statistics
        
        Args:
            template_stats: Template bandit statistics
            channel_stats: Tug of war channel statistics
        
        Returns:
            True if saved successfully
        """
        try:
            # Calculate totals
            total_pulls = sum(
                stats.get('pulls', 0) 
                for stats in template_stats.values()
            )
            total_selections = sum(
                stats.get('selections', 0) 
                for stats in channel_stats.values()
            )
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO model_snapshots 
                    (template_stats, channel_stats, total_pulls, total_selections)
                    VALUES (?, ?, ?, ?)
                """, (
                    json.dumps(template_stats),
                    json.dumps(channel_stats),
                    total_pulls,
                    total_selections
                ))
                
                logger.info(f"Saved model snapshot (pulls={total_pulls}, selections={total_selections})")
                return True
        
        except Exception as e:
            logger.error(f"Failed to save model snapshot: {e}")
            return False
    
    def get_click_rate(
        self,
        template: str = None,
        channel: str = None,
        days: int = 7
    ) -> float:
        """
        Calculate click rate for template/channel over time period
        
        Args:
            template: Filter by template (optional)
            channel: Filter by channel (optional)
            days: Number of days to look back
        
        Returns:
            Click rate (0.0 - 1.0)
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Build query dynamically based on filters
                query = """
                    SELECT 
                        COUNT(DISTINCT n.notification_id) as total_sent,
                        COUNT(DISTINCT c.click_id) as total_clicks
                    FROM notifications n
                    LEFT JOIN clicks c ON n.notification_id = c.notification_id
                    WHERE n.sent_at >= datetime('now', '-' || ? || ' days')
                """
                params = [days]
                
                if template:
                    query += " AND n.template = ?"
                    params.append(template)
                
                if channel:
                    query += " AND n.channel = ?"
                    params.append(channel)
                
                cursor.execute(query, params)
                row = cursor.fetchone()
                
                total_sent = row['total_sent'] or 0
                total_clicks = row['total_clicks'] or 0
                
                return total_clicks / total_sent if total_sent > 0 else 0.0
        
        except Exception as e:
            logger.error(f"Failed to calculate click rate: {e}")
            return 0.0
    
    def get_recent_notifications(
        self,
        limit: int = 50,
        user_id: str = None
    ) -> List[Dict[str, Any]]:
        """
        Get recent notifications with click status
        
        Args:
            limit: Maximum number of results
            user_id: Filter by user (optional)
        
        Returns:
            List of notification dictionaries
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                query = """
                    SELECT 
                        n.*,
                        c.clicked_at,
                        c.engagement,
                        CASE WHEN c.click_id IS NOT NULL THEN 1 ELSE 0 END as clicked
                    FROM notifications n
                    LEFT JOIN clicks c ON n.notification_id = c.notification_id
                """
                
                params = []
                if user_id:
                    query += " WHERE n.user_id = ?"
                    params.append(user_id)
                
                query += " ORDER BY n.sent_at DESC LIMIT ?"
                params.append(limit)
                
                cursor.execute(query, params)
                
                return [dict(row) for row in cursor.fetchall()]
        
        except Exception as e:
            logger.error(f"Failed to get recent notifications: {e}")
            return []
    
    def get_performance_summary(
        self,
        days: int = 7
    ) -> Dict[str, Any]:
        """
        Get performance summary for the dashboard
        
        Args:
            days: Number of days to analyze
        
        Returns:
            Dictionary with performance metrics
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Template performance
                cursor.execute("""
                    SELECT 
                        n.template,
                        COUNT(DISTINCT n.notification_id) as sent,
                        COUNT(DISTINCT c.click_id) as clicks,
                        CAST(COUNT(DISTINCT c.click_id) AS REAL) / 
                        COUNT(DISTINCT n.notification_id) as click_rate,
                        AVG(c.engagement) as avg_engagement
                    FROM notifications n
                    LEFT JOIN clicks c ON n.notification_id = c.notification_id
                    WHERE n.sent_at >= datetime('now', '-' || ? || ' days')
                    GROUP BY n.template
                """, (days,))
                
                templates = [dict(row) for row in cursor.fetchall()]
                
                # Channel performance
                cursor.execute("""
                    SELECT 
                        n.channel,
                        COUNT(DISTINCT n.notification_id) as sent,
                        COUNT(DISTINCT c.click_id) as clicks,
                        CAST(COUNT(DISTINCT c.click_id) AS REAL) / 
                        COUNT(DISTINCT n.notification_id) as click_rate
                    FROM notifications n
                    LEFT JOIN clicks c ON n.notification_id = c.notification_id
                    WHERE n.sent_at >= datetime('now', '-' || ? || ' days')
                    GROUP BY n.channel
                """, (days,))
                
                channels = [dict(row) for row in cursor.fetchall()]
                
                # Overall stats
                cursor.execute("""
                    SELECT 
                        COUNT(DISTINCT n.notification_id) as total_sent,
                        COUNT(DISTINCT c.click_id) as total_clicks,
                        CAST(COUNT(DISTINCT c.click_id) AS REAL) / 
                        COUNT(DISTINCT n.notification_id) as overall_click_rate
                    FROM notifications n
                    LEFT JOIN clicks c ON n.notification_id = c.notification_id
                    WHERE n.sent_at >= datetime('now', '-' || ? || ' days')
                """, (days,))
                
                overall = dict(cursor.fetchone())
                
                return {
                    'templates': templates,
                    'channels': channels,
                    'overall': overall,
                    'period_days': days
                }
        
        except Exception as e:
            logger.error(f"Failed to get performance summary: {e}")
            return {
                'templates': [],
                'channels': [],
                'overall': {},
                'period_days': days
            }
    
    def create_template(self, template_id: str, name: str, template_type: str, 
                       channels: List[str], title: str, body: str, 
                       email_html: str = None, variables: List[str] = None) -> bool:
        """Create a new template"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO templates (id, name, type, channels, title, body, email_html, variables)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    template_id,
                    name,
                    template_type,
                    json.dumps(channels),
                    title,
                    body,
                    email_html,
                    json.dumps(variables or [])
                ))
                logger.info(f"Created template: {name} ({template_id})")
                return True
        except Exception as e:
            logger.error(f"Failed to create template: {e}")
            return False
    
    def get_all_templates(self) -> List[Dict[str, Any]]:
        """Get all templates"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM templates ORDER BY created_at DESC")
                rows = cursor.fetchall()
                
                templates = []
                for row in rows:
                    templates.append({
                        'id': row['id'],
                        'name': row['name'],
                        'type': row['type'],
                        'channels': json.loads(row['channels']),
                        'title': row['title'],
                        'body': row['body'],
                        'email_html': row['email_html'],
                        'variables': json.loads(row['variables']),
                        'created_at': row['created_at'],
                        'updated_at': row['updated_at']
                    })
                return templates
        except Exception as e:
            logger.error(f"Failed to get templates: {e}")
            return []
    
    def get_template(self, template_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific template"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM templates WHERE id = ?", (template_id,))
                row = cursor.fetchone()
                
                if row:
                    return {
                        'id': row['id'],
                        'name': row['name'],
                        'type': row['type'],
                        'channels': json.loads(row['channels']),
                        'title': row['title'],
                        'body': row['body'],
                        'email_html': row['email_html'],
                        'variables': json.loads(row['variables']),
                        'created_at': row['created_at'],
                        'updated_at': row['updated_at']
                    }
                return None
        except Exception as e:
            logger.error(f"Failed to get template: {e}")
            return None
    
    def update_template(self, template_id: str, name: str, template_type: str,
                       channels: List[str], title: str, body: str,
                       email_html: str = None, variables: List[str] = None) -> bool:
        """Update an existing template"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE templates 
                    SET name = ?, type = ?, channels = ?, title = ?, body = ?, 
                        email_html = ?, variables = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (
                    name,
                    template_type,
                    json.dumps(channels),
                    title,
                    body,
                    email_html,
                    json.dumps(variables or []),
                    template_id
                ))
                logger.info(f"Updated template: {name} ({template_id})")
                return True
        except Exception as e:
            logger.error(f"Failed to update template: {e}")
            return False
    
    def delete_template(self, template_id: str) -> bool:
        """Delete a template"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM templates WHERE id = ?", (template_id,))
                logger.info(f"Deleted template: {template_id}")
                return True
        except Exception as e:
            logger.error(f"Failed to delete template: {e}")
            return False
