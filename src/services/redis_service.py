"""Redis service for managing channel configurations."""
import json
import logging
from typing import List, Optional, Dict, Any
import redis.asyncio as redis
from config.settings import settings

logger = logging.getLogger(__name__)


class RedisService:
    """Service for Redis operations."""
    
    CHANNEL_KEY_PREFIX = "channel:"
    CHANNELS_SET_KEY = "channels:all"
    
    def __init__(self):
        """Initialize Redis connection."""
        self.redis: Optional[redis.Redis] = None
    
    async def connect(self):
        """Establish Redis connection."""
        try:
            self.redis = await redis.from_url(
                f"redis://{settings.redis_host}:{settings.redis_port}/{settings.redis_db}",
                password=settings.redis_password,
                encoding="utf-8",
                decode_responses=True
            )
            await self.redis.ping()
            logger.info("Connected to Redis successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    async def disconnect(self):
        """Close Redis connection."""
        if self.redis:
            await self.redis.close()
            logger.info("Disconnected from Redis")
    
    async def add_channel(self, channel_id: int, config: Optional[Dict[str, Any]] = None) -> bool:
        """
        Add channel to monitoring.
        
        Args:
            channel_id: Telegram channel ID
            config: Optional channel-specific configuration
        
        Returns:
            True if added successfully
        """
        try:
            channel_key = f"{self.CHANNEL_KEY_PREFIX}{channel_id}"
            
            # Default config
            channel_config = {
                "channel_id": channel_id,
                "enabled": True,
                "custom_prompt": None,
                **(config or {})
            }
            
            # Save channel config
            await self.redis.set(
                channel_key,
                json.dumps(channel_config)
            )
            
            # Add to channels set
            await self.redis.sadd(self.CHANNELS_SET_KEY, str(channel_id))
            
            logger.info(f"Added channel {channel_id} to monitoring")
            return True
        except Exception as e:
            logger.error(f"Failed to add channel {channel_id}: {e}")
            return False
    
    async def remove_channel(self, channel_id: int) -> bool:
        """
        Remove channel from monitoring.
        
        Args:
            channel_id: Telegram channel ID
        
        Returns:
            True if removed successfully
        """
        try:
            channel_key = f"{self.CHANNEL_KEY_PREFIX}{channel_id}"
            
            # Remove channel config
            await self.redis.delete(channel_key)
            
            # Remove from channels set
            await self.redis.srem(self.CHANNELS_SET_KEY, str(channel_id))
            
            logger.info(f"Removed channel {channel_id} from monitoring")
            return True
        except Exception as e:
            logger.error(f"Failed to remove channel {channel_id}: {e}")
            return False
    
    async def get_channel_config(self, channel_id: int) -> Optional[Dict[str, Any]]:
        """
        Get channel configuration.
        
        Args:
            channel_id: Telegram channel ID
        
        Returns:
            Channel config or None if not found
        """
        try:
            channel_key = f"{self.CHANNEL_KEY_PREFIX}{channel_id}"
            config_json = await self.redis.get(channel_key)
            
            if config_json:
                return json.loads(config_json)
            return None
        except Exception as e:
            logger.error(f"Failed to get config for channel {channel_id}: {e}")
            return None
    
    async def update_channel_config(
        self, 
        channel_id: int, 
        updates: Dict[str, Any]
    ) -> bool:
        """
        Update channel configuration.
        
        Args:
            channel_id: Telegram channel ID
            updates: Config fields to update
        
        Returns:
            True if updated successfully
        """
        try:
            config = await self.get_channel_config(channel_id)
            if not config:
                logger.warning(f"Channel {channel_id} not found")
                return False
            
            config.update(updates)
            
            channel_key = f"{self.CHANNEL_KEY_PREFIX}{channel_id}"
            await self.redis.set(channel_key, json.dumps(config))
            
            logger.info(f"Updated config for channel {channel_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to update channel {channel_id}: {e}")
            return False
    
    async def get_all_channels(self) -> List[int]:
        """
        Get list of all monitored channels.
        
        Returns:
            List of channel IDs
        """
        try:
            channel_ids = await self.redis.smembers(self.CHANNELS_SET_KEY)
            return [int(cid) for cid in channel_ids]
        except Exception as e:
            logger.error(f"Failed to get all channels: {e}")
            return []
    
    async def is_channel_monitored(self, channel_id: int) -> bool:
        """
        Check if channel is being monitored.
        
        Args:
            channel_id: Telegram channel ID
        
        Returns:
            True if channel is monitored
        """
        try:
            return await self.redis.sismember(
                self.CHANNELS_SET_KEY, 
                str(channel_id)
            )
        except Exception as e:
            logger.error(f"Failed to check channel {channel_id}: {e}")
            return False


# Global instance
redis_service = RedisService()
