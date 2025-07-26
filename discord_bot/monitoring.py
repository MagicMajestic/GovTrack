# GovTracker2 Python Migration by Replit Agent
import logging
import re
from datetime import datetime, timedelta
from models.curator import Curator
from models.discord_server import DiscordServer
from models.activity import Activity
from models.response_tracking import ResponseTracking
from database import db
from app import app
from config import Config
import asyncio

class MessageMonitor:
    def __init__(self, bot):
        self.bot = bot
        self.keywords = ['куратор', 'curator', 'help', 'помощь']
        self.pending_responses = {}  # Track messages waiting for curator responses
        
    def start_monitoring(self):
        """Start monitoring tasks"""
        logging.info("Message monitoring started")
        
        # Start cleanup task for old pending responses
        asyncio.create_task(self.cleanup_pending_responses())
    
    async def process_message(self, message):
        """Process incoming Discord message"""
        try:
            with app.app_context():
                # Find server in database
                server = DiscordServer.find_by_server_id(str(message.guild.id))
                if not server or not server.is_active:
                    return
                
                # Find or create curator
                curator = Curator.find_by_discord_id(str(message.author.id))
                if not curator:
                    # Auto-create curator if they're active in tracked server
                    curator = Curator(
                        discord_id=str(message.author.id),
                        name=message.author.display_name,
                        curator_type='auto_created'
                    )
                    db.session.add(curator)
                    db.session.flush()  # Get the ID
                
                # Check if this is a help request
                content_lower = message.content.lower()
                is_help_request = any(keyword in content_lower for keyword in self.keywords)
                
                if is_help_request:
                    await self.handle_help_request(message, server)
                
                # Check if this is a response to a help request
                if message.reference and message.reference.message_id:
                    await self.handle_response_message(message, curator, server)
                
                # Record general message activity
                activity = Activity(
                    curator_id=curator.id,
                    server_id=server.id,
                    type='message',
                    content=message.content[:500],  # Limit content length
                    points=Config.RATING_POINTS['message'],
                    message_id=str(message.id),
                    channel_id=str(message.channel.id)
                )
                
                db.session.add(activity)
                
                # Update curator points
                curator.total_points += activity.points
                
                # Recalculate rating
                from utils.rating import calculate_curator_rating
                rating_data = calculate_curator_rating(curator.id)
                curator.rating_level = rating_data['level']
                
                db.session.commit()
                
                logging.debug(f"Processed message from {curator.name} in {server.name}")
        
        except Exception as e:
            logging.error(f"Error processing message: {e}")
            db.session.rollback()
    
    async def handle_help_request(self, message, server):
        """Handle help request message"""
        try:
            # Store pending response for tracking
            self.pending_responses[str(message.id)] = {
                'timestamp': datetime.utcnow(),
                'server_id': server.id,
                'channel_id': str(message.channel.id),
                'author_id': str(message.author.id)
            }
            
            logging.info(f"Help request detected in {server.name}: {message.content[:100]}")
            
            # Notify curators if role is configured
            if server.role_tag_id:
                await self.notify_curators(message, server)
        
        except Exception as e:
            logging.error(f"Error handling help request: {e}")
    
    async def handle_response_message(self, message, curator, server):
        """Handle response to help request"""
        try:
            # Get the original message
            original_message_id = str(message.reference.message_id)
            
            if original_message_id in self.pending_responses:
                pending = self.pending_responses[original_message_id]
                
                # Calculate response time
                response_time = datetime.utcnow() - pending['timestamp']
                response_seconds = int(response_time.total_seconds())
                
                # Record response tracking
                response_tracking = ResponseTracking(
                    curator_id=curator.id,
                    server_id=server.id,
                    mention_timestamp=pending['timestamp'],
                    response_timestamp=datetime.utcnow(),
                    response_time_seconds=response_seconds,
                    mention_message_id=original_message_id,
                    response_message_id=str(message.id),
                    channel_id=str(message.channel.id),
                    trigger_keywords=','.join(self.keywords)
                )
                
                db.session.add(response_tracking)
                
                # Record reply activity with bonus points
                reply_activity = Activity(
                    curator_id=curator.id,
                    server_id=server.id,
                    type='reply',
                    content=message.content[:500],
                    points=Config.RATING_POINTS['reply'],
                    message_id=str(message.id),
                    channel_id=str(message.channel.id)
                )
                
                db.session.add(reply_activity)
                
                # Update curator points
                curator.total_points += reply_activity.points
                
                # Remove from pending responses
                del self.pending_responses[original_message_id]
                
                db.session.commit()
                
                logging.info(f"Response tracked: {curator.name} responded in {response_seconds}s")
        
        except Exception as e:
            logging.error(f"Error handling response message: {e}")
            db.session.rollback()
    
    async def process_reaction(self, reaction, user, action):
        """Process reaction add/remove"""
        try:
            with app.app_context():
                # Find server and curator
                server = DiscordServer.find_by_server_id(str(reaction.message.guild.id))
                if not server or not server.is_active:
                    return
                
                curator = Curator.find_by_discord_id(str(user.id))
                if not curator:
                    # Auto-create curator
                    curator = Curator(
                        discord_id=str(user.id),
                        name=user.display_name,
                        curator_type='auto_created'
                    )
                    db.session.add(curator)
                    db.session.flush()
                
                # Only track reaction additions for points
                if action == 'add':
                    activity = Activity(
                        curator_id=curator.id,
                        server_id=server.id,
                        type='reaction',
                        content=f"Reacted with {reaction.emoji}",
                        points=Config.RATING_POINTS['reaction'],
                        message_id=str(reaction.message.id),
                        channel_id=str(reaction.message.channel.id)
                    )
                    
                    db.session.add(activity)
                    curator.total_points += activity.points
                    
                    # Recalculate rating
                    from utils.rating import calculate_curator_rating
                    rating_data = calculate_curator_rating(curator.id)
                    curator.rating_level = rating_data['level']
                    
                    db.session.commit()
                    
                    logging.debug(f"Reaction tracked: {curator.name} in {server.name}")
        
        except Exception as e:
            logging.error(f"Error processing reaction: {e}")
            db.session.rollback()
    
    async def process_message_edit(self, before, after):
        """Process message edits"""
        # Currently just log edits, could be extended for activity tracking
        logging.debug(f"Message edited by {after.author.display_name}")
    
    async def process_message_delete(self, message):
        """Process message deletions"""
        # Remove from pending responses if it was a help request
        if str(message.id) in self.pending_responses:
            del self.pending_responses[str(message.id)]
            logging.debug(f"Removed deleted message from pending responses")
    
    async def notify_curators(self, message, server):
        """Notify curators about help request"""
        try:
            if not server.role_tag_id:
                return
            
            # Get the role
            guild = message.guild
            role = guild.get_role(int(server.role_tag_id))
            
            if not role:
                logging.warning(f"Role {server.role_tag_id} not found in {guild.name}")
                return
            
            # Send notification
            notification_text = f"{role.mention} Help requested in {message.channel.mention}"
            
            # Try to send in the same channel
            try:
                await message.channel.send(notification_text)
            except Exception as e:
                logging.error(f"Could not send notification: {e}")
        
        except Exception as e:
            logging.error(f"Error notifying curators: {e}")
    
    async def cleanup_pending_responses(self):
        """Clean up old pending responses"""
        while True:
            try:
                current_time = datetime.utcnow()
                expired_responses = []
                
                for message_id, pending in self.pending_responses.items():
                    # Remove responses older than 1 hour
                    if (current_time - pending['timestamp']).total_seconds() > 3600:
                        expired_responses.append(message_id)
                
                for message_id in expired_responses:
                    del self.pending_responses[message_id]
                
                if expired_responses:
                    logging.info(f"Cleaned up {len(expired_responses)} expired pending responses")
                
                # Wait 5 minutes before next cleanup
                await asyncio.sleep(300)
            
            except Exception as e:
                logging.error(f"Error in cleanup task: {e}")
                await asyncio.sleep(60)  # Wait 1 minute on error
