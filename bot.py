import os
import raumcheck
import discord
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

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
            result, times = raumcheck.get_availability(room)
        else:
            result, times = raumcheck.get_availability(room, day=parts[2])
        
        embed = discord.Embed(description=result)
        if times is not None:
            for name, value in times.items():
                embed.add_field(name=name, value=value, inline=False)
        
        embed.set_footer(text="Angaben ohne Gewähr")
        await message.channel.send(embed=embed)

client.run(TOKEN)
