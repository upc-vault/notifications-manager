"""
Tug of War (TOW) Algorithm
Used to dynamically select the optimal notification channel based on performance.
Channels compete in a 'tug of war' fashion based on their success rates.
"""
import numpy as np
from typing import List, Dict, Optional
from dataclasses import dataclass
from enum import Enum


class Channel(Enum):
    """Available notification channels"""
    PUSH = "push"
    EMAIL = "email"
    SMS = "sms"
    WHATSAPP = "whatsapp"
    WEBPUSH = "webpush"


@dataclass
class ChannelStats:
    """Statistics for a notification channel"""
    channel: Channel
    position: float  # Position in tug of war (-1 to 1)
    successes: int = 0
    failures: int = 0
    total_attempts: int = 0
    success_rate: float = 0.0
    

class TugOfWarChannelSelector:
    """
    Tug of War algorithm for dynamic channel selection.
    
    Channels are positioned on a line (-1 to 1). When a channel succeeds,
    it pulls towards the center (position 0). The channel closest to center
    is selected most often.
    """
    
    def __init__(self, channels: List[Channel], 
                 pull_strength: float = 0.1,
                 position_weight: float = 0.7,
                 performance_weight: float = 0.3):
        """
        Initialize the Tug of War selector.
        
        Args:
            channels: List of available channels
            pull_strength: How much a success/failure moves the position (0-1)
            position_weight: Weight given to current position in selection (0-1)
            performance_weight: Weight given to historical performance (0-1)
        """
        self.channels = channels
        self.pull_strength = pull_strength
        self.position_weight = position_weight
        self.performance_weight = performance_weight
        
        # Initialize channel statistics
        # Start all channels at equal spacing from -1 to 1
        n = len(channels)
        positions = np.linspace(-1, 1, n)
        
        self.stats = {
            ch: ChannelStats(
                channel=ch,
                position=pos
            )
            for ch, pos in zip(channels, positions)
        }
        
        self.total_selections = 0
        
    def select_channel(self, context: Optional[Dict] = None, disabled_channels: Optional[List[str]] = None) -> Channel:
        """
        Select a channel using Tug of War positioning.
        
        Channels closer to position 0 (center) are more likely to be selected.
        Can exclude channels based on context (quiet hours, user preferences, etc.)
        
        Args:
            context: Optional context (user preferences, time, urgency, etc.)
            disabled_channels: List of channel names to exclude from selection
            
        Returns:
            Selected channel
        """
        # Filter out disabled channels
        available_channels = {}
        for channel, stats in self.stats.items():
            # Skip if channel is explicitly disabled
            if disabled_channels and channel.value in disabled_channels:
                continue
            available_channels[channel] = stats
        
        # If no channels available (all disabled), use all channels (emergency fallback)
        if not available_channels:
            available_channels = self.stats
        
        # Calculate selection probabilities based on position and performance
        probabilities = {}
        
        for channel, stats in available_channels.items():
            # Position score: channels closer to 0 (center) score higher
            position_score = 1.0 - abs(stats.position)
            
            # Performance score: based on historical success rate
            if stats.total_attempts > 0:
                performance_score = stats.success_rate
            else:
                performance_score = 0.5  # Neutral for untested channels
            
            # Combined score
            score = (self.position_weight * position_score + 
                    self.performance_weight * performance_score)
            
            probabilities[channel] = score
        
        # Normalize to probabilities
        total = sum(probabilities.values())
        probabilities = {ch: score/total for ch, score in probabilities.items()}
        
        # Select channel based on probabilities
        selected = np.random.choice(
            list(probabilities.keys()),
            p=list(probabilities.values())
        )
        
        self.total_selections += 1
        return selected
    
    def update_result(self, channel: Channel, success: bool):
        """
        Update channel statistics after a notification attempt.
        
        Args:
            channel: The channel that was used
            success: Whether the notification was successful (delivered, opened, clicked)
        """
        stats = self.stats[channel]
        stats.total_attempts += 1
        
        if success:
            stats.successes += 1
            # Pull towards center (position 0)
            if stats.position > 0:
                stats.position = max(0, stats.position - self.pull_strength)
            else:
                stats.position = min(0, stats.position + self.pull_strength)
        else:
            stats.failures += 1
            # Push away from center
            if stats.position >= 0:
                stats.position = min(1, stats.position + self.pull_strength)
            else:
                stats.position = max(-1, stats.position - self.pull_strength)
        
        # Update success rate
        stats.success_rate = stats.successes / stats.total_attempts
    
    def get_statistics(self) -> Dict:
        """Get current statistics for all channels"""
        return {
            'total_selections': self.total_selections,
            'channels': [
                {
                    'channel': stats.channel.value,
                    'position': stats.position,
                    'successes': stats.successes,
                    'failures': stats.failures,
                    'total_attempts': stats.total_attempts,
                    'success_rate': stats.success_rate
                }
                for stats in sorted(self.stats.values(), 
                                   key=lambda s: s.position)
            ]
        }
    
    def get_best_channel(self) -> Channel:
        """Get the channel with best position (closest to 0)"""
        return min(self.stats.keys(), key=lambda ch: abs(self.stats[ch].position))
    
    def reset_positions(self):
        """Reset all channels to initial positions"""
        n = len(self.channels)
        positions = np.linspace(-1, 1, n)
        
        for ch, pos in zip(self.channels, positions):
            self.stats[ch].position = pos
