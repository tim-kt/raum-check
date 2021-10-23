import sys
import os.path
import argparse
import urllib.request
import fitz
from datetime import datetime

WEEKDAYS = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]

def get_rooms():
    """Downloads the Raumplan.pdf and parses it into a neatly organized dictionary."""
    if (os.path.isfile("Raumplan.pdf")):
        os.remove("Raumplan.pdf")

    urllib.request.urlretrieve("https://www.intern.tu-darmstadt.de/media/dezernat_ii/corona_klausurdurchfuehrung/Raumplan.pdf", "Raumplan.pdf")

    pages = []
    with fitz.open("Raumplan.pdf") as pdf:
        for page in pdf:
            pages.append(page.get_text())

    os.remove("Raumplan.pdf")

    rooms = {}
    for page in pages:
        lines = page.split("\n")
        room = lines[0].split()[0]

        # The first six lines are the room and table heading
        event_lines = lines[6:]
        events = {}
        for index, line in enumerate(event_lines):
            if line in WEEKDAYS:
                date, start = event_lines[index+1].split()
                end = event_lines[index+2][2:]
                name = event_lines[index+3]
                
                # Some names are not properly separated ('xx-xx-xxxx-xx<name>' instead of 'xx-xx-xxxx-xx <name>')
                if len(name) > 13 and name[13] != "":
                    name = name[:13] + " " + name[13:]

                if date not in events:
                    events[date] = []

                events[date].append({
                    "name": name,
                    "start": start,
                    "end": end,
                })
        
        rooms[room] = events

    return rooms

def get_availability(room, date=None):
    room = room.upper()
    if date is None:
        date_display = "heute"
        date = datetime.today().strftime('%d.%m.%Y')
        # DD.MM.YYYY -> DD.MM.YY
        date = date[:-4] + date[-2:]
    else:
        parts = date.split(".")
        if len(parts) != 3:
            return "Ungültiges Datum angegeben. Bitte nutze das Format DD.MM.YY", None

        day, month, year = parts
        if len(day) == 1:
            day = "0" + day
        if len(month) == 1:
            month = "0" + month
        if len(year) == 4:
            year = year[2:]

        date = "{}.{}.{}".format(day, month, year)
        date_display = "am {}".format(date)

    # TODO cache?
    rooms = get_rooms()
    if room not in rooms.keys():
        return "Der Raum **{}** konnte nicht im Raumplan gefunden werden.".format(room), None

    if date in rooms.get(room).keys():
        print(rooms.get(room).get(date))
        return "Der Raum **{}** ist {} zu folgenden Uhrzeiten belegt:".format(room, date_display), rooms.get(room).get(date)
    else:
        return "Der Raum **{}** ist {} nicht belegt.".format(room, date_display), None
