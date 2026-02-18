import datetime
import ephem #type: ignore
import mondkalender
import time

from mondkalender import ephemDateToDatetimeAtTimeZone, datetimeToString

try:
    from zoneinfo import ZoneInfo
except:
    from backports.zoneinfo import ZoneInfo

def getLines(location, timezoneString, now=None):
    sun = ephem.Sun()
    moon = ephem.Moon()
    
    timezone = ZoneInfo(timezoneString)
    if now is None:
        now = ephem.now()
    location.date = now
    nextNoon = location.next_transit(sun)
    lastNoon = location.previous_transit(sun)
    yield 'Lokale Zeit:\t       '+datetimeToString(ephemDateToDatetimeAtTimeZone(now, timezone), False)
    yield 'Wahre Sonnenzeit:\t'+datetimeToString(datetime.datetime(nextNoon.datetime().year, nextNoon.datetime().month, nextNoon.datetime().day, 12, 0, 0) + datetime.timedelta(days=(now-nextNoon)/(nextNoon-lastNoon)))
    try:
        siderialTime = str(location.sidereal_time())[:-6]
        if siderialTime[1] == ':':
            siderialTime = '0' + siderialTime
        yield 'Sternzeit:\t\t'+siderialTime
        yield 'UTC:\t\t\t'+datetimeToString(ephemDateToDatetimeAtTimeZone(now, datetime.timezone.utc))
        yield ''
    
        location.date = ephem.date(ephemDateToDatetimeAtTimeZone(now, timezone).replace(hour=0, minute=0, second=0))
        sunrisetoday = location.next_rising(sun)
        noonToday = location.next_transit(sun)
        sunsetToday = location.next_setting(sun)
        yield 'Sonnenaufgang:\t\t'+datetimeToString(ephemDateToDatetimeAtTimeZone(sunrisetoday, timezone))
        yield 'Mittag:\t\t\t'+datetimeToString(ephemDateToDatetimeAtTimeZone(noonToday, timezone))
        yield 'Sonnenuntergang:\t'+datetimeToString(ephemDateToDatetimeAtTimeZone(sunsetToday, timezone))+' ('+str(sunsetToday.datetime()-sunrisetoday.datetime())[:-10]+'h Tag)'
        yield ''

        calendar = mondkalender.MoonCalendar(year=ephemDateToDatetimeAtTimeZone(now, timezone).year)

        temp = 'abnehmend'
        if ephem.next_full_moon(now) < ephem.next_new_moon(now):
            temp = 'zunehmend'
        dateTuple = now.tuple()
            
        yield 'Monat (' + temp + '):\t'+calendar.getMonth(now) + ', ' + calendar.getBabylonianMonthLiliusClavius(now) + calendar.getHijriMonthName(dateTuple[0], dateTuple[1], dateTuple[2])
        if ephem.next_full_moon(now) < ephem.next_new_moon(now):
            yield 'nächster Vollmond:\t'+datetimeToString(ephemDateToDatetimeAtTimeZone(ephem.next_full_moon(now), timezone), False)
            yield 'nächster Neumond:\t'+datetimeToString(ephemDateToDatetimeAtTimeZone(ephem.next_new_moon(now), timezone), False)
        else:
            yield 'nächster Neumond:\t'+datetimeToString(ephemDateToDatetimeAtTimeZone(ephem.next_new_moon(now), timezone), False)
            yield 'nächster Vollmond:\t'+datetimeToString(ephemDateToDatetimeAtTimeZone(ephem.next_full_moon(now), timezone), False)
        yield ''

        location.date = ephem.date(ephemDateToDatetimeAtTimeZone(now, timezone).replace(hour=0, minute=0, second=0))
        moonriseToday = location.next_rising(moon)
        moonZenitToday = location.next_transit(moon)
        moonsetToday = location.next_setting(moon)
        tempList = sorted([(moonriseToday, 'Mondaufgang:\t\t'), 
                            (moonZenitToday, 'Mondhöchsstand:\t\t'), 
                            (moonsetToday, 'Monduntergang:\t\t')], key=lambda x: x[0])
        for i in range(3):
            moon.compute(moonZenitToday)
            outstring = tempList[i][1] + datetimeToString(ephemDateToDatetimeAtTimeZone(tempList[i][0], timezone))
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
        location.date = now
        moon.compute(location)
        yield 'Position des Mondes:\t' + str(moon.ra)
    except Exception as ex:
        yield 'Error:\t'+str(ex)


def main(stdscr):
    stdscr.clear()
    #location = ephem.city('Berlin')

    #Zschopau
    location = ephem.Observer()
    location.lon, location.lat  = '13.066667', '50.75'
    
    while True:
        for i, line in enumerate(getLines(location, 'Europe/Berlin')):
            stdscr.addstr(i+1, 0, line)
            curses.curs_set(0) # hide cursor 
            stdscr.refresh()
        time.sleep(0.5)

if __name__ == '__main__':
    import curses 
    curses.wrapper(main)



