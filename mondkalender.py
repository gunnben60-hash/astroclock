import datetime
import math
import ephem
from MooncalendarByAloysiusLiliusAndChristophClavius.rechneEpakte import getVollmondeNachClaviusLilius
try:
    from zoneinfo import ZoneInfo
except:
    from backports.zoneinfo import ZoneInfo
    
def ephemDateToDatetimeAtTimeZone(ephemDate, timezone):
    date = ephemDate.datetime()
    return date + timezone.utcoffset(datetime.datetime.now())

def datetimeToString(date: datetime, short=True):
    if short:
        return '%s:%s' %('{:02d}'.format(date.hour), '{:02d}'.format(date.minute))    
    return '%s.%s.%s %s:%s' %('{:02d}'.format(date.day), '{:02d}'.format(date.month), '{:02d}'.format(date.year), '{:02d}'.format(date.hour), '{:02d}'.format(date.minute))

class MoonCalendar:
    def __init__(self, year=datetime.datetime.now().year):
        referencedate = ephem.date(datetime.datetime(int(year),1,21,12,00,00))
        self.previousWinterSolstice = ephem.previous_winter_solstice(referencedate)
        self.springEquinox = ephem.next_spring_equinox(referencedate)
        self.summerSolstice = ephem.next_summer_solstice(referencedate)
        self.autumnEquinox = ephem.next_autumn_equinox(referencedate)
        self.winterSolstice = ephem.next_winter_solstice(referencedate)
        referencedate = ephem.date(datetime.datetime(int(year)+1,1,21,12,00,00))
        self.nextSpringEquinox = ephem.next_spring_equinox(referencedate)
        
        self.months = []
        referencedate = ephem.next_full_moon(self.previousWinterSolstice)
        self.months.append((ephem.previous_new_moon(referencedate), ephem.next_new_moon(referencedate), 'Wintermond')) 
        number = 2
        while ephem.next_full_moon(self.months[-1][1]) <= self.springEquinox:
            self.months.append((self.months[-1][1], ephem.next_new_moon(ephem.date(self.months[-1][1].datetime()+datetime.timedelta(days=1))), 'Wintermond %s' %number)) 
            number += 1
        self.months.append((self.months[-1][1], ephem.next_new_moon(ephem.date(self.months[-1][1].datetime()+datetime.timedelta(days=1))), 'Frühlingsmond')) 
        number = 2
        while ephem.next_full_moon(self.months[-1][1]) <= self.summerSolstice:
            self.months.append((self.months[-1][1], ephem.next_new_moon(ephem.date(self.months[-1][1].datetime()+datetime.timedelta(days=1))), 'Frühlingsmond %s' %number)) 
            number += 1
        self.months.append((self.months[-1][1], ephem.next_new_moon(ephem.date(self.months[-1][1].datetime()+datetime.timedelta(days=1))), 'Sommermond')) 
        number = 2
        while ephem.next_full_moon(self.months[-1][1]) <= self.autumnEquinox:
            self.months.append((self.months[-1][1], ephem.next_new_moon(ephem.date(self.months[-1][1].datetime()+datetime.timedelta(days=1))), 'Sommermond %s' %number)) 
            number += 1
        number = 2
        self.months.append((self.months[-1][1], ephem.next_new_moon(ephem.date(self.months[-1][1].datetime()+datetime.timedelta(days=1))), 'Herbstmond'))
        while ephem.next_full_moon(self.months[-1][1]) <= self.winterSolstice:
            self.months.append((self.months[-1][1], ephem.next_new_moon(ephem.date(self.months[-1][1].datetime()+datetime.timedelta(days=1))), 'Herbstmond %s' %number)) 
            number += 1
        number = 2
        self.months.append((self.months[-1][1], ephem.next_new_moon(ephem.date(self.months[-1][1].datetime()+datetime.timedelta(days=1))), 'Wintermond'))
        while ephem.next_full_moon(self.months[-1][1]) <= self.nextSpringEquinox:
            self.months.append((self.months[-1][1], ephem.next_new_moon(ephem.date(self.months[-1][1].datetime()+datetime.timedelta(days=1))), 'Wintermond %s' %number)) 
            number += 1
        
        currYear = year-1
        self.vollmondeLiliusClavius = []
        prevMonth = 0
        for yearCall in range(year-1, year+2): # einen genügend großen Bereich generieren
            for day, month in [x for x in getVollmondeNachClaviusLilius(yearCall)]:
                if month < prevMonth:
                    currYear += 1
                prevMonth = month
                self.vollmondeLiliusClavius.append( (day, month, currYear) )
        
    def getMonth(self, ephemDate=ephem.now()):
        for i in range(len(self.months)):
            if self.months[i+1][0] >= ephemDate:
                return self.months[i][2]
            
    def getBabylonianMonthLiliusClavius(self, ephemDate=ephem.now()):
        for i in range(len(self.months)):
            if self.months[i+1][0] >= ephemDate:
                return self.getBabylonianMonthNameLiliusClavius(self.months[i][0])
    
    @classmethod   
    def getBabylonianMonthNameAstronomical(cls, beginOfMonth, checkForLeapMonth=True):
        # dieses Konzept funktioniert nicht, weil der Abstand zwischen zwei astronomischen Vollmonden tatsächlich manchmal größer als ein 1/12 Jahr sein kann und damit Monate übersprungen werden
        location = ephem.Observer()
        location.lon, location.lat  = '13.066667', '50.75' # Ergebnis sollte unabhängig von der Position sein
        nextFullMoon = ephem.next_full_moon(beginOfMonth)
        location.date = nextFullMoon
        sun = ephem.Sun()
        sun.compute(location)
        
        bla = float(sun.a_ra)
        index = int(float(sun.a_ra) * 12.0 / 2.0 / math.pi)
        monthName = ['Nisannu', 'Ajaru', 'Simanu', 'Du\'uzu', 'Abu', 'Ululu', 'Tašritu', 'Araḫsamna', 'Kislimu', 'Tebetu', 'Šabatu', 'Addaru',][index]
        if not checkForLeapMonth:
            return monthName
        monthNameBefore = cls.getBabylonianMonthNameAstronomical(beginOfMonth-28.0, False)
        if monthNameBefore == monthName:
            return monthName + ' 2'
        monthNameAfter = cls.getBabylonianMonthNameAstronomical(beginOfMonth+28.0, False)
        if monthNameAfter == monthName:
            return monthName + ' 1'
        return monthName  
    
    def getBabylonianMonthNameLiliusClavius(self, beginOfMonth, checkForLeapMonth=True):
        beginOfMonthDatetime = ephemDateToDatetimeAtTimeZone(beginOfMonth, ZoneInfo('Europe/Berlin'))
        for (day, month, year) in self.vollmondeLiliusClavius:
            compareDatetime = datetime.datetime(year=year, month=month, day=day)
            if compareDatetime > beginOfMonthDatetime:
                break
       
        if (month == 3 and day >= 21) or (month == 4 and day <= 20):
            monthName = 'Nisannu'
        elif (month == 4 and day >= 21) or (month == 5 and day <= 21):
            monthName = 'Ajaru'
        elif (month == 5 and day >= 22) or (month == 6 and day <= 21):
            monthName = 'Simanu'
        elif (month == 6 and day >= 22) or (month == 7 and day <= 23):
            monthName = 'Du\'uzu'
        elif (month == 7 and day >= 23) or (month == 8 and day <= 22):
            monthName = 'Abu'
        elif (month == 8 and day >= 23) or (month == 9 and day <= 22):
            monthName = 'Ululu'
        elif (month == 9 and day >= 23) or (month == 10 and day <= 22):
            monthName = 'Tašritu'
        elif (month == 10 and day >= 23) or (month == 11 and day <= 22):
            monthName = 'Araḫsamna'
        elif (month == 11 and day >= 23) or (month == 12 and day <= 20):
            monthName = 'Kislimu'
        elif (month == 12 and day >= 21) or (month == 1 and day <= 19):
            monthName = 'Tebetu'
        elif (month == 1 and day >= 20) or (month == 2 and day <= 18):
            monthName = 'Šabatu'
        elif (month == 2 and day >= 19) or (month == 3 and day <= 20):
            monthName = 'Addaru'
        else:
            print('Fehler', day, month)
        
        if not checkForLeapMonth:
            return monthName
        monthNameBefore = self.getBabylonianMonthNameLiliusClavius(ephem.Date(beginOfMonth-28.0), False)
        if monthNameBefore == monthName:
            return monthName + ' 2'
        monthNameAfter = self.getBabylonianMonthNameLiliusClavius(ephem.Date(beginOfMonth+28.0), False)
        if monthNameAfter == monthName:
            return monthName + ' 1'
        return monthName  
    
          
    def generateMoonCalender(self, location) -> str:
        outstring = 'Monat\tbabyl. Name\tNeumond\tVollmond\tvollster Mond\tLänge des Mondtages bei Vollmond\tMondhelligkeit\n'
        for (begin, end, name) in self.months:
            moon = ephem.Moon()

            outstring += name + '\t'
            outstring += self.getBabylonianMonthNameLiliusClavius(begin) + '\t'
            outstring += datetimeToString(ephemDateToDatetimeAtTimeZone(begin, ZoneInfo('Europe/Berlin')), False) + '\t'
            
            nextFullMoon = ephem.next_full_moon(begin)
            location.date = nextFullMoon
            
            nextTransit = location.next_transit(moon)
            previousTransit = location.previous_transit(moon)
            
            if nextTransit - nextFullMoon < nextFullMoon - previousTransit:
                relevantTransit = nextTransit
            else: 
                relevantTransit = previousTransit
            location.date = relevantTransit
            
            previousMoonrise = location.previous_rising(moon)
            nextMoonset = location.next_setting(moon)
            
            #outstring += ephem.to_timezone(nextFullMoon, ZoneInfo('Europe/Berlin')).strftime('%d.%m.%y %H:%M:%S') + '\t'
            outstring += datetimeToString(ephemDateToDatetimeAtTimeZone(nextFullMoon, ZoneInfo('Europe/Berlin')), False) + '\t'
            #outstring += ephem.to_timezone(relevantTransit, ZoneInfo('Europe/Berlin')).strftime('%d.%m.%y %H:%M:%S') + '\t'
            outstring += datetimeToString(ephemDateToDatetimeAtTimeZone(relevantTransit, ZoneInfo('Europe/Berlin')), False) + '\t'
            outstring += str(nextMoonset.datetime()-previousMoonrise.datetime())[:-10]+'h\t'

            moon.compute(nextFullMoon)
            averageDistanceMoonKm = 381
            percentage = -int((moon.earth_distance*1.495979e+5-averageDistanceMoonKm) / averageDistanceMoonKm *200.0 + 0.5)
            outstring += ('+' if percentage>0 else '') + str(percentage) + ' %'

            outstring += '\n'
        return outstring        

      
if __name__ == '__main__':
    year = 2029
    calendar = MoonCalendar(year)
   
    #Zschopau
    location = ephem.Observer()
    location.lon, location.lat  = '13.066667', '50.75'

    with open('%s.txt' %year, 'w', encoding='utf-8') as outfile:
        outfile.write(calendar.generateMoonCalender(location))
    