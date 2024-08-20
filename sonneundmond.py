
import datetime
import ephem
import mondkalender
import os
import time

import curses 
from zoneinfo import ZoneInfo

def main(stdscr):
    stdscr.clear()
    #location = ephem.city('Berlin')

    #Zschopau
    location = ephem.Observer()
    location.lon, location.lat  = '13.066667', '50.75'
    
    sun = ephem.Sun()
    moon = ephem.Moon()
    while True:
        
        location.date = ephem.now()
        nextNoon = location.next_transit(sun)
        lastNoon = location.previous_transit(sun)
        stdscr.addstr(1, 0, 'MESZ:\t       '+ephem.to_timezone(ephem.now(), ZoneInfo('Europe/Berlin')).strftime('%d.%m.%y %H:%M:%S'))
        stdscr.addstr(2, 0, 'Wahre Sonnenzeit:\t'+(datetime.datetime(nextNoon.datetime().year, nextNoon.datetime().month, nextNoon.datetime().day, 12, 0, 0)
            + datetime.timedelta(days=(ephem.now()-nextNoon)/(nextNoon-lastNoon))).strftime('%H:%M:%S'))
        siderialTime = str(location.sidereal_time())[:-3]
        if siderialTime[1] == ':':
            siderialTime = '0' + siderialTime
        stdscr.addstr(3, 0, 'Sternzeit:\t\t'+siderialTime)
        stdscr.addstr(4, 0, 'UTC:\t\t\t'+datetime.datetime.now(datetime.timezone.utc).strftime('%H:%M:%S'))
        
        location.date = ephem.date(datetime.datetime.now().replace(hour=0, minute=0, second=0))
        sunrisetoday = location.next_rising(sun)
        noonToday = location.next_transit(sun)
        sunsetToday = location.next_setting(sun)
        stdscr.addstr(6, 0, 'Sonnenaufgang:\t\t'+ephem.to_timezone(sunrisetoday, ZoneInfo('Europe/Berlin')).strftime('%H:%M:%S'))
        stdscr.addstr(7, 0, 'Mittag:\t\t\t'+ephem.to_timezone(noonToday, ZoneInfo('Europe/Berlin')).strftime('%H:%M:%S'))
        stdscr.addstr(8, 0, 'Sonnenuntergang:\t'+ephem.to_timezone(sunsetToday, ZoneInfo('Europe/Berlin')).strftime('%H:%M:%S')+' ('
                      +str(sunsetToday.datetime()-sunrisetoday.datetime())[:-10]+'h Tag)')

        calendar = mondkalender.MoonCalendar()

        stdscr.addstr(10, 0, 'Monat:\t\t\t'+calendar.getMonth())
        if ephem.next_full_moon(ephem.now()) < ephem.next_new_moon(ephem.now()):
            stdscr.addstr(11, 0, 'nächster Vollmond:\t'+ephem.to_timezone(ephem.next_full_moon(ephem.now()), ZoneInfo('Europe/Berlin')).strftime('%d.%m.%y %H:%M:%S'))
            stdscr.addstr(12, 0, 'nächster Neumond:\t'+ephem.to_timezone(ephem.next_new_moon(ephem.now()), ZoneInfo('Europe/Berlin')).strftime('%d.%m.%y %H:%M:%S'))
        else:
            stdscr.addstr(11, 0, 'nächster Neumond:\t'+ephem.to_timezone(ephem.next_new_moon(ephem.now()), ZoneInfo('Europe/Berlin')).strftime('%d.%m.%y %H:%M:%S'))
            stdscr.addstr(12, 0, 'nächster Vollmond:\t'+ephem.to_timezone(ephem.next_full_moon(ephem.now()), ZoneInfo('Europe/Berlin')).strftime('%d.%m.%y %H:%M:%S'))

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
                

            stdscr.addstr(14+i, 0, outstring)
        curses.curs_set(0) # hide cursor 
        stdscr.refresh()
        time.sleep(0.5)


curses.wrapper(main)



