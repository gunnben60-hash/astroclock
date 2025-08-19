import datetime
import ephem
from backports.zoneinfo import ZoneInfo

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
        self.months.append((ephem.previous_new_moon(referencedate), ephem.next_new_moon(referencedate), 'letzter Wintermond')) 
        number = 2
        while ephem.next_full_moon(self.months[-1][1]) <= self.springEquinox:
            self.months.append((self.months[-1][1], ephem.next_new_moon(ephem.date(self.months[-1][1].datetime()+datetime.timedelta(days=1))), 'letzer Wintermond %s' %number)) 
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
        
    def getMonth(self, ephemDate=ephem.now()):
        for i in range(len(self.months)):
            if self.months[i+1][0] >= ephemDate:
                return self.months[i][2]
            
    def generateMoonCalender(self, location) -> str:
        outstring = 'Monat\tNeumond\tVollmond\tvollster Mond\tLänge des Mondtages bei Vollmond\tMondhelligkeit\n'
        for (begin, end, name) in self.months:
            moon = ephem.Moon()

            outstring += name + '\t'
            outstring += ephem.to_timezone(begin, ZoneInfo('Europe/Berlin')).strftime('%d.%m.%y %H:%M:%S') + '\t'
            
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
            
            outstring += ephem.to_timezone(nextFullMoon, ZoneInfo('Europe/Berlin')).strftime('%d.%m.%y %H:%M:%S') + '\t'
            outstring += ephem.to_timezone(relevantTransit, ZoneInfo('Europe/Berlin')).strftime('%d.%m.%y %H:%M:%S') + '\t'
            outstring += str(nextMoonset.datetime()-previousMoonrise.datetime())[:-10]+'h\t'

            moon.compute(nextFullMoon)
            averageDistanceMoonKm = 381
            percentage = -int((moon.earth_distance*1.495979e+5-averageDistanceMoonKm) / averageDistanceMoonKm *200.0 + 0.5)
            outstring += ('+' if percentage>0 else '') + str(percentage) + ' %'

            outstring += '\n'
        return outstring        

      
if __name__ == '__main__':
    calendar = MoonCalendar()
    print(calendar.getMonth())
    
    #Zschopau
    location = ephem.Observer()
    location.lon, location.lat  = '13.066667', '50.75'

    #print(moon.phase)

    
    with open('2025.txt', 'w') as outfile:
        outfile.write(calendar.generateMoonCalender(location))