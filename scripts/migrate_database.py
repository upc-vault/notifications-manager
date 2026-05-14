"""
Database Migration Script
Adds new columns for user behavior tracking and preferences
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.models.user import db, User
from src.models.notification_log import NotificationLog
from src.models.user_preferences import UserPreferences
from src.api.main import app
from sqlalchemy import text

def migrate_database():
    """Add new columns to existing tables"""
    with app.app_context():
        connection = db.engine.connect()
        
        print("🔄 Starting database migration...")
        
        # Check if columns exist before adding them
        def column_exists(table_name, column_name):
            try:
                result = connection.execute(text(f"PRAGMA table_info({table_name})"))
                columns = [row[1] for row in result]
                return column_name in columns
            except Exception as e:
                print(f"❌ Error checking column: {e}")
                return False
        
        # Migrate User table
        print("\n📝 Migrating User table...")
        user_columns = [
            ("last_active_time", "ALTER TABLE users ADD COLUMN last_active_time DATETIME"),
            ("last_notification_clicked_at", "ALTER TABLE users ADD COLUMN last_notification_clicked_at DATETIME"),
            ("preferred_language", "ALTER TABLE users ADD COLUMN preferred_language VARCHAR(10) DEFAULT 'en'"),
            ("timezone", "ALTER TABLE users ADD COLUMN timezone VARCHAR(50) DEFAULT 'Europe/Madrid'"),
            ("device_type", "ALTER TABLE users ADD COLUMN device_type VARCHAR(20)")
        ]
        
        for col_name, sql in user_columns:
            if not column_exists('users', col_name):
                try:
                    connection.execute(text(sql))
                    connection.commit()
                    print(f"  ✅ Added column: {col_name}")
                except Exception as e:
                    print(f"  ⚠️  Column {col_name} may already exist or error: {e}")
            else:
                print(f"  ⏭️  Column {col_name} already exists")
        
        # Migrate NotificationLog table
        print("\n📝 Migrating NotificationLog table...")
        log_columns = [
            ("time_to_click", "ALTER TABLE notification_logs ADD COLUMN time_to_click INTEGER"),
            ("device_type", "ALTER TABLE notification_logs ADD COLUMN device_type VARCHAR(20)"),
            ("dismissed_at", "ALTER TABLE notification_logs ADD COLUMN dismissed_at DATETIME"),
            ("read_duration", "ALTER TABLE notification_logs ADD COLUMN read_duration INTEGER")
        ]
        
        for col_name, sql in log_columns:
            if not column_exists('notification_logs', col_name):
                try:
                    connection.execute(text(sql))
                    connection.commit()
                    print(f"  ✅ Added column: {col_name}")
                except Exception as e:
                    print(f"  ⚠️  Column {col_name} may already exist or error: {e}")
            else:
                print(f"  ⏭️  Column {col_name} already exists")
        
        # Create user_preferences table if it doesn't exist
        print("\n📝 Creating user_preferences table...")
        try:
            # Check if table exists
            result = connection.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='user_preferences'"))
            if result.fetchone() is None:
                db.create_all()
                print("  ✅ Created user_preferences table")
            else:
                print("  ⏭️  Table user_preferences already exists")
                # Add missing columns to existing table
                pref_columns = [
                    ("high_contrast_mode", "ALTER TABLE user_preferences ADD COLUMN high_contrast_mode BOOLEAN DEFAULT 0"),
                    ("large_text_mode", "ALTER TABLE user_preferences ADD COLUMN large_text_mode BOOLEAN DEFAULT 0")
                ]
                for col_name, sql in pref_columns:
                    if not column_exists('user_preferences', col_name):
                        try:
                            connection.execute(text(sql))
                            connection.commit()
                            print(f"  ✅ Added column: {col_name}")
                        except Exception as e:
                            print(f"  ⏭️  Column {col_name} already exists or error: {e}")
                    else:
                        print(f"  ⏭️  Column {col_name} already exists")
        except Exception as e:
            print(f"  ❌ Error creating user_preferences table: {e}")
        
        connection.close()
        print("\n✅ Database migration completed!")
        print("\n💡 Next steps:")
        print("   1. Restart your Flask application")
        print("   2. Test the new preferences page at /preferences")
        print("   3. Send a notification to see ML use the new features")

if __name__ == '__main__':
    migrate_database()
