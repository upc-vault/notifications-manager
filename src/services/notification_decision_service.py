"""
Notification Decision Service
Uses ML models to decide template, channel, and priority
"""
import sys
from pathlib import Path
from typing import Dict, Tuple, Optional, List
from dataclasses import dataclass

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.ml.sleeping_bandit import SleepingMultiArmedBandit, Template
from src.ml.tug_of_war import TugOfWarChannelSelector, Channel
from src.models.user_profile import UserProfile, BankingTier
from src.utils.redis_client import redis_client


@dataclass
class NotificationDecision:
    """Result of notification decision"""
    template_id: str
    template_name: str
    channel: str
    priority: str
    priority_score: int
    user_affinity: float
    confidence: float
    reasoning: str


class NotificationDecisionService:
    """
    Service that uses ML models to make intelligent notification decisions
    """
    
    def __init__(self):
        """Initialize decision service with ML models"""
        print("Initializing Notification Decision Service...")
        
        # Templates will be loaded from database dynamically
        self.templates = []
        
        # Initialize channels
        self.channels = [
            Channel.PUSH,
            Channel.EMAIL,
            Channel.SMS,
            Channel.WHATSAPP,
            Channel.WEBPUSH
        ]
        
        # Initialize ML models (per-user instances will be cached)
        self.bandit_models = {}
        self.tow_models = {}
        
        print("✓ Notification Decision Service initialized")
    
    def _load_templates_from_db(self) -> List[Template]:
        """
        Load active templates from database
        
        Returns:
            List of Template objects for ML algorithm
        """
        try:
            from src.models.notification_template import NotificationTemplate
            
            # Get all active templates from database
            db_templates = NotificationTemplate.query.filter_by(is_active=True).all()
            
            if not db_templates:
                print("⚠️  No templates found in database, using fallback templates")
                # Fallback templates if database is empty
                return [
                    Template("fallback_info", "Informational", "Information about your account."),
                    Template("fallback_alert", "Alert", "Important alert notification.")
                ]
            
            # Convert database templates to ML Template objects
            ml_templates = []
            for db_template in db_templates:
                ml_templates.append(Template(
                    id=str(db_template.id),  # Use database ID
                    name=db_template.name,
                    content=db_template.description or db_template.name,
                    is_available=True
                ))
            
            print(f"✓ Loaded {len(ml_templates)} templates from database")
            return ml_templates
            
        except Exception as e:
            print(f"⚠️  Error loading templates from database: {e}")
            # Fallback templates
            return [
                Template("fallback_info", "Informational", "Information about your account."),
                Template("fallback_alert", "Alert", "Important alert notification.")
            ]
    
    def _get_or_create_user_models(self, user: UserProfile) -> Tuple[SleepingMultiArmedBandit, TugOfWarChannelSelector]:
        """
        Get or create ML models for a user (cached in Redis)
        
        Args:
            user: User profile
            
        Returns:
            Tuple of (bandit, tow_selector)
        """
        # Check cache first
        cache_key = f"ml_models:{user.user_id}"
        cached = redis_client.get(cache_key)
        
        if cached:
            return cached
        
        # Load fresh templates from database
        templates = self._load_templates_from_db()
        
        # Create new models
        bandit = SleepingMultiArmedBandit(templates, epsilon=0.1, decay_rate=0.995)
        tow = TugOfWarChannelSelector(self.channels, pull_strength=0.05)
        
        # Cache for 1 hour
        redis_client.set(cache_key, (bandit, tow), ttl=3600)
        
        return bandit, tow
    
    def _calculate_priority(
        self, 
        template_id: str, 
        notification_type: Optional[str],
        user: UserProfile
    ) -> Tuple[str, int]:
        """
        Calculate notification priority based on notification type and user tier
        
        Priority rules by notification_type:
        Priority rules by notification_type:
        - urgent, security: CRITICAL (1)
        - transactional, important: HIGH (2)
        - informative: MEDIUM (3)
        - promotional, marketing: LOW (4)
        
        Adjusted by user tier:
        - Patrimonial/Private: +1 priority level
        
        Args:
            template_id: Selected template
            notification_type: Type of notification (urgent, informative, promotional, etc.)
            user: User profile
            
        Returns:
            Tuple of (priority_name, priority_score)
        """
        # Base priority by notification type
        type_priority_map = {
            "urgent": ("critical", 1),
            "security": ("critical", 1),
            "transactional": ("high", 2),
            "important": ("high", 2),
            "informative": ("medium", 3),
            "informational": ("medium", 3),
            "promotional": ("low", 4),
            "marketing": ("low", 4),
        }
        
        # Use notification_type if provided, otherwise default to medium
        priority_name, score = type_priority_map.get(
            notification_type.lower() if notification_type else "informative",
            ("medium", 3)
        )
        
        # Upgrade priority for high-value customers
        if user.banking_tier in [BankingTier.PRIVATE, BankingTier.PATRIMONIAL]:
            if score > 1:  # Don't upgrade critical
                score -= 1
                if score == 1:
                    priority_name = "critical"
                elif score == 2:
                    priority_name = "high"
                elif score == 3:
                    priority_name = "medium"
        
        return priority_name, score
    
    def decide(
        self, 
        user: UserProfile,
        message_type: Optional[str] = None,
        context: Optional[Dict] = None
    ) -> NotificationDecision:
        """
        Make intelligent notification decision using ML models
        
        Args:
            user: User profile with preferences and behavior
            message_type: Notification type (urgent, informative, promotional, etc.)
            context: Optional context data (time, location, etc.)
            
        Returns:
            NotificationDecision with template, channel, priority
        """
        # Get or create user's ML models (loads fresh templates from database)
        bandit, tow = self._get_or_create_user_models(user)
        
        # Get current templates (in case they were updated)
        current_templates = self._load_templates_from_db()
        
        # Load user preferences if available
        user_preferences = self._load_user_preferences(user.user_id)
        
        # Check if notification can be sent based on preferences
        if user_preferences:
            can_send, reason = user_preferences.can_send_notification(message_type)
            if not can_send and message_type not in ['urgent', 'security', 'transactional']:
                # Return decision with reasoning about why we can't send
                # For non-critical notifications, respect user preferences
                print(f"⚠️  Cannot send notification: {reason}")
        
        # Set template availability based on user preferences
        if user_preferences:
            if not user_preferences.marketing_opt_in or not user_preferences.promotional_opt_in:
                # Disable promotional templates
                for template in current_templates:
                    try:
                        from src.models.notification_template import NotificationTemplate
                        db_template = NotificationTemplate.query.get(int(template.id))
                        if db_template and db_template.notification_type == 'promotional':
                            bandit.set_template_availability(template.id, False)
                    except:
                        pass
        
        # 1. Select template using Sleeping Bandit
        selected_template_id = bandit.select_template()
        template = next((t for t in current_templates if t.id == selected_template_id), current_templates[0])
        
        # 2. Determine disabled channels based on context and preferences
        disabled_channels = self._get_disabled_channels(user, user_preferences, message_type, context)
        
        # 3. Select channel using Tug of War (with disabled channels)
        selected_channel = tow.select_channel(context=context, disabled_channels=disabled_channels)
        
        # 4. Calculate user affinities
        template_affinity = user.get_template_affinity(selected_template_id)
        channel_affinity = user.get_channel_affinity(selected_channel.value)
        combined_affinity = (template_affinity + channel_affinity) / 2
        
        # 5. Calculate priority based on notification_type (not template)
        priority_name, priority_score = self._calculate_priority(
            selected_template_id, 
            message_type,  # Use message_type for priority calculation
            user
        )
        
        # 6. Calculate confidence (based on epsilon and affinities)
        confidence = combined_affinity * (1 - bandit.epsilon)
        
        # 7. Generate reasoning
        reasoning = self._generate_reasoning(
            user, 
            template.name, 
            selected_channel.value,
            priority_name,
            template_affinity,
            channel_affinity,
            disabled_channels,
            user_preferences
        )
        
        # 8. Cache decision
        decision_cache_key = f"decision:{user.user_id}:latest"
        decision = NotificationDecision(
            template_id=selected_template_id,
            template_name=template.name,
            channel=selected_channel.value,
            priority=priority_name,
            priority_score=priority_score,
            user_affinity=combined_affinity,
            confidence=confidence,
            reasoning=reasoning
        )
        redis_client.set(decision_cache_key, decision, ttl=300)  # 5 minutes
        
        return decision
    
    def _load_user_preferences(self, user_id: str):
        """Load user preferences from database"""
        try:
            from src.models.user_preferences import UserPreferences
            from src.models.user import User, db
            
            # Find user by username (user_id in UserProfile is actually username)
            user = User.query.filter_by(username=user_id).first()
            if user:
                # Get or create preferences
                prefs = UserPreferences.query.filter_by(user_id=user.id).first()
                if not prefs:
                    prefs = UserPreferences(user_id=user.id)
                    db.session.add(prefs)
                    db.session.commit()
                return prefs
            return None
        except Exception as e:
            print(f"⚠️  Error loading user preferences: {e}")
            return None
    
    def _get_disabled_channels(self, user: UserProfile, user_preferences, message_type: str, context: Optional[Dict]) -> List[str]:
        """
        Determine which channels should be disabled based on user preferences,
        time of day, quiet hours, and context
        
        Returns:
            List of channel names to disable
        """
        disabled = []
        
        if not user_preferences:
            return disabled
        
        # Check each channel's opt-in status
        if not user_preferences.email_enabled:
            disabled.append('email')
        if not user_preferences.sms_enabled:
            disabled.append('sms')
        if not user_preferences.push_enabled:
            disabled.append('push')
        if not user_preferences.webpush_enabled:
            disabled.append('webpush')
        if not user_preferences.whatsapp_enabled:
            disabled.append('whatsapp')
        
        # Check quiet hours for non-critical notifications
        if message_type not in ['urgent', 'security', 'transactional']:
            if user_preferences.is_in_quiet_hours():
                # During quiet hours, only allow silent channels
                # Disable noisy channels: SMS, Push, WhatsApp
                disabled.extend(['sms', 'push', 'whatsapp'])
        
        # Time-based channel selection
        from datetime import datetime
        
        try:
            # Get user's local time (simplified - using datetime without pytz for now)
            local_time = datetime.now().time()
            hour = local_time.hour
            
            # Night time (22:00 - 06:00) - prefer silent channels
            if hour >= 22 or hour < 6:
                if message_type not in ['urgent', 'security']:
                    # Disable intrusive channels at night
                    disabled.extend(['sms', 'push', 'whatsapp'])
            
            # Business hours (09:00 - 18:00) - all channels OK
            # Off hours (18:00 - 22:00) - prefer less intrusive
            elif hour >= 18 and hour < 22:
                if message_type in ['promotional', 'marketing']:
                    # Promotional messages less intrusive in evening
                    disabled.extend(['sms', 'push'])
                    
        except Exception as e:
            print(f"⚠️  Error in time-based channel selection: {e}")
        
        # Remove duplicates
        return list(set(disabled))
    
    def _generate_reasoning(
        self, 
        user: UserProfile,
        template_name: str,
        channel: str,
        priority: str,
        template_affinity: float,
        channel_affinity: float,
        disabled_channels: List[str] = None,
        user_preferences = None
    ) -> str:
        """Generate human-readable reasoning for decision"""
        reasons = []
        
        # User segment
        reasons.append(f"User {user.banking_tier.value.upper()}")
        
        # Age factor
        if user.age < 30:
            reasons.append("young tech-savvy")
        elif user.age > 60:
            reasons.append("senior user")
        
        # Digital adoption
        if user.digital_adoption > 0.8:
            reasons.append(f"high digital adoption ({user.digital_adoption:.0%})")
        elif user.digital_adoption < 0.5:
            reasons.append(f"low digital adoption ({user.digital_adoption:.0%})")
        
        # Template selection with ML info
        reasons.append(f"Template '{template_name}' selected by Sleeping Bandit (affinity {template_affinity:.2f})")
        
        # Channel selection with ML info
        channel_reason = f"Channel '{channel}' selected by Tug of War (affinity {channel_affinity:.2f})"
        if disabled_channels:
            channel_reason += f" | Excluded: {', '.join(disabled_channels)}"
        reasons.append(channel_reason)
        
        # Quiet hours info
        if user_preferences and user_preferences.is_in_quiet_hours():
            reasons.append("Quiet hours active - silent channels preferred")
        
        # Priority
        reasons.append(f"Priority {priority.upper()}")
        
        return " | ".join(reasons)
    
    def update_feedback(
        self, 
        user_id: str,
        template_id: str,
        channel: str,
        success: bool,
        opened: bool = False,
        clicked: bool = False
    ) -> bool:
        """
        Update ML models with user feedback
        
        Args:
            user_id: User ID
            template_id: Template used
            channel: Channel used
            success: Whether notification was delivered
            opened: Whether user opened notification
            clicked: Whether user clicked notification
            
        Returns:
            True if updated successfully
        """
        try:
            # Get user's models from cache
            cache_key = f"ml_models:{user_id}"
            models = redis_client.get(cache_key)
            
            if not models:
                print(f"No models found for user {user_id}")
                return False
            
            bandit, tow = models
            
            # Calculate reward for bandit
            if clicked:
                reward = 1.0
            elif opened:
                reward = 0.6
            elif success:
                reward = 0.3
            else:
                reward = 0.0
            
            # Update bandit
            bandit.update_reward(template_id, reward)
            
            # Update TOW
            channel_enum = Channel[channel.upper()]
            tow.update_result(channel_enum, success)
            
            # Save updated models
            redis_client.set(cache_key, (bandit, tow), ttl=3600)
            
            return True
            
        except Exception as e:
            print(f"Error updating feedback: {e}")
            return False


# Global instance
decision_service = NotificationDecisionService()
