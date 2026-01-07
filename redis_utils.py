#!/usr/bin/env python3
"""Utility script for backing up and restoring Redis data."""
import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

from src.services.redis_service import redis_service


async def backup_redis(output_file: str):
    """
    Backup all Redis data to a JSON file.
    
    Args:
        output_file: Path to output JSON file
    """
    print(f"🔄 Backing up Redis data to {output_file}")
    
    await redis_service.connect()
    
    try:
        # Get all channels
        channels = await redis_service.get_all_channels()
        
        backup_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "channels_count": len(channels),
            "channels": []
        }
        
        # Get config for each channel
        for channel_id in channels:
            config = await redis_service.get_channel_config(channel_id)
            if config:
                backup_data["channels"].append(config)
        
        # Save to file
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Backup completed successfully!")
        print(f"   Channels backed up: {len(channels)}")
        print(f"   File: {output_path.absolute()}")
        
    except Exception as e:
        print(f"❌ Backup failed: {e}")
        sys.exit(1)
    finally:
        await redis_service.disconnect()


async def restore_redis(input_file: str, overwrite: bool = False):
    """
    Restore Redis data from a JSON backup file.
    
    Args:
        input_file: Path to input JSON file
        overwrite: If True, overwrite existing channels
    """
    print(f"🔄 Restoring Redis data from {input_file}")
    
    input_path = Path(input_file)
    
    if not input_path.exists():
        print(f"❌ File not found: {input_file}")
        sys.exit(1)
    
    # Load backup data
    with open(input_path, 'r', encoding='utf-8') as f:
        backup_data = json.load(f)
    
    print(f"   Backup from: {backup_data['timestamp']}")
    print(f"   Channels to restore: {backup_data['channels_count']}")
    
    if not overwrite:
        confirm = input("   This will add channels. Continue? (y/n): ")
        if confirm.lower() != 'y':
            print("❌ Restore cancelled")
            sys.exit(0)
    
    await redis_service.connect()
    
    try:
        restored = 0
        skipped = 0
        
        for channel_config in backup_data["channels"]:
            channel_id = channel_config["channel_id"]
            
            # Check if channel already exists
            exists = await redis_service.is_channel_monitored(channel_id)
            
            if exists and not overwrite:
                print(f"   ⏭️  Skipping existing channel: {channel_id}")
                skipped += 1
                continue
            
            # Add or update channel
            success = await redis_service.add_channel(
                channel_id=channel_id,
                config=channel_config
            )
            
            if success:
                print(f"   ✅ Restored channel: {channel_id}")
                restored += 1
            else:
                print(f"   ❌ Failed to restore channel: {channel_id}")
        
        print(f"\n✅ Restore completed!")
        print(f"   Restored: {restored}")
        print(f"   Skipped: {skipped}")
        
    except Exception as e:
        print(f"❌ Restore failed: {e}")
        sys.exit(1)
    finally:
        await redis_service.disconnect()


async def list_channels():
    """List all monitored channels with their configs."""
    print("📋 Listing all monitored channels")
    
    await redis_service.connect()
    
    try:
        channels = await redis_service.get_all_channels()
        
        if not channels:
            print("   No channels configured")
            return
        
        print(f"   Total channels: {len(channels)}\n")
        
        for i, channel_id in enumerate(channels, 1):
            config = await redis_service.get_channel_config(channel_id)
            
            print(f"{i}. Channel ID: {channel_id}")
            if config:
                print(f"   Enabled: {config.get('enabled', True)}")
                if config.get('custom_prompt'):
                    print(f"   Custom prompt: Yes")
            print()
        
    except Exception as e:
        print(f"❌ Failed to list channels: {e}")
        sys.exit(1)
    finally:
        await redis_service.disconnect()


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python redis_utils.py backup <output_file>")
        print("  python redis_utils.py restore <input_file> [--overwrite]")
        print("  python redis_utils.py list")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "backup":
        if len(sys.argv) < 3:
            output_file = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        else:
            output_file = sys.argv[2]
        
        asyncio.run(backup_redis(output_file))
    
    elif command == "restore":
        if len(sys.argv) < 3:
            print("❌ Please specify input file")
            sys.exit(1)
        
        input_file = sys.argv[2]
        overwrite = "--overwrite" in sys.argv
        
        asyncio.run(restore_redis(input_file, overwrite))
    
    elif command == "list":
        asyncio.run(list_channels())
    
    else:
        print(f"❌ Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
