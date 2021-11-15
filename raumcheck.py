import math
import os.path
import urllib.request
import fitz
import json
import time

WEEKDAYS = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]

def get_rooms():
    """
    Downloads the Raumplan.pdf and parses it into a neatly organized dictionary.
    
    If there is a raumplan.json file which was last modified during the last hour,
    the data from there will be used. Otherwise, it will be created or overwritten.
    """
    # TODO Check if there are any entries for today (if not, the PDF is not up to date)
    if (os.path.isfile("raumplan.json")):
        if time.time() - os.path.getmtime("raumplan.json") < 60*60:
            with open("raumplan.json") as f:
                return json.load(f)

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

                # TODO this should be a class with helper methods (e.g. is_free())
                events[date].append({
                    "name": name,
                    "start": start,
                    "end": end,
                })
        
        rooms[room] = events
    
    with open("raumplan.json", "w+") as f:
        json.dump(rooms, f)

    return rooms

def get_availability(room, date):
    """
    Returns the availablity of the given room on the given date.
    
    The result is an array of events, which all have the properties
    - name (course ID and, optionally, a name)
    - start (when the event starts)
    - end (when the event ends)
    """
    rooms = get_rooms()
    if room not in rooms.keys():
        return None

    if date in rooms.get(room).keys():
        return rooms.get(room).get(date)
    else:
        return []

def get_sorted_rooms(s):
    """Returns a a list of room names, sorted by levenshtein distance to the given string s."""
    rooms = get_rooms()
    distances = list(map(lambda x: dist(x, s), rooms.keys()))
    sorted_rooms = [x for _, x in sorted(zip(distances, rooms.keys()))]
    return sorted_rooms

def dist(x, y):
    def single_dist(x, y):
        try:
            return math.abs(int(x) - int(y))
        except:
            return 0 if x==y else 1
        
    m = min(len(x), len(y))
    return sum(single_dist(a,b)*(m-i) for i,(a,b) in enumerate(zip(x,y)))
