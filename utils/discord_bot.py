import discord
from discord.ext import commands
import os
from models import APIKey, db
from app import create_app
import asyncio

class PremiumKeyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        super().__init__(command_prefix='!', intents=intents)
        self.verification_requests = {}

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

            # Check if user already has a verification in progress
            if ctx.author.id in bot.verification_requests:
                await ctx.send("You already have a verification request in progress. Please complete that first.")
                return

            # Start verification process
            await ctx.send("To get a premium API key, please complete these steps:\n"
                         "1. React with ✅ to confirm you've read our terms of service\n"
                         "2. Answer: How will you use this API key? (Reply in this channel)")

            try:
                # Add verification emoji
                verify_msg = await ctx.send("React with ✅ to confirm:")
                await verify_msg.add_reaction("✅")

                def check_reaction(reaction, user):
                    return user == ctx.author and str(reaction.emoji) == "✅" and reaction.message.id == verify_msg.id

                def check_message(m):
                    return m.author == ctx.author and m.channel == ctx.channel

                # Store verification state
                bot.verification_requests[ctx.author.id] = {
                    'stage': 'started',
                    'timestamp': discord.utils.utcnow()
                }

                # Wait for reaction
                try:
                    reaction, user = await bot.wait_for('reaction_add', timeout=300.0, check=check_reaction)
                except asyncio.TimeoutError:
                    del bot.verification_requests[ctx.author.id]
                    await ctx.send("Verification timed out. Please try again.")
                    return

                # Wait for usage description
                await ctx.send("Great! Now please describe how you plan to use this API key:")
                try:
                    msg = await bot.wait_for('message', timeout=300.0, check=check_message)
                except asyncio.TimeoutError:
                    del bot.verification_requests[ctx.author.id]
                    await ctx.send("Verification timed out. Please try again.")
                    return

                # Create API key
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
                        await ctx.author.send(
                            f"Congratulations! Here's your premium API key: `{api_key.key}`\n"
                            f"Please keep this key secure and don't share it with others.\n"
                            f"You can make up to 100 signing requests per day with this key.\n"
                            f"For documentation and support, visit our website."
                        )
                        await ctx.send("✨ Verification complete! I've sent your premium API key via DM.")
                    except discord.Forbidden:
                        await ctx.send("I couldn't send you a DM. Please enable DMs from server members and try again.")
                        # Rollback the key creation if we couldn't send it
                        db.session.delete(api_key)
                        db.session.commit()
                except Exception as e:
                    print(f"Error creating API key: {str(e)}")
                    await ctx.send("There was an error processing your request. Please try again later.")
                
                # Clean up verification state
                del bot.verification_requests[ctx.author.id]

            except Exception as e:
                print(f"Error in verification process: {str(e)}")
                if ctx.author.id in bot.verification_requests:
                    del bot.verification_requests[ctx.author.id]
                await ctx.send("An error occurred during verification. Please try again later.")

        @bot.event
        async def on_command_error(ctx, error):
            if isinstance(error, commands.CommandNotFound):
                await ctx.send("Unknown command. Use `!request_premium` to request a premium API key.")
            else:
                await ctx.send("An error occurred while processing your command. Please try again.")

        token = os.getenv('DISCORD_BOT_TOKEN')
        if not token:
            print("Error: DISCORD_BOT_TOKEN not found in environment variables")
            return
            
        try:
            bot.run(token)
        except Exception as e:
            print(f"Error running bot: {str(e)}")
