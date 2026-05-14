"""
Transfer Service - Handles money transfers with ML-powered notifications
"""
import logging
from decimal import Decimal
from typing import Dict, Any, Optional, Tuple
from datetime import datetime

from src.models.user import db, User
from src.models.transfer import Transfer
from src.services.notification_decision_service import decision_service

logger = logging.getLogger(__name__)


class TransferService:
    """Service for handling P2P money transfers with intelligent notifications"""
    
    def create_transfer(self, sender_username: str, receiver_username: str, 
                       amount: float, description: str = None) -> Tuple[Optional[Transfer], Optional[str]]:
        """
        Create a new money transfer
        
        Args:
            sender_username: Username of sender
            receiver_username: Username of receiver
            amount: Amount to transfer
            description: Optional description
        
        Returns:
            Tuple of (Transfer object, error message)
        """
        try:
            # Validate amount
            if amount <= 0:
                return None, "Amount must be greater than zero"
            
            if amount > 999999.99:
                return None, "Amount exceeds maximum limit"
            
            # Find sender
            sender = User.query.filter(
                (User.username == sender_username) | (User.email == sender_username)
            ).first()
            
            if not sender:
                return None, f"Sender not found: {sender_username}"
            
            # Find receiver
            receiver = User.query.filter(
                (User.username == receiver_username) | (User.email == receiver_username)
            ).first()
            
            if not receiver:
                return None, f"Receiver not found: {receiver_username}"
            
            # Prevent self-transfer
            if sender.id == receiver.id:
                return None, "Cannot transfer money to yourself"
            
            # Create transfer
            transfer = Transfer(
                sender_id=sender.id,
                receiver_id=receiver.id,
                amount=amount,
                description=description
            )
            
            db.session.add(transfer)
            db.session.commit()
            
            logger.info(f"✓ Transfer created: {transfer.reference_number} - ${amount} from {sender.username} to {receiver.username}")
            
            return transfer, None
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"❌ Failed to create transfer: {e}")
            return None, str(e)
    
    def process_transfer(self, transfer_id: int, send_notification: bool = True) -> Tuple[bool, Optional[str]]:
        """
        Process a pending transfer and send ML-powered notification
        
        Args:
            transfer_id: Transfer ID
            send_notification: Whether to send notification to receiver
        
        Returns:
            Tuple of (success, error message)
        """
        try:
            transfer = Transfer.query.get(transfer_id)
            
            if not transfer:
                return False, "Transfer not found"
            
            if transfer.status != 'pending':
                return False, f"Transfer already {transfer.status}"
            
            # Update status to processing
            transfer.status = 'processing'
            db.session.commit()
            
            # Simulate payment processing (in real system, this would integrate with payment gateway)
            # For demo purposes, we'll mark it as completed immediately
            
            transfer.complete()
            db.session.commit()
            
            logger.info(f"✓ Transfer processed: {transfer.reference_number}")
            
            # Send notification to receiver using ML decision
            if send_notification:
                self._send_transfer_notification(transfer)
            
            return True, None
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"❌ Failed to process transfer: {e}")
            return False, str(e)
    
    def _send_transfer_notification(self, transfer: Transfer):
        """
        Send notification to receiver using ML-powered decision system
        
        Args:
            transfer: Transfer object
        """
        try:
            receiver = transfer.receiver
            sender = transfer.sender
            
            # Build notification data
            notification_data = {
                "user_id": receiver.username,
                "event_type": "money_received",
                "priority": "high",
                "data": {
                    "title": f"💰 Money Received!",
                    "body": f"You received ${transfer.amount} from {sender.full_name or sender.username}",
                    "amount": float(transfer.amount),
                    "sender": sender.username,
                    "sender_name": sender.full_name or sender.username,
                    "reference": transfer.reference_number,
                    "description": transfer.description,
                    "timestamp": transfer.completed_at.isoformat() if transfer.completed_at else None
                },
                "template_type": "URGENT",  # Money notifications are typically urgent
                "metadata": {
                    "transfer_id": transfer.id,
                    "reference_number": transfer.reference_number,
                    "event": "money_received"
                }
            }
            
            # Use ML decision service to send notification
            decision_service.decide_and_notify(notification_data)
            
            logger.info(f"✓ Transfer notification sent to {receiver.username} via ML decision")
            
        except Exception as e:
            logger.error(f"❌ Failed to send transfer notification: {e}")
    
    def get_user_transfers(self, username: str, transfer_type: str = 'all', 
                          limit: int = 50, offset: int = 0) -> Tuple[list, int]:
        """
        Get transfers for a user
        
        Args:
            username: Username
            transfer_type: 'sent', 'received', or 'all'
            limit: Max results
            offset: Pagination offset
        
        Returns:
            Tuple of (list of transfers, total count)
        """
        try:
            # Find user
            user = User.query.filter(
                (User.username == username) | (User.email == username)
            ).first()
            
            if not user:
                return [], 0
            
            # Build query based on type
            if transfer_type == 'sent':
                query = Transfer.query.filter_by(sender_id=user.id)
            elif transfer_type == 'received':
                query = Transfer.query.filter_by(receiver_id=user.id)
            else:  # 'all'
                query = Transfer.query.filter(
                    (Transfer.sender_id == user.id) | (Transfer.receiver_id == user.id)
                )
            
            # Get total count
            total = query.count()
            
            # Get paginated results
            transfers = query.order_by(Transfer.created_at.desc()).limit(limit).offset(offset).all()
            
            return transfers, total
            
        except Exception as e:
            logger.error(f"❌ Failed to get user transfers: {e}")
            return [], 0
    
    def get_transfer(self, transfer_id: int) -> Optional[Transfer]:
        """Get transfer by ID"""
        return Transfer.query.get(transfer_id)
    
    def get_transfer_by_reference(self, reference_number: str) -> Optional[Transfer]:
        """Get transfer by reference number"""
        return Transfer.query.filter_by(reference_number=reference_number).first()


# Create singleton instance
transfer_service = TransferService()
