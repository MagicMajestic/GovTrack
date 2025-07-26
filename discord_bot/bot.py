# GovTracker2 Python Migration by Replit Agent
import discord
from discord.ext import commands
import os
import logging
import asyncio
from datetime import datetime
from models.curator import Curator
from models.discord_server import DiscordServer
from models.activity import Activity
from models.response_tracking import ResponseTracking
from database import db
from app import app
from .monitoring import MessageMonitor
from .notifications import NotificationManager

# Configure Discord logging
discord.utils.setup_logging(level=logging.INFO)

# Bot configuration
intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
intents.guilds = True
intents.members = True

class GovTrackerBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix='!gt',
            intents=intents,
            help_command=None
        )
        
        self.monitor = MessageMonitor(self)
        self.notification_manager = NotificationManager(self)
        self.tracked_servers = {}
        
    async def setup_hook(self):
        """Called when the bot is starting up"""
        logging.info("GovTracker2 Bot is starting up...")
        
        # Load tracked servers from database
        await self.load_tracked_servers()
        
        # Start monitoring tasks
        self.monitor.start_monitoring()
        
        logging.info("Bot setup completed")
    
    async def load_tracked_servers(self):
        """Load tracked servers from database"""
        try:
            with app.app_context():
                servers = DiscordServer.get_active_servers()
                
                for server in servers:
                    self.tracked_servers[int(server.server_id)] = {
                        'id': server.id,
                        'name': server.name,
                        'role_tag_id': server.role_tag_id,
                        'is_active': server.is_active
                    }
                
                logging.info(f"Loaded {len(self.tracked_servers)} tracked servers")
        
        except Exception as e:
            logging.error(f"Error loading tracked servers: {e}")
    
    async def on_ready(self):
        """Called when bot is ready"""
        logging.info(f'{self.user} has connected to Discord!')
        logging.info(f'Bot is in {len(self.guilds)} guilds')
        
        # Set bot status
        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name=f"{len(self.tracked_servers)} servers"
        )
        await self.change_presence(activity=activity)
    
    async def on_guild_join(self, guild):
        """Called when bot joins a new guild"""
        logging.info(f"Joined guild: {guild.name} ({guild.id})")
        
        # Check if this server should be tracked
        with app.app_context():
            server = DiscordServer.find_by_server_id(str(guild.id))
            if server and server.is_active:
                self.tracked_servers[guild.id] = {
                    'id': server.id,
                    'name': server.name,
                    'role_tag_id': server.role_tag_id,
                    'is_active': server.is_active
                }
                logging.info(f"Now tracking server: {guild.name}")
    
    async def on_guild_remove(self, guild):
        """Called when bot leaves a guild"""
        logging.info(f"Left guild: {guild.name} ({guild.id})")
        
        if guild.id in self.tracked_servers:
            del self.tracked_servers[guild.id]
    
    async def on_message(self, message):
        """Handle incoming messages"""
        # Ignore bot messages
        if message.author.bot:
            return
        
        # Only process messages from tracked servers
        if message.guild and message.guild.id in self.tracked_servers:
            await self.monitor.process_message(message)
        
        # Process bot commands
        await self.process_commands(message)
    
    async def on_reaction_add(self, reaction, user):
        """Handle reaction additions"""
        if user.bot:
            return
        
        if reaction.message.guild and reaction.message.guild.id in self.tracked_servers:
            await self.monitor.process_reaction(reaction, user, 'add')
    
    async def on_reaction_remove(self, reaction, user):
        """Handle reaction removals"""
        if user.bot:
            return
        
        if reaction.message.guild and reaction.message.guild.id in self.tracked_servers:
            await self.monitor.process_reaction(reaction, user, 'remove')
    
    async def on_message_edit(self, before, after):
        """Handle message edits"""
        if after.author.bot:
            return
        
        if after.guild and after.guild.id in self.tracked_servers:
            await self.monitor.process_message_edit(before, after)
    
    async def on_message_delete(self, message):
        """Handle message deletions"""
        if message.author.bot:
            return
        
        if message.guild and message.guild.id in self.tracked_servers:
            await self.monitor.process_message_delete(message)

# Bot instance
bot = None

def get_bot_instance():
    """Get the bot instance"""
    global bot
    return bot

async def main():
    """Main bot function"""
    global bot
    
    bot = GovTrackerBot()
    
    # Add bot commands
    await setup_commands(bot)
    
    # Start the bot
    token = os.environ.get('DISCORD_TOKEN')
    if not token:
        logging.error("DISCORD_TOKEN environment variable not set")
        return
    
    try:
        await bot.start(token)
    except Exception as e:
        logging.error(f"Error starting bot: {e}")
    finally:
        await bot.close()

async def setup_commands(bot):
    """Setup bot commands"""
    
    @bot.command(name='status')
    async def status_command(ctx):
        """Get bot status"""
        embed = discord.Embed(
            title="GovTracker2 Bot Status",
            color=discord.Color.green()
        )
        
        embed.add_field(
            name="Servers",
            value=f"Tracking {len(bot.tracked_servers)} servers",
            inline=True
        )
        
        embed.add_field(
            name="Uptime",
            value="Online",
            inline=True
        )
        
        embed.add_field(
            name="Version",
            value="Python 3.12 Migration",
            inline=True
        )
        
        await ctx.send(embed=embed)
    
    @bot.command(name='stats')
    async def stats_command(ctx):
        """Get server statistics"""
        if ctx.guild.id not in bot.tracked_servers:
            await ctx.send("This server is not being tracked.")
            return
        
        try:
            with app.app_context():
                server = DiscordServer.find_by_server_id(str(ctx.guild.id))
                if not server:
                    await ctx.send("Server not found in database.")
                    return
                
                # Get statistics
                activity_count = server.get_activity_count(days=30)
                active_curators = server.get_active_curators()
                
                embed = discord.Embed(
                    title=f"Statistics for {ctx.guild.name}",
                    color=discord.Color.blue()
                )
                
                embed.add_field(
                    name="Activities (30 days)",
                    value=activity_count,
                    inline=True
                )
                
                embed.add_field(
                    name="Active Curators",
                    value=len(active_curators),
                    inline=True
                )
                
                if active_curators:
                    top_curators = sorted(active_curators, key=lambda x: x.total_points, reverse=True)[:5]
                    curator_list = "\n".join([f"• {c.name} ({c.total_points} pts)" for c in top_curators])
                    embed.add_field(
                        name="Top Curators",
                        value=curator_list,
                        inline=False
                    )
                
                await ctx.send(embed=embed)
        
        except Exception as e:
            logging.error(f"Error in stats command: {e}")
            await ctx.send("An error occurred while fetching statistics.")
    
    @bot.command(name='help')
    async def help_command(ctx):
        """Show help information"""
        embed = discord.Embed(
            title="GovTracker2 Bot Commands",
            description="Available commands for GovTracker2 bot",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="!gtstatus",
            value="Show bot status and information",
            inline=False
        )
        
        embed.add_field(
            name="!gtstats",
            value="Show server statistics and top curators",
            inline=False
        )
        
        embed.add_field(
            name="!gthelp",
            value="Show this help message",
            inline=False
        )
        
        embed.set_footer(text="GovTracker2 Python Migration by Replit Agent")
        
        await ctx.send(embed=embed)

def start_discord_bot():
    """Start the Discord bot"""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Bot stopped by user")
    except Exception as e:
        logging.error(f"Bot error: {e}")

if __name__ == "__main__":
    start_discord_bot()
