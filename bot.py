import os
import raumcheck
import discord
from discord.ext import commands
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
DISCORD_TAG = os.getenv("DISCORD_TAG")
ENVIRONMENT = os.getenv("ENVIRONMENT")

bot = commands.Bot(command_prefix=DISCORD_TAG + " ")

@bot.event
async def on_ready():
    print("{} is running".format(bot.user.name))

@bot.event
async def on_command_error(ctx, error):
    print("Error ({}) on command: {}".format(error, ctx.message.content))

@bot.command()
async def find(ctx, query, date_str=None):
    """Finds free rooms near the given query string (based on levenshtein distance)."""
    print("{}: {}".format(ctx.message.author, ctx.message.content))
    query = query.upper()
    async with ctx.typing():
        date = get_date(date_str)
        rooms = raumcheck.get_sorted_rooms(query)
        free_rooms = {}
        for room in rooms:
            events = raumcheck.get_availability(room, date)
            if len(events) == 0:
                free_rooms[room] = events
                if len(free_rooms) == 5:
                    break
        
    if len(free_rooms) == 0:
        description = "Ich konnte keine freien Räume finden :("
    else:
        description = "Ich habe folgende Räume in deiner Nähe gefunden, die heute nicht belegt sind:\n- **{}**".format("**\n- **".join(free_rooms.keys()))
        
    embed = discord.Embed(description=description)
    embed.set_footer(text="Angaben ohne Gewähr." if ENVIRONMENT == "PRODUCTION" else "Development build.")
    await ctx.send(embed=embed)

@bot.command()
async def check(ctx, room, date_str=None):
    """Checks the given room for availability (today or on the given date)."""
    print("{}: {}".format(ctx.message.author, ctx.message.content))
    room = room.upper()
    date = get_date(date_str)
    if date is None:
        # TODO better error handling
        await ctx.send(embed=discord.Embed(description="Ungültiges Datum angegeben. Bitte nutze das Format DD.MM.YY"))
        return

    date_display = "heute" if date_str is None else "am {}".format(date)

    async with ctx.typing():
        events = raumcheck.get_availability(room, date)

        if events is None:
            embed = discord.Embed(description="Der Raum **{}** konnte nicht im Raumplan gefunden werden.".format(room))
        elif len(events) == 0:
            embed = discord.Embed(description="Der Raum **{}** ist {} nicht belegt.".format(room, date_display))
        else:
            embed = discord.Embed(description="Der Raum **{}** ist {} zu folgenden Uhrzeiten belegt:".format(room, date_display))
            for event in events:
                embed.add_field(name="{} bis {}".format(event["start"], event["end"]), value=event["name"], inline=False)

    embed.set_footer(text="Angaben ohne Gewähr." if ENVIRONMENT == "PRODUCTION" else "Development build.")
    await ctx.send(embed=embed)

def get_date(date_str):
    """
    Returns one of the following:
    - today's date if the given date is None (format: DD.MM.YY)
    - the given date, but adjusted to fit the format DD.MM.YY (D -> 0D, M -> 0M, YYYY -> YY)

    If the given date does not have three parts separated with a dot, None is returned. 
    """
    if date_str is None:
        date = datetime.today().strftime('%d.%m.%Y')
        # Convert from DD.MM.YYYY to DD.MM.YY
        date = date[:-4] + date[-2:]
    else:
        parts = date_str.split(".")
        if len(parts) != 3:
            return None

        day, month, year = parts
        if len(day) == 1:
            day = "0" + day
        if len(month) == 1:
            month = "0" + month
        if len(year) == 4:
            year = year[2:]

        date = "{}.{}.{}".format(day, month, year)

    return date

bot.run(TOKEN)