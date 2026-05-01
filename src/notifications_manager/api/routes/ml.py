"""
ML/AI API routes for recommendations and feedback
"""
from flask import Blueprint, request, jsonify
import logging
import uuid

logger = logging.getLogger(__name__)

ml_bp = Blueprint('ml', __name__)


def init_ml_routes(decision_service, analytics_db):
    """Initialize ML routes with dependencies"""
    
    @ml_bp.route('/api/v1/ml/recommend-template', methods=['POST'])
    def recommend_template():
        """Get AI template recommendation for a user"""
        try:
            data = request.get_json()
            user_id = data.get('user_id')
            context = data.get('context', {})
            
            if not user_id:
                return jsonify({'success': False, 'error': 'user_id required'}), 400
            
            # Build context for template selection
            selection_context = {
                'notification_type': 'general',
                'user_segment': 'standard',
                'priority': 'medium',
                'time_of_day': 'afternoon',
                **context
            }
            
            # Get template recommendation from ML model
            selected_template = decision_service.template_bandit.select_template(selection_context)
            
            # Get all template scores for visualization
            all_scores = []
            for template_name in decision_service.template_bandit.arms.keys():
                arm = decision_service.template_bandit.arms[template_name]
                context_bonus = decision_service.template_bandit._calculate_context_bonus(
                    template_name,
                    selection_context
                )
                score = decision_service.template_bandit.get_ucb_score(arm, context_bonus)
                all_scores.append({
                    'template': template_name.value,
                    'score': score
                })
            
            # Sort by score descending
            all_scores.sort(key=lambda x: x['score'], reverse=True)
            
            # Get decision metadata
            template_stats = {}
            for template_name, arm in decision_service.template_bandit.arms.items():
                template_stats[template_name.value] = {
                    'pulls': arm.total_pulls,
                    'wins': arm.success_count,
                    'win_rate': arm.success_rate
                }
            
            # Determine strategy (exploration vs exploitation)
            # If selected template is not the one with highest win rate, it's exploration
            # Use template value (string) as tiebreaker to avoid enum comparison
            templates_by_rate = sorted(
                decision_service.template_bandit.arms.items(),
                key=lambda x: (x[1].success_rate, x[0].value),
                reverse=True
            )
            best_template_by_rate = templates_by_rate[0][0].value if templates_by_rate else selected_template.value
            selected_template_str = selected_template.value if hasattr(selected_template, 'value') else selected_template
            strategy = 'exploration' if selected_template_str != best_template_by_rate else 'exploitation'
            
            return jsonify({
                'success': True,
                'template': selected_template_str,
                'scores': all_scores,
                'strategy': strategy,
                'decision_metadata': {
                    'template_pulls': {t: s['pulls'] for t, s in template_stats.items()},
                    'template_wins': {t: s['wins'] for t, s in template_stats.items()},
                    'template_rates': {t: s['win_rate'] for t, s in template_stats.items()}
                },
                'context': context
            }), 200
        
        except Exception as e:
            logger.error(f"Error getting recommendation: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @ml_bp.route('/api/v1/ml/feedback', methods=['POST'])
    def submit_feedback():
        """Submit user feedback for ML learning"""
        try:
            data = request.get_json()
            user_id = data.get('user_id')
            template = data.get('template')
            channel = data.get('channel', 'webpush')
            engagement = data.get('engagement', 0.0)
            demo_mode = data.get('demo_mode', False)
            
            if not user_id or not template:
                return jsonify({'success': False, 'error': 'user_id and template required'}), 400
            
            # Determine success based on engagement
            success = engagement > 0.5
            
            # Submit feedback to ML models
            decision_service.update_feedback(
                template=template,
                channel=channel,
                success=success,
                engagement=engagement
            )
            
            # Log to analytics if not demo mode
            if not demo_mode:
                notification_id = str(uuid.uuid4())
                analytics_db.log_notification(
                    notification_id=notification_id,
                    user_id=user_id,
                    template=template,
                    channel=channel,
                    title='Demo Notification',
                    body='AI Intelligence Demo',
                    metadata={'demo': True, 'engagement': engagement}
                )
                
                if engagement > 0.5:
                    analytics_db.log_click(notification_id, engagement)
            
            # Get updated stats
            updated_stats = {}
            for template_name, arm in decision_service.template_bandit.arms.items():
                updated_stats[template_name.value] = {
                    'pulls': arm.total_pulls,
                    'wins': arm.success_count,
                    'win_rate': arm.success_rate
                }
            
            return jsonify({
                'success': True,
                'message': 'Feedback recorded',
                'updated_stats': updated_stats
            }), 200
        
        except Exception as e:
            logger.error(f"Error submitting feedback: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'error': str(e)}), 500
    
    return ml_bp
