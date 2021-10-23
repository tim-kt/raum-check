import os
import raumcheck
import discord
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
ENVIRONMENT = os.getenv('ENVIRONMENT')

client = discord.Client()

@client.event
async def on_ready():
    print("{} is running".format(client.user.name))

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if client.user.mentioned_in(message) and message.mention_everyone is False:
        print("{}: {}".format(message.author, message.content))
        parts = message.content.split()
        if len(parts) < 2:
            return

        room = parts[1]
        if len(parts) < 3:
            result, events = raumcheck.get_availability(room)
        else:
            result, events = raumcheck.get_availability(room, date=parts[2])
        
        embed = discord.Embed(description=result)
        if events is not None:
            for event in events:
                embed.add_field(name="{} bis {}".format(event["start"], event["end"]), value=event["name"], inline=False)
        
        if ENVIRONMENT == "PRODUCTION":
            embed.set_footer(text="Angaben ohne Gewähr.")
        else:
            embed.set_footer(text="Development build.")

        await message.channel.send(embed=embed)

client.run(TOKEN)
