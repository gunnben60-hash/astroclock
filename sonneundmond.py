import datetime
import ephem #type: ignore
import mondkalender
import time

import curses 
from zoneinfo import ZoneInfo

def getLines(location):
    sun = ephem.Sun()
    moon = ephem.Moon()
        
    location.date = ephem.now()
    nextNoon = location.next_transit(sun)
    lastNoon = location.previous_transit(sun)
    yield 'MESZ:\t       '+ephem.to_timezone(ephem.now(), ZoneInfo('Europe/Berlin')).strftime('%d.%m.%y %H:%M:%S')
    yield 'Wahre Sonnenzeit:\t'+(datetime.datetime(nextNoon.datetime().year, nextNoon.datetime().month, nextNoon.datetime().day, 12, 0, 0)
        + datetime.timedelta(days=(ephem.now()-nextNoon)/(nextNoon-lastNoon))).strftime('%H:%M:%S')
    siderialTime = str(location.sidereal_time())[:-3]
    if siderialTime[1] == ':':
        siderialTime = '0' + siderialTime
    yield 'Sternzeit:\t\t'+siderialTime
    yield 'UTC:\t\t\t'+datetime.datetime.now(datetime.timezone.utc).strftime('%H:%M:%S')
    yield ''
    
    location.date = ephem.date(datetime.datetime.now().replace(hour=0, minute=0, second=0))
    sunrisetoday = location.next_rising(sun)
    noonToday = location.next_transit(sun)
    sunsetToday = location.next_setting(sun)
    yield 'Sonnenaufgang:\t\t'+ephem.to_timezone(sunrisetoday, ZoneInfo('Europe/Berlin')).strftime('%H:%M:%S')
    yield 'Mittag:\t\t\t'+ephem.to_timezone(noonToday, ZoneInfo('Europe/Berlin')).strftime('%H:%M:%S')
    yield 'Sonnenuntergang:\t'+ephem.to_timezone(sunsetToday, ZoneInfo('Europe/Berlin')).strftime('%H:%M:%S')+' ('+str(sunsetToday.datetime()-sunrisetoday.datetime())[:-10]+'h Tag)'
    yield ''

    calendar = mondkalender.MoonCalendar()

    yield 'Monat:\t\t\t'+calendar.getMonth()
    if ephem.next_full_moon(ephem.now()) < ephem.next_new_moon(ephem.now()):
        yield 'nächster Vollmond:\t'+ephem.to_timezone(ephem.next_full_moon(ephem.now()), ZoneInfo('Europe/Berlin')).strftime('%d.%m.%y %H:%M:%S')
        yield 'nächster Neumond:\t'+ephem.to_timezone(ephem.next_new_moon(ephem.now()), ZoneInfo('Europe/Berlin')).strftime('%d.%m.%y %H:%M:%S')
    else:
        yield 'nächster Neumond:\t'+ephem.to_timezone(ephem.next_new_moon(ephem.now()), ZoneInfo('Europe/Berlin')).strftime('%d.%m.%y %H:%M:%S')
        yield 'nächster Vollmond:\t'+ephem.to_timezone(ephem.next_full_moon(ephem.now()), ZoneInfo('Europe/Berlin')).strftime('%d.%m.%y %H:%M:%S')
    yield ''

    location.date = ephem.date(datetime.datetime.now().replace(hour=0, minute=0, second=0))
    moonriseToday = location.next_rising(moon)
    moonZenitToday = location.next_transit(moon)
    moonsetToday = location.next_setting(moon)
    tempList = sorted([(moonriseToday, 'Mondaufgang:\t\t'), 
                        (moonZenitToday, 'Mondhöchsstand:\t\t'), 
                        (moonsetToday, 'Monduntergang:\t\t')], key=lambda x: x[0])
    for i in range(3):
        moon.compute(moonZenitToday)
        outstring = tempList[i][1] + ephem.to_timezone(tempList[i][0], ZoneInfo('Europe/Berlin')).strftime('%H:%M:%S')
        if (tempList[i][1] == 'Monduntergang:\t\t'):
            location.date = moonZenitToday
            previousMoonrise = location.previous_rising(moon)
            nextMoonSet = location.next_setting(moon)
            outstring += ' ('+str(nextMoonSet.datetime()-previousMoonrise.datetime())[:-10]+'h über Horizont)'
        elif (tempList[i][1] == 'Mondhöchsstand:\t\t'):
            moon.compute(moonZenitToday)
            averageDistanceMoonKm = 381
            percentage = -int((moon.earth_distance*1.495979e+5-averageDistanceMoonKm) / averageDistanceMoonKm *200.0 + 0.5)
            outstring +=' (' + ('+' if percentage>0 else '') + str(percentage) + '% Helligkeit)'
        else:
            outstring += ' (Phase: ' + str(int(moon.phase+0.5)) + '%)'
        yield outstring
    location.date = ephem.date(datetime.datetime.now())
    moon.compute(location)
    yield 'Position des Mondes:\t' + str(moon.ra)


def main(stdscr):
    stdscr.clear()
    #location = ephem.city('Berlin')

    #Zschopau
    location = ephem.Observer()
    location.lon, location.lat  = '13.066667', '50.75'
    
    while True:
        for i, line in enumerate(getLines(location)):
            stdscr.addstr(i+1, 0, line)
            curses.curs_set(0) # hide cursor 
            stdscr.refresh()
        time.sleep(0.5)

if __name__ == '__main__':
    curses.wrapper(main)



