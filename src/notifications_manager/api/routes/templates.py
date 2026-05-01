"""
Template management API routes blueprint
"""
from flask import Blueprint, request, jsonify
import uuid
import logging

logger = logging.getLogger(__name__)

templates_bp = Blueprint('templates', __name__)


def init_template_routes(analytics_db):
    """Initialize routes with service dependencies"""
    
    @templates_bp.route('/api/v1/templates', methods=['GET'])
    def get_templates():
        """Get all templates"""
        try:
            templates = analytics_db.get_all_templates()
            return jsonify(templates), 200
        except Exception as e:
            logger.error(f"Error getting templates: {e}")
            return jsonify({'error': str(e)}), 500

    @templates_bp.route('/api/v1/templates', methods=['POST'])
    def create_template():
        """Create a new template"""
        try:
            data = request.get_json()
            
            template_id = str(uuid.uuid4())
            
            success = analytics_db.create_template(
                template_id=template_id,
                name=data.get('name'),
                template_type=data.get('type'),
                channels=data.get('channels', []),
                title=data.get('title'),
                body=data.get('body'),
                email_html=data.get('email_html'),
                variables=data.get('variables', [])
            )
            
            if success:
                return jsonify({'id': template_id, 'message': 'Template created'}), 201
            else:
                return jsonify({'error': 'Failed to create template'}), 500
        except Exception as e:
            logger.error(f"Error creating template: {e}")
            return jsonify({'error': str(e)}), 500

    @templates_bp.route('/api/v1/templates/<template_id>', methods=['GET'])
    def get_template(template_id):
        """Get a specific template"""
        try:
            template = analytics_db.get_template(template_id)
            if template:
                return jsonify(template), 200
            else:
                return jsonify({'error': 'Template not found'}), 404
        except Exception as e:
            logger.error(f"Error getting template: {e}")
            return jsonify({'error': str(e)}), 500

    @templates_bp.route('/api/v1/templates/<template_id>', methods=['PUT'])
    def update_template(template_id):
        """Update a template"""
        try:
            data = request.get_json()
            
            success = analytics_db.update_template(
                template_id=template_id,
                name=data.get('name'),
                template_type=data.get('type'),
                channels=data.get('channels', []),
                title=data.get('title'),
                body=data.get('body'),
                email_html=data.get('email_html'),
                variables=data.get('variables', [])
            )
            
            if success:
                return jsonify({'message': 'Template updated'}), 200
            else:
                return jsonify({'error': 'Failed to update template'}), 500
        except Exception as e:
            logger.error(f"Error updating template: {e}")
            return jsonify({'error': str(e)}), 500

    @templates_bp.route('/api/v1/templates/<template_id>', methods=['DELETE'])
    def delete_template(template_id):
        """Delete a template"""
        try:
            success = analytics_db.delete_template(template_id)
            if success:
                return jsonify({'message': 'Template deleted'}), 200
            else:
                return jsonify({'error': 'Failed to delete template'}), 500
        except Exception as e:
            logger.error(f"Error deleting template: {e}")
            return jsonify({'error': str(e)}), 500
    
    return templates_bp
