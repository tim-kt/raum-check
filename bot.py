import os
import raumcheck
import discord
from discord.ext import commands
from dotenv import load_dotenv
import datetime

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
ENVIRONMENT = os.getenv("ENVIRONMENT")

bot = commands.Bot(("raum ", "Raum "))

@bot.event
async def on_ready():
    print("{} is running".format(bot.user.name))

@bot.event
async def on_command_error(ctx, error):
    print("Error ({}) on command: {}".format(error, ctx.message.content))

@bot.command()
async def find(ctx, query, date_str=None):
    """Finds free rooms near the given query string (levenshtein)."""
    print("{}: {}".format(ctx.message.author, ctx.message.content))
    query = query.upper()
    async with ctx.typing():
        try:
            date = get_date(date_str)
        except ValueError as e:
            await ctx.send(embed=discord.Embed(description=e.args[0]))
            return

        date_display = "heute" if date_str is None else "am {}".format(date)        

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
        description = "Ich habe folgende Räume gefunden, die {} nicht belegt sind:\n- **{}**".format(date_display, "**\n- **".join(free_rooms.keys()))
        
    embed = discord.Embed(description=description)
    embed.set_footer(text="Angaben ohne Gewähr." if ENVIRONMENT == "PRODUCTION" else "Development build.")
    await ctx.send(embed=embed)

@bot.command()
async def check(ctx, room, date_str=None):
    """Checks the given room for availability."""
    print("{}: {}".format(ctx.message.author, ctx.message.content))
    room = room.upper()
    try:
        date = get_date(date_str)
    except ValueError as e:
        await ctx.send(embed=discord.Embed(description=e.args[0]))
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

WEEKDAYS = {
    "mo": 0,
    "montag": 0,
    "di": 1,
    "dienstag": 1,
    "mi": 2,
    "mittwoch": 2,
    "do": 3,
    "donnerstag": 3,
    "fr": 4,
    "freitag": 4,
    "sa": 5,
    "samstag": 5,
    "so": 6,
    "sonntag": 6,
}

def get_date(date_str):
    """
    Returns one of the following:
    - today's date if the given string is None or 'heute'
    - tomorrow's date if the given string is 'morgen'
    - the date of given weekday if the string date is in the keys of WEEKDAYS
    - the given date, adjusted to fit the format
    
    The format will always be DD.MM.YY. TODO docstring
    """
    if date_str is not None:
        date_str = date_str.lower()
    
    if date_str is None or date_str == "heute":
        date = datetime.date.today().strftime('%d.%m.%Y')
    elif date_str == "morgen":
        date = (datetime.date.today() + datetime.timedelta(days=1)).strftime('%d.%m.%Y')
    elif date_str in WEEKDAYS.keys():
        today = datetime.date.today()
        days_ahead = (WEEKDAYS[date_str] - today.weekday()) % 7
        date = (today + datetime.timedelta(days=days_ahead)).strftime('%d.%m.%Y')
    else:
        try:
            datetime.datetime.strptime(date_str, '%d.%m.%Y')
        except ValueError:
            raise ValueError("Bitte gib ein gültiges Datum im Format DD.MM.YYYY an (oder heute, morgen oder ein Wochentag).")

        date = date_str

    # Convert from DD.MM.YYYY to DD.MM.YY (results of strftime())
    if len(date) == 10:
        date = date[:-4] + date[-2:]

    return date

bot.run(TOKEN)