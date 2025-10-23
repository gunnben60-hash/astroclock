import datetime
import ephem
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
            #outstring += ephem.to_timezone(begin, ZoneInfo('Europe/Berlin')).strftime('%d.%m.%y %H:%M:%S') + '\t'
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
    calendar = MoonCalendar()
    print(calendar.getMonth())
    
    #Zschopau
    location = ephem.Observer()
    location.lon, location.lat  = '13.066667', '50.75'

    #print(moon.phase)

    goldenNumbers = {'03':{}, '04':{}}
    goldenNumbers['04']['14'] = 1
    goldenNumbers['04']['03'] = 2
    goldenNumbers['03']['23'] = 3
    goldenNumbers['04']['11'] = 4
    goldenNumbers['03']['31'] = 5
    goldenNumbers['04']['19'] = 6
    goldenNumbers['04']['08'] = 7
    goldenNumbers['03']['28'] = 8
    goldenNumbers['04']['16'] = 9
    goldenNumbers['04']['05'] = 10
    goldenNumbers['03']['25'] = 11
    goldenNumbers['04']['13'] = 12
    goldenNumbers['04']['02'] = 13
    goldenNumbers['03']['22'] = 14
    goldenNumbers['04']['10'] = 15
    goldenNumbers['03']['30'] = 16
    goldenNumbers['04']['18'] = 17
    goldenNumbers['04']['07'] = 18
    goldenNumbers['03']['27'] = 19
    print(len(goldenNumbers['04']) + len(goldenNumbers['03']))

    neumondTermine = {}
    vollmondTermine = {}
    frühlingsMonde = {}
    for i in range(1900, 2200):
        yearstring  = "{:04d}".format(i) 
        calendar = MoonCalendar(i)
        result = calendar.generateMoonCalender(location)
        for line in result.split('\n'):
            zeile = line.split('\t')
            if len(zeile) < 2:
                continue
            neumond = zeile[1]
            vollmond = zeile[2]
            if '.'+yearstring+' ' in neumond:
                day, month, year = neumond.split(' ')[0].split('.')
                if not month in neumondTermine:
                    neumondTermine[month] = {}
                if not day in neumondTermine[month]:
                    neumondTermine[month][day] = []
                neumondTermine[month][day].append(neumond)
            if '.'+yearstring+' ' in vollmond:
                day, month, year = vollmond.split(' ')[0].split('.')
                if not month in vollmondTermine:
                    vollmondTermine[month] = {}
                if not day in vollmondTermine[month]:
                    vollmondTermine[month][day] = []
                vollmondTermine[month][day].append(vollmond)
                if (int(month) == 3 and int(day) >= 21) or (int(month) == 4 and int(day) <= 18):
                    if not month in frühlingsMonde:
                        frühlingsMonde[month] = {}
                    if not day in frühlingsMonde[month]:
                        frühlingsMonde[month][day] = []
                    frühlingsMonde[month][day].append(vollmond)
    
    outstring = 'Datum\tgoldene Zahl\tAnzahl\n'
    for month in sorted(frühlingsMonde.keys()):
        for day in sorted(frühlingsMonde[month].keys()):
            outstring += day + '.' + month + '\t'
            if day in goldenNumbers[month]:
                outstring += str(goldenNumbers[month][day]) + '\t'
            else:
                outstring += '\t'
            outstring += str(len(frühlingsMonde[month][day])) + '\n'
    with open('Frühlingsmonde.txt', 'w') as outfile:
        outfile.write(outstring)

    pass
    '''
    with open('2025.txt', 'w') as outfile:
        outfile.write(calendar.generateMoonCalender(location))
    '''