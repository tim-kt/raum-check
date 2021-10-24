import os
import raumcheck
import discord
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
ENVIRONMENT = os.getenv("ENVIRONMENT")

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
        if "find" in message.content:
            # A find query should have the following format:
            # @<mention> find <string> <optionally: number of results>
            async with message.channel.typing():
                date = get_date()
                query = message.content.split()
                rooms = raumcheck.get_sorted_rooms(query[2].upper())
                free_rooms = {}
                for room in rooms:
                    events = raumcheck.get_availability(room, date)
                    if len(events) == 0:
                        free_rooms[room] = events
                        if len(free_rooms) == int(query[3]) if len(query) > 3 else 5:
                            break
            
            if len(free_rooms) == 0:
                description = "Ich konnte keine freien Räume finden :("
            else:
                description = "Ich habe folgende Räume in deiner Nähe gefunden, die heute nicht belegt sind:\n- **{}**".format("**\n- **".join(free_rooms.keys()))
            embed = discord.Embed(description=description)
            await message.channel.send(embed=embed)
        else:
            # A check query should have the following format:
            # @<mention> <room> <optionally: date>
            query = message.content.split()
            if len(query) < 2:
                await message.channel.send(embed=discord.Embed(description="Bitte gib einen Raum an."))
                return

            room = query[1]
            date = get_date(date=query[2] if len(query) > 2 else None)
            if date is None:
                await message.channel.send(embed=discord.Embed(description="Ungültiges Datum angegeben. Bitte nutze das Format DD.MM.YY"))
                return

            date_display = "am {}".format(date) if len(query) > 2 else "heute"

            async with message.channel.typing():
                events = raumcheck.get_availability(room, date)

                if events is None:
                    embed = discord.Embed(description="Der Raum **{}** konnte nicht im Raumplan gefunden werden.".format(room.upper()))
                elif len(events) == 0:
                    embed = discord.Embed(description="Der Raum **{}** ist {} nicht belegt.".format(room.upper(), date_display))
                else:
                    embed = discord.Embed(description="Der Raum **{}** ist {} zu folgenden Uhrzeiten belegt:".format(room.upper(), date_display))
                    for event in events:
                        embed.add_field(name="{} bis {}".format(event["start"], event["end"]), value=event["name"], inline=False)

            embed.set_footer(text="Angaben ohne Gewähr." if ENVIRONMENT == "PRODUCTION" else "Development build.")
            await message.channel.send(embed=embed)


def get_date(date=None):
    """
    Returns one of the following:
    - today's date if the given date is None (format: DD.MM.YY)
    - the given date, but adjusted to fit the format DD.MM.YY (D -> 0D, M -> 0M, YYYY -> YY)

    If the given date does not have three parts separated with a dot, None is returned. 
    """
    if date is None:
        date = date = datetime.today().strftime('%d.%m.%Y')
        # Convert from DD.MM.YYYY to DD.MM.YY
        date = date[:-4] + date[-2:]
    else:
        parts = date.split(".")
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


client.run(TOKEN)
