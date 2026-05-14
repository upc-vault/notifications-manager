"""API endpoints for managing user notification preferences"""
from flask import Blueprint, request, jsonify
from src.models.user import User, db
from src.models.user_preferences import UserPreferences
from src.services.auth_service import token_required
from datetime import time
import logging

logger = logging.getLogger(__name__)

preferences_bp = Blueprint('preferences', __name__, url_prefix='/api/v1/preferences')


@preferences_bp.route('/', methods=['GET'])
@token_required
def get_preferences(current_user):
    """Get user's notification preferences"""
    try:
        prefs = UserPreferences.query.filter_by(user_id=current_user.id).first()
        
        # Create default if doesn't exist
        if not prefs:
            prefs = UserPreferences(user_id=current_user.id)
            db.session.add(prefs)
            db.session.commit()
        
        return jsonify({
            "success": True,
            "preferences": {
                # Quiet Hours
                "quiet_hours_enabled": prefs.quiet_hours_enabled,
                "quiet_hours_start": prefs.quiet_hours_start.strftime("%H:%M") if prefs.quiet_hours_start else None,
                "quiet_hours_end": prefs.quiet_hours_end.strftime("%H:%M") if prefs.quiet_hours_end else None,
                
                # Rate Limiting
                "max_notifications_per_day": prefs.max_notifications_per_day,
                "max_notifications_per_hour": prefs.max_notifications_per_hour,
                
                # Channel Preferences
                "preferred_channels": prefs.preferred_channels or [],
                "email_enabled": prefs.email_enabled,
                "sms_enabled": prefs.sms_enabled,
                "push_enabled": prefs.push_enabled,
                "whatsapp_enabled": prefs.whatsapp_enabled,
                
                # Content Preferences
                "marketing_opt_in": prefs.marketing_opt_in,
                "promotional_opt_in": prefs.promotional_opt_in,
                "prefer_short_messages": prefs.prefer_short_messages,
                "prefer_rich_content": prefs.prefer_rich_content,
                
                # Visual Preferences
                "high_contrast_mode": prefs.high_contrast_mode,
                "large_text_mode": prefs.large_text_mode
            }
        }), 200
    except Exception as e:
        logger.error(f"Error getting preferences: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@preferences_bp.route('/', methods=['PUT'])
@token_required
def update_preferences(current_user):
    """Update user's notification preferences"""
    try:
        data = request.get_json()
        
        prefs = UserPreferences.query.filter_by(user_id=current_user.id).first()
        if not prefs:
            prefs = UserPreferences(user_id=current_user.id)
            db.session.add(prefs)
        
        # Update quiet hours
        if 'quiet_hours_enabled' in data:
            prefs.quiet_hours_enabled = data['quiet_hours_enabled']
        if 'quiet_hours_start' in data:
            if data['quiet_hours_start']:
                hour, minute = map(int, data['quiet_hours_start'].split(':'))
                prefs.quiet_hours_start = time(hour, minute)
            else:
                prefs.quiet_hours_start = None
        if 'quiet_hours_end' in data:
            if data['quiet_hours_end']:
                hour, minute = map(int, data['quiet_hours_end'].split(':'))
                prefs.quiet_hours_end = time(hour, minute)
            else:
                prefs.quiet_hours_end = None
        
        # Update rate limiting
        if 'max_notifications_per_day' in data:
            prefs.max_notifications_per_day = data['max_notifications_per_day']
        if 'max_notifications_per_hour' in data:
            prefs.max_notifications_per_hour = data['max_notifications_per_hour']
        
        # Update channel preferences
        if 'preferred_channels' in data:
            prefs.preferred_channels = data['preferred_channels']
        if 'email_enabled' in data:
            prefs.email_enabled = data['email_enabled']
        if 'sms_enabled' in data:
            prefs.sms_enabled = data['sms_enabled']
        if 'push_enabled' in data:
            prefs.push_enabled = data['push_enabled']
        if 'whatsapp_enabled' in data:
            prefs.whatsapp_enabled = data['whatsapp_enabled']
        
        # Update content preferences
        if 'marketing_opt_in' in data:
            prefs.marketing_opt_in = data['marketing_opt_in']
        if 'promotional_opt_in' in data:
            prefs.promotional_opt_in = data['promotional_opt_in']
        if 'prefer_short_messages' in data:
            prefs.prefer_short_messages = data['prefer_short_messages']
        if 'prefer_rich_content' in data:
            prefs.prefer_rich_content = data['prefer_rich_content']
        
        # Update visual preferences
        if 'high_contrast_mode' in data:
            prefs.high_contrast_mode = data['high_contrast_mode']
        if 'large_text_mode' in data:
            prefs.large_text_mode = data['large_text_mode']
        
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Preferences updated successfully"
        }), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating preferences: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@preferences_bp.route('/quiet-hours', methods=['POST'])
@token_required
def set_quiet_hours(current_user):
    """Set quiet hours for Do Not Disturb"""
    try:
        data = request.get_json()
        
        if not all(k in data for k in ['enabled', 'start', 'end']):
            return jsonify({
                "success": False,
                "error": "Missing required fields: enabled, start, end"
            }), 400
        
        prefs = UserPreferences.query.filter_by(user_id=current_user.id).first()
        if not prefs:
            prefs = UserPreferences(user_id=current_user.id)
            db.session.add(prefs)
        
        prefs.quiet_hours_enabled = data['enabled']
        
        if data['start']:
            hour, minute = map(int, data['start'].split(':'))
            prefs.quiet_hours_start = time(hour, minute)
        
        if data['end']:
            hour, minute = map(int, data['end'].split(':'))
            prefs.quiet_hours_end = time(hour, minute)
        
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Quiet hours updated",
            "quiet_hours": {
                "enabled": prefs.quiet_hours_enabled,
                "start": prefs.quiet_hours_start.strftime("%H:%M") if prefs.quiet_hours_start else None,
                "end": prefs.quiet_hours_end.strftime("%H:%M") if prefs.quiet_hours_end else None
            }
        }), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error setting quiet hours: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@preferences_bp.route('/channels', methods=['GET'])
@token_required
def get_channel_preferences(current_user):
    """Get user's channel preferences"""
    try:
        prefs = UserPreferences.query.filter_by(user_id=current_user.id).first()
        if not prefs:
            prefs = UserPreferences(user_id=current_user.id)
            db.session.add(prefs)
            db.session.commit()
        
        enabled_channels = prefs.get_preferred_channels()
        
        return jsonify({
            "success": True,
            "channels": {
                "email": {
                    "enabled": prefs.email_enabled,
                    "priority": enabled_channels.index('email') + 1 if 'email' in enabled_channels else None
                },
                "sms": {
                    "enabled": prefs.sms_enabled,
                    "priority": enabled_channels.index('sms') + 1 if 'sms' in enabled_channels else None
                },
                "push": {
                    "enabled": prefs.push_enabled,
                    "priority": enabled_channels.index('push') + 1 if 'push' in enabled_channels else None
                },
                "whatsapp": {
                    "enabled": prefs.whatsapp_enabled,
                    "priority": enabled_channels.index('whatsapp') + 1 if 'whatsapp' in enabled_channels else None
                }
            },
            "preferred_order": enabled_channels
        }), 200
    except Exception as e:
        logger.error(f"Error getting channel preferences: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@preferences_bp.route('/channels', methods=['PUT'])
@token_required
def update_channel_preferences(current_user):
    """Update user's channel preferences"""
    try:
        data = request.get_json()
        
        prefs = UserPreferences.query.filter_by(user_id=current_user.id).first()
        if not prefs:
            prefs = UserPreferences(user_id=current_user.id)
            db.session.add(prefs)
        
        # Update individual channel toggles
        if 'email_enabled' in data:
            prefs.email_enabled = data['email_enabled']
        if 'sms_enabled' in data:
            prefs.sms_enabled = data['sms_enabled']
        if 'push_enabled' in data:
            prefs.push_enabled = data['push_enabled']
        if 'whatsapp_enabled' in data:
            prefs.whatsapp_enabled = data['whatsapp_enabled']
        
        # Update preferred order
        if 'preferred_order' in data:
            prefs.preferred_channels = data['preferred_order']
        
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Channel preferences updated"
        }), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating channel preferences: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500
