import discord
from discord import app_commands
import os
from models import APIKey, db
from app import create_app

class KeyManagementBot(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        print(f'Bot is being set up...')
        await self.tree.sync()
        
    async def on_ready(self):
        print(f'Logged in as {self.user.name}')
        print('Bot is ready!')

def run_bot():
    # Create Flask app context
    app = create_app()
    with app.app_context():
        bot = KeyManagementBot()

        @bot.tree.command(name="request_free", description="Request a free API key (10 requests/day)")
        async def request_free(interaction: discord.Interaction):
            """Request a free API key with IP restriction"""
            server_id = os.getenv('DISCORD_SERVER_ID')
            if str(interaction.guild_id) != server_id:
                await interaction.response.send_message(
                    "Free key requests are only available in our official server.",
                    ephemeral=True
                )
                return

            # Check if user already has a key
            existing_key = APIKey.query.filter(
                APIKey.name.like(f'Free-{interaction.user.name}-%')
            ).first()

            if existing_key:
                await interaction.response.send_message(
                    "You already have a free API key. Only one free key per user is allowed.\n"
                    "For premium access with higher limits, please contact an admin in the server.",
                    ephemeral=True
                )
                return

            # Create API key with user's Discord ID in name for tracking
            api_key = APIKey(
                key=APIKey.generate_key(),
                name=f'Free-{interaction.user.name}-{interaction.user.id}',
                tier='regular'
            )
            
            # Save to database
            try:
                db.session.add(api_key)
                db.session.commit()
                
                # Send key via DM
                try:
                    await interaction.user.send(
                        f"Here's your free API key: `{api_key.key}`\n\n"
                        f"📝 Key Details:\n"
                        f"• Rate Limit: 10 signing requests per day\n"
                        f"• Valid for IP-restricted usage only\n\n"
                        f"🔒 Important:\n"
                        f"• Keep this key secure and don't share it\n"
                        f"• For premium access (100 requests/day), contact an admin\n"
                        f"• Report any security concerns to admins immediately"
                    )
                    await interaction.response.send_message(
                        "✨ I've sent your free API key via DM! Check your messages for details.\n"
                        "For premium access with higher limits, please contact an admin.",
                        ephemeral=True
                    )
                except discord.Forbidden:
                    await interaction.response.send_message(
                        "I couldn't send you a DM. Please enable DMs from server members and try again.",
                        ephemeral=True
                    )
                    # Rollback the key creation if we couldn't send it
                    db.session.delete(api_key)
                    db.session.commit()
            except Exception as e:
                print(f"Error creating API key: {str(e)}")
                await interaction.response.send_message(
                    "There was an error processing your request. Please try again later.",
                    ephemeral=True
                )

        token = os.getenv('DISCORD_BOT_TOKEN')
        if not token:
            print("Error: DISCORD_BOT_TOKEN not found in environment variables")
            return
            
        try:
            bot.run(token)
        except Exception as e:
            print(f"Error running bot: {str(e)}")
