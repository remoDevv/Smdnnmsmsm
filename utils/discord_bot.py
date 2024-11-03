import discord
from discord.ext import commands
import os
from models import APIKey, db
from app import create_app

class PremiumKeyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        super().__init__(command_prefix='!', intents=intents)

    async def setup_hook(self):
        print(f'Bot is being set up...')
        
    async def on_ready(self):
        print(f'Logged in as {self.user.name}')
        print('Bot is ready!')

def run_bot():
    # Create Flask app context
    app = create_app()
    with app.app_context():
        bot = PremiumKeyBot()

        @bot.command(name='request_premium')
        async def request_premium_key(ctx):
            """Request a premium API key"""
            server_id = os.getenv('DISCORD_SERVER_ID')
            if str(ctx.guild.id) != server_id:
                await ctx.send("Premium key requests are only available in our official server.")
                return
                
            # Create a new premium API key
            api_key = APIKey(
                key=APIKey.generate_key(),
                name=f'Premium-{ctx.author.name}',
                tier='premium'
            )
            
            # Save to database
            try:
                db.session.add(api_key)
                db.session.commit()
                
                # Send key via DM
                try:
                    await ctx.author.send(f"Here's your premium API key: `{api_key.key}`\n"
                                      f"Please keep this key secure and don't share it with others.")
                    await ctx.send("I've sent your premium API key via DM! 🎉")
                except discord.Forbidden:
                    await ctx.send("I couldn't send you a DM. Please enable DMs from server members and try again.")
                    # Rollback the key creation if we couldn't send it
                    db.session.delete(api_key)
                    db.session.commit()
            except Exception as e:
                print(f"Error creating API key: {str(e)}")
                await ctx.send("There was an error processing your request. Please try again later.")

        token = os.getenv('DISCORD_BOT_TOKEN')
        if not token:
            print("Error: DISCORD_BOT_TOKEN not found in environment variables")
            return
            
        try:
            bot.run(token)
        except Exception as e:
            print(f"Error running bot: {str(e)}")
