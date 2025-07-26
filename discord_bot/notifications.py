# GovTracker2 Python Migration by Replit Agent
import discord
import logging
from datetime import datetime
from models.curator import Curator
from models.discord_server import DiscordServer
from app import app

class NotificationManager:
    def __init__(self, bot):
        self.bot = bot
        
    async def send_curator_notification(self, server_id, message, role_id=None):
        """Send notification to curators in a specific server"""
        try:
            guild = self.bot.get_guild(server_id)
            if not guild:
                logging.warning(f"Guild {server_id} not found")
                return False
            
            # Get default channel (usually general or first text channel)
            channel = None
            for ch in guild.text_channels:
                if ch.permissions_for(guild.me).send_messages:
                    channel = ch
                    break
            
            if not channel:
                logging.warning(f"No suitable channel found in {guild.name}")
                return False
            
            # Prepare notification message
            notification_content = message
            
            if role_id:
                role = guild.get_role(role_id)
                if role:
                    notification_content = f"{role.mention} {message}"
            
            # Send notification
            await channel.send(notification_content)
            logging.info(f"Notification sent to {guild.name}: {message}")
            return True
            
        except Exception as e:
            logging.error(f"Error sending notification: {e}")
            return False
    
    async def send_system_notification(self, message, notification_type="info"):
        """Send system notification to all tracked servers"""
        try:
            sent_count = 0
            
            with app.app_context():
                servers = DiscordServer.get_active_servers()
                
                for server in servers:
                    guild = self.bot.get_guild(int(server.server_id))
                    if not guild:
                        continue
                    
                    # Create embed for system notification
                    color = {
                        'info': discord.Color.blue(),
                        'warning': discord.Color.orange(),
                        'error': discord.Color.red(),
                        'success': discord.Color.green()
                    }.get(notification_type, discord.Color.blue())
                    
                    embed = discord.Embed(
                        title="GovTracker2 System Notification",
                        description=message,
                        color=color,
                        timestamp=datetime.utcnow()
                    )
                    
                    embed.set_footer(text="GovTracker2 Python Migration by Replit Agent")
                    
                    # Find suitable channel
                    channel = None
                    for ch in guild.text_channels:
                        if ch.permissions_for(guild.me).send_messages:
                            channel = ch
                            break
                    
                    if channel:
                        try:
                            await channel.send(embed=embed)
                            sent_count += 1
                        except Exception as e:
                            logging.error(f"Failed to send to {guild.name}: {e}")
            
            logging.info(f"System notification sent to {sent_count} servers")
            return sent_count > 0
            
        except Exception as e:
            logging.error(f"Error sending system notification: {e}")
            return False
    
    async def send_backup_notification(self, backup_info, success=True):
        """Send backup completion notification"""
        try:
            if success:
                message = f"✅ Backup completed successfully!\n"
                message += f"**Backup ID:** {backup_info.get('id', 'Unknown')}\n"
                message += f"**Size:** {backup_info.get('size', 'Unknown')} bytes\n"
                message += f"**Tables:** {backup_info.get('tables_count', 'Unknown')}\n"
                message += f"**Created:** {backup_info.get('created_at', 'Unknown')}"
                notification_type = "success"
            else:
                message = f"❌ Backup failed!\n"
                message += f"**Error:** {backup_info.get('error', 'Unknown error')}\n"
                message += f"**Time:** {datetime.utcnow().isoformat()}"
                notification_type = "error"
            
            await self.send_system_notification(message, notification_type)
            
        except Exception as e:
            logging.error(f"Error sending backup notification: {e}")
    
    async def send_curator_update_notification(self, curator_id, update_type, details=None):
        """Send notification about curator updates"""
        try:
            with app.app_context():
                curator = Curator.query.get(curator_id)
                if not curator:
                    return False
                
                messages = {
                    'level_up': f"🎉 {curator.name} leveled up to {curator.rating_level}!",
                    'milestone': f"🏆 {curator.name} reached {curator.total_points} points!",
                    'achievement': f"⭐ {curator.name} earned an achievement!"
                }
                
                message = messages.get(update_type, f"📢 Update for {curator.name}")
                
                if details:
                    message += f"\n{details}"
                
                # Send to servers where curator is active
                servers = DiscordServer.get_active_servers()
                for server in servers:
                    # Check if curator has activity in this server
                    recent_activity = curator.activities.filter_by(server_id=server.id).first()
                    if recent_activity:
                        await self.send_curator_notification(
                            int(server.server_id),
                            message,
                            int(server.role_tag_id) if server.role_tag_id else None
                        )
                
                return True
                
        except Exception as e:
            logging.error(f"Error sending curator update notification: {e}")
            return False
    
    async def send_daily_report(self):
        """Send daily activity report"""
        try:
            with app.app_context():
                from datetime import timedelta
                from sqlalchemy import func
                from models.activity import Activity
                
                # Get yesterday's statistics
                yesterday = datetime.utcnow() - timedelta(days=1)
                today = datetime.utcnow()
                
                daily_stats = db.session.query(
                    func.count(Activity.id).label('total_activities'),
                    func.count(Activity.curator_id.distinct()).label('active_curators'),
                    func.sum(Activity.points).label('total_points')
                ).filter(
                    Activity.timestamp >= yesterday,
                    Activity.timestamp < today
                ).first()
                
                # Get top curator of the day
                top_curator_data = db.session.query(
                    Activity.curator_id,
                    func.sum(Activity.points).label('daily_points')
                ).filter(
                    Activity.timestamp >= yesterday,
                    Activity.timestamp < today
                ).group_by(Activity.curator_id).order_by(
                    func.sum(Activity.points).desc()
                ).first()
                
                top_curator_name = "None"
                if top_curator_data:
                    top_curator = Curator.query.get(top_curator_data.curator_id)
                    if top_curator:
                        top_curator_name = f"{top_curator.name} ({top_curator_data.daily_points} pts)"
                
                # Create report message
                report = f"📊 **Daily Activity Report**\n"
                report += f"**Date:** {yesterday.strftime('%Y-%m-%d')}\n"
                report += f"**Total Activities:** {daily_stats.total_activities or 0}\n"
                report += f"**Active Curators:** {daily_stats.active_curators or 0}\n"
                report += f"**Total Points Earned:** {daily_stats.total_points or 0}\n"
                report += f"**Top Curator:** {top_curator_name}\n"
                
                await self.send_system_notification(report, "info")
                
                return True
                
        except Exception as e:
            logging.error(f"Error sending daily report: {e}")
            return False
    
    async def send_error_notification(self, error_message, context="System"):
        """Send error notification to administrators"""
        try:
            message = f"🚨 **Error in {context}**\n"
            message += f"**Error:** {error_message}\n"
            message += f"**Time:** {datetime.utcnow().isoformat()}\n"
            message += f"**Action Required:** Please check the logs for more details."
            
            await self.send_system_notification(message, "error")
            
        except Exception as e:
            logging.error(f"Error sending error notification: {e}")
    
    async def send_maintenance_notification(self, maintenance_type, scheduled_time=None):
        """Send maintenance notification"""
        try:
            if maintenance_type == "start":
                message = "🔧 **Maintenance Started**\n"
                message += "The GovTracker2 system is currently undergoing maintenance.\n"
                message += "Some features may be temporarily unavailable."
            
            elif maintenance_type == "end":
                message = "✅ **Maintenance Completed**\n"
                message += "The GovTracker2 system is now fully operational.\n"
                message += "Thank you for your patience!"
            
            elif maintenance_type == "scheduled":
                message = "📅 **Scheduled Maintenance Notice**\n"
                message += f"Maintenance is scheduled for: {scheduled_time}\n"
                message += "Please save your work and expect brief service interruption."
            
            else:
                message = f"🔧 **Maintenance Notification**\n{maintenance_type}"
            
            await self.send_system_notification(message, "warning")
            
        except Exception as e:
            logging.error(f"Error sending maintenance notification: {e}")
