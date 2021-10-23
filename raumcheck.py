import sys
import os.path
import argparse
import urllib.request
import fitz
from datetime import datetime

def get_pages():
    if (os.path.isfile("Raumplan.pdf")):
        os.remove("Raumplan.pdf")

    urllib.request.urlretrieve("https://www.intern.tu-darmstadt.de/media/dezernat_ii/corona_klausurdurchfuehrung/Raumplan.pdf", "Raumplan.pdf")

    pages = []
    with fitz.open("Raumplan.pdf") as pdf:
        for page in pdf:
            pages.append(page.get_text())

    os.remove("Raumplan.pdf")
    return pages

def get_availability(room, day=None):
    room = room.upper()
    day_display = "heute"
    if day is None:
        day = datetime.today().strftime('%d.%m.%Y')
    else:
        if len(day) == 10:
            day = day[:-4]+day[-2:]
        day_display = "am {}".format(day)

    pages = get_pages()
    rooms = {}
    for page in pages:
        lines = page.split("\n")
        
        if room == lines[0].split()[0]:
            if day not in page:
                result = "Der Raum **{}** ist {} nicht belegt.".format(room, day_display)
                return result, None
            else:
                result = "Der Raum **{}** ist {} zu folgenden Uhrzeiten belegt:".format(room, day_display)
                times = {}
                for index, line in enumerate(lines):
                    if day in line:
                        start = line.split()[1]
                        end = lines[index+1][2:]
                        event = lines[index+2]
                        times["{} bis {}".format(start, end)] = event
                
                return result, times
    
    return "Der Raum **{}** konnte nicht im Raumplan gefunden werden.".format(room), None