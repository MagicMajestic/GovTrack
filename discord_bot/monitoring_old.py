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
        self.notification_tasks = {}  # Track active notification tasks
        
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
                
                # Check if this is a help request (from any user)
                content_lower = message.content.lower()
                is_help_request = any(keyword in content_lower for keyword in self.keywords)
                
                # Also check for role mentions
                if server.curator_role_id:
                    role_mentioned = f"<@&{server.curator_role_id}>" in message.content
                    is_help_request = is_help_request or role_mentioned
                
                if is_help_request:
                    await self.handle_help_request(message, server)
                
                # Find curator (only track activities for known curators)
                curator = Curator.query.filter_by(discord_id=str(message.author.id)).first()
                if not curator:
                    return  # Skip tracking for unknown users
                
                # Check if this is a response to a help request
                if message.reference and message.reference.message_id:
                    await self.handle_response_message(message, curator, server)
                    return  # Don't double-count as both reply and message
                
                # Record general message activity
                activity = Activity()
                activity.curator_id = curator.id
                activity.server_id = server.id
                activity.type = 'message'
                activity.content = message.content[:500]  # Limit content length
                activity.points = Config.RATING_POINTS['message']
                activity.message_id = str(message.id)
                activity.channel_id = str(message.channel.id)
                
                db.session.add(activity)
                
                # Update curator points
                curator.total_points += activity.points
                
                # Recalculate rating
                from utils.rating import calculate_curator_rating
                rating_data = calculate_curator_rating(curator.id)
                curator.rating_level = rating_data['level']
                
                db.session.commit()
                
                logging.info(f"Message tracked: {curator.name} posted in {server.name} - points: {activity.points}")
        
        except Exception as e:
            logging.error(f"Error processing message: {e}")
            try:
                with app.app_context():
                    db.session.rollback()
            except:
                pass
    
    async def handle_help_request(self, message, server):
        """Handle help request message"""
        try:
            message_id = str(message.id)
            
            # Prevent duplicate help request handling
            if message_id in self.pending_responses:
                return  # Already processing this message
            
            # Store pending response for tracking
            self.pending_responses[message_id] = {
                'timestamp': datetime.utcnow(),
                'server_id': server.id,
                'channel_id': str(message.channel.id),
                'author_id': str(message.author.id)
            }
            
            logging.info(f"Help request detected in {server.name}: {message.content[:100]}")
            
            # Notify curators if role is configured (start async task)
            if server.curator_role_id and message_id not in self.notification_tasks:
                task = asyncio.create_task(self.notify_curators(message, server))
                self.notification_tasks[message_id] = task
        
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
                response_tracking = ResponseTracking()
                response_tracking.curator_id = curator.id
                response_tracking.server_id = server.id
                response_tracking.mention_timestamp = pending['timestamp']
                response_tracking.response_timestamp = datetime.utcnow()
                response_tracking.response_time_seconds = response_seconds
                response_tracking.mention_message_id = original_message_id
                response_tracking.response_message_id = str(message.id)
                response_tracking.channel_id = str(message.channel.id)
                response_tracking.trigger_keywords = ','.join(self.keywords)
                
                db.session.add(response_tracking)
                
                # Don't record reply activity separately - it's already tracked as response
                
                # Remove from pending responses and cancel notifications
                del self.pending_responses[original_message_id]
                if original_message_id in self.notification_tasks:
                    self.notification_tasks[original_message_id].cancel()
                    del self.notification_tasks[original_message_id]
                
                # Update curator rating
                from utils.rating import calculate_curator_rating
                rating_data = calculate_curator_rating(curator.id)
                curator.rating_level = rating_data['level']
                
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
                
                curator = Curator.query.filter_by(discord_id=str(user.id)).first()
                if not curator:
                    # Auto-create curator
                    curator = Curator()
                    curator.discord_id = str(user.id)
                    curator.name = user.display_name
                    curator.curator_type = 'auto_created'
                    db.session.add(curator)
                    db.session.flush()
                
                # Only track reaction additions for points
                if action == 'add':
                    # Check if this reaction is on a help request
                    message_id = str(reaction.message.id)
                    is_help_response = message_id in self.pending_responses
                    
                    if is_help_response:
                        # This is a reaction to a help request - record as response
                        pending = self.pending_responses[message_id]
                        response_time = datetime.utcnow() - pending['timestamp']
                        response_seconds = int(response_time.total_seconds())
                        
                        # Record response tracking
                        response_tracking = ResponseTracking()
                        response_tracking.curator_id = curator.id
                        response_tracking.server_id = server.id
                        response_tracking.mention_timestamp = pending['timestamp']
                        response_tracking.response_timestamp = datetime.utcnow()
                        response_tracking.response_time_seconds = response_seconds
                        response_tracking.mention_message_id = message_id
                        response_tracking.response_message_id = f"reaction_{reaction.emoji}"
                        response_tracking.channel_id = str(reaction.message.channel.id)
                        response_tracking.trigger_keywords = ','.join(self.keywords)
                        
                        db.session.add(response_tracking)
                        
                        # Remove from pending responses FIRST to stop notifications
                        del self.pending_responses[message_id]
                        
                        # Update curator rating
                        from utils.rating import calculate_curator_rating
                        rating_data = calculate_curator_rating(curator.id)
                        curator.rating_level = rating_data['level']
                        
                        db.session.commit()
                        
                        logging.info(f"Reaction tracked: {curator.name} reacted with {reaction.emoji} in {server.name}")
                        logging.info(f"Response tracked: {curator.name} responded in {response_seconds}s")
                        
                        # Don't record this as general reaction activity - it's already a response
                        return
                    
                    # Record general reaction activity
                    activity = Activity()
                    activity.curator_id = curator.id
                    activity.server_id = server.id
                    activity.type = 'reaction'
                    activity.content = f"Reacted with {reaction.emoji}"
                    activity.points = Config.RATING_POINTS['reaction']
                    activity.message_id = str(reaction.message.id)
                    activity.channel_id = str(reaction.message.channel.id)
                    
                    db.session.add(activity)
                    curator.total_points += activity.points
                    
                    # Recalculate rating
                    from utils.rating import calculate_curator_rating
                    rating_data = calculate_curator_rating(curator.id)
                    curator.rating_level = rating_data['level']
                    
                    db.session.commit()
        
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
        """Notify curators about help request with repeating reminders"""
        try:
            if not server.curator_role_id:
                return
            
            # Get notification settings - refresh server data from DB
            with app.app_context():
                fresh_server = DiscordServer.find_by_server_id(str(message.guild.id))
                if not fresh_server:
                    return
                reminder_interval = fresh_server.reminder_interval_seconds or 300  # Default 5 minutes
                auto_reminder_enabled = fresh_server.auto_reminder_enabled if fresh_server.auto_reminder_enabled is not None else True
                
            logging.info(f"Using reminder interval: {reminder_interval}s, auto-reminder: {auto_reminder_enabled}")
            
            # Get the role
            guild = message.guild
            role = guild.get_role(int(server.curator_role_id))
            
            if not role:
                logging.warning(f"Role {server.curator_role_id} not found in {guild.name}")
                return
            
            # Start reminder loop
            elapsed_time = 0
            reminder_count = 0
            
            while True:
                # Wait for the reminder interval
                await asyncio.sleep(reminder_interval)
                elapsed_time += reminder_interval
                reminder_count += 1
                
                # Check if the message was already responded to
                if str(message.id) not in self.pending_responses:
                    logging.info(f"Help request {message.id} was answered, stopping reminders")
                    return  # Already responded to
                
                # Format elapsed time
                minutes = elapsed_time // 60
                seconds = elapsed_time % 60
                if minutes > 0:
                    time_text = f"{minutes} минут {seconds} секунд" if seconds > 0 else f"{minutes} минут"
                else:
                    time_text = f"{seconds} секунд"
                
                # Send notification
                notification_text = f"⚠️ {role.mention} Запрос помощи без ответа уже {time_text}!\n" \
                                  f"Сообщение: {message.jump_url}"
                
                try:
                    await message.channel.send(notification_text)
                    logging.info(f"Reminder #{reminder_count} sent for message {message.id} after {elapsed_time}s")
                except Exception as e:
                    logging.error(f"Could not send reminder: {e}")
                    return
                
                # If auto reminder is disabled, send only one notification
                if not auto_reminder_enabled:
                    logging.info(f"Auto reminder disabled, sent single notification for {message.id}")
                    return
        
        except Exception as e:
            logging.error(f"Error in curator notification loop: {e}")
        except asyncio.CancelledError:
            logging.info(f"Notification task cancelled for message {message.id}")
            return
    
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
    
    async def process_reaction(self, reaction, user, action):
        """Process reaction add/remove"""
        try:
            with app.app_context():
                # Find server in database
                server = DiscordServer.find_by_server_id(str(reaction.message.guild.id))
                if not server or not server.is_active:
                    return
                
                # Find curator (only track known curators)
                curator = Curator.query.filter_by(discord_id=str(user.id)).first()
                if not curator:
                    return
                
                # Only track reaction additions for points
                if action == 'add':
                    # Check if this reaction is on a help request
                    message_id = str(reaction.message.id)
                    is_help_response = message_id in self.pending_responses
                    
                    if is_help_response:
                        # This is a reaction to a help request - record as response
                        pending = self.pending_responses[message_id]
                        response_time = datetime.utcnow() - pending['timestamp']
                        response_seconds = int(response_time.total_seconds())
                        
                        # Record response tracking
                        response_tracking = ResponseTracking()
                        response_tracking.curator_id = curator.id
                        response_tracking.server_id = server.id
                        response_tracking.mention_timestamp = pending['timestamp']
                        response_tracking.response_timestamp = datetime.utcnow()
                        response_tracking.response_time_seconds = response_seconds
                        response_tracking.mention_message_id = message_id
                        response_tracking.response_message_id = f"reaction_{reaction.emoji}"
                        response_tracking.channel_id = str(reaction.message.channel.id)
                        response_tracking.trigger_keywords = ','.join(self.keywords)
                        
                        db.session.add(response_tracking)
                        
                        # Remove from pending responses FIRST to stop notifications
                        del self.pending_responses[message_id]
                        
                        # Update curator rating
                        from utils.rating import calculate_curator_rating
                        rating_data = calculate_curator_rating(curator.id)
                        curator.rating_level = rating_data['level']
                        
                        db.session.commit()
                        
                        logging.info(f"Reaction tracked: {curator.name} reacted with {reaction.emoji} in {server.name}")
                        logging.info(f"Response tracked: {curator.name} responded in {response_seconds}s")
                        
                        # Don't record this as general reaction activity - it's already a response
                        return
                    
                    # Record general reaction activity only if it's not a help response
                    activity = Activity()
                    activity.curator_id = curator.id
                    activity.server_id = server.id
                    activity.type = 'reaction'
                    activity.content = f"Reacted with {reaction.emoji}"
                    activity.points = Config.RATING_POINTS['reaction']
                    activity.message_id = str(reaction.message.id)
                    activity.channel_id = str(reaction.message.channel.id)
                    
                    db.session.add(activity)
                    curator.total_points += activity.points
                    
                    # Recalculate rating
                    from utils.rating import calculate_curator_rating
                    rating_data = calculate_curator_rating(curator.id)
                    curator.rating_level = rating_data['level']
                    
                    db.session.commit()
        
        except Exception as e:
            logging.error(f"Error processing reaction: {e}")
            try:
                with app.app_context():
                    db.session.rollback()
            except:
                pass
