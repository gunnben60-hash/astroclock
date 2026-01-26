

#year = 2041
#year = 2025
year = 2011

outstring = ''
outstring2 = ''

neulichtSpezialfall = {
    1: 6,
    2: 4,
    3: 6,
    4: 4,
    5: 4,
    6: 2, 
    7: [2, 31],
    8: 30, 
    9: 28,
    10: 28,
    11: 26,
    12: 26       
}

def getFrühlingsvollmondNachEpakte(year):
    goldeneZahl = year % 19 + 1
    julianischeEpakte = (11 * (goldeneZahl - 1)) % 30
    c = int(year/100.0)
    S = int(3.0*(c+1.0)/4.0)
    L = int((8.0*c+13.0)/25.0)
    gregorianischeEpakte = (julianischeEpakte - S + L + 8) % 30

    # Frühlingsvollmond nach Epakte
    # https://www.tondering.dk/claus/cal/easter.php?spm=a2ty_o01.29997173.0.0.737b5171zMKwE0
    frühlingsvollmondNachEpakte = [
        '04-13',
        '04-12',
        '04-11',
        '04-10',
        '04-09',
        '04-08',
        '04-07',
        '04-06',
        '04-05',
        '04-04',
        '04-03',
        '04-02',
        '04-01',
        '03-31',
        '03-30',
        '03-29',
        '03-28',
        '03-27',
        '03-26',
        '03-25',
        '03-24',
        '03-23',
        '03-22',
        '03-21',
        '04-18',
        '04-18',
        '04-17',
        '04-16',
        '04-15',
        '04-14',
        '04-13',
    ]
    if goldeneZahl > 11:
        frühlingsvollmondNachEpakte[25] = '04-17'
        
    return frühlingsvollmondNachEpakte[gregorianischeEpakte]

# https://ems.press/content/serial-article-files/45579
def getFrühlingsvollmondNachClaviusLilius(year):
    
    goldeneZahl = year % 19 + 1
    julianischeEpakte = (11 * (goldeneZahl - 1)) % 30
    c = int(year/100.0)
    S = int(3.0*(c+1.0)/4.0)
    L = int((8.0*c+13.0)/25.0)
    gregorianischeEpakte = (julianischeEpakte - S + L + 8) % 30
    
    neulichtKalenderClaviusLilius = {
        1: [0, 29, 28, 27, 26, 25, 24, 23, 22, 21, 20, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0],
        2: [29, 28, 27, 26, [25, 24], 23, 22, 21, 20, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1],
        3: [0, 29, 28, 27, 26, 25, 24, 23, 22, 21, 20, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0],
        4: [29, 28, 27, 26, [25, 24], 23, 22, 21, 20, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0, 29],
        5: [28, 27, 26, 25, 24, 23, 22, 21, 20, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0, 29, 28],
        6: [27, 26, [25, 24], 23, 22, 21, 20, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0, 29, 28, 27],
        7: [26, 25, 24, 23, 22, 21, 20, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0, 29, 28, 27, 26],
        8: [[25, 24], 23, 22, 21, 20, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0, 29, 28, 27, 26, 25, 24],
        9: [23, 22, 21, 20, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0, 29, 28, 27, 26, [25, 24], 23],
        10: [22, 21, 20, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0, 29, 28, 27, 26, 25, 24, 23, 22],
        11: [21, 20, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0, 29, 28, 27, 26, [25, 24], 23, 22, 21],
        12: [20, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0, 29, 28, 27, 26, 25, 24, 23, 22, 21, 20]
    }

    if gregorianischeEpakte == 25 and goldeneZahl > 11:
        month = 4
        dayMinusOne = neulichtSpezialfall[month] - 1
    else:
        for month in [3,4]:
            stop = False
            for dayMinusOne in range(31):
                if month == 3 and dayMinusOne < 7:
                    continue
                epact = neulichtKalenderClaviusLilius[month][dayMinusOne]
                if type(epact) == type([]):
                    if epact[0] == gregorianischeEpakte or epact[1] == gregorianischeEpakte:
                        stop = True
                        break    
                else:
                    if epact == gregorianischeEpakte:
                        stop = True
                        break
            if stop:
                break
                
    # Vollmond ist 13 Tage nach dem Neulicht
    day = dayMinusOne + 14
    if day > 31:
        day = day - 31
        month += 1
    return '0' + str(month) + '-' + '{:02d}'.format(day)


def adjustDay(day, month):
    monthLength = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    if day == 0:
        month -= 1
        day = monthLength[month-1]
        if month < 1:
            month = 12
    if day > monthLength[month-1]:
        day -= monthLength[month-1]
        month += 1
        if month > 12:
            month = 1
    return day, month

# https://ems.press/content/serial-article-files/45579
def getNeumondeNachClaviusLilius(year):
    
    global outstring2
    
    goldeneZahl = year % 19 + 1
    julianischeEpakte = (11 * (goldeneZahl - 1)) % 30
    c = int(year/100.0)
    S = int(3.0*(c+1.0)/4.0)
    L = int((8.0*c+13.0)/25.0)
    gregorianischeEpakte = (julianischeEpakte - S + L + 8) % 30
    
    neulichtKalenderClaviusLilius = {
        1: [0, 29, 28, 27, 26, 25, 24, 23, 22, 21, 20, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0],
        2: [29, 28, 27, 26, [25, 24], 23, 22, 21, 20, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1],
        3: [0, 29, 28, 27, 26, 25, 24, 23, 22, 21, 20, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0],
        4: [29, 28, 27, 26, [25, 24], 23, 22, 21, 20, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0, 29],
        5: [28, 27, 26, 25, 24, 23, 22, 21, 20, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0, 29, 28],
        6: [27, 26, [25, 24], 23, 22, 21, 20, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0, 29, 28, 27],
        7: [26, 25, 24, 23, 22, 21, 20, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0, 29, 28, 27, 26],
        8: [[25, 24], 23, 22, 21, 20, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0, 29, 28, 27, 26, 25, 24],
        9: [23, 22, 21, 20, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0, 29, 28, 27, 26, [25, 24], 23],
        10: [22, 21, 20, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0, 29, 28, 27, 26, 25, 24, 23, 22],
        11: [21, 20, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0, 29, 28, 27, 26, [25, 24], 23, 22, 21],
        12: [20, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0, 29, 28, 27, 26, 25, 24, 23, 22, 21, 20]
    }

    if gregorianischeEpakte == 25 and goldeneZahl > 11:
        for month in range(1, 13):
            if type(neulichtSpezialfall[month]) == type([]):
                for day in neulichtSpezialfall[month]:
                    dayMinusOne = day - 1
                    result=adjustDay(dayMinusOne, month)
                    yield result
            else:
                dayMinusOne = neulichtSpezialfall[month] - 1
                result=adjustDay(dayMinusOne, month)
                yield result
    else:
        for month in range(1, 13):
            for dayMinusOne in range(31):
                if len(neulichtKalenderClaviusLilius[month]) < dayMinusOne+1:
                    continue
                epact = neulichtKalenderClaviusLilius[month][dayMinusOne]
                if type(epact) == type([]):
                    if epact[0] == gregorianischeEpakte or epact[1] == gregorianischeEpakte:
                        yield adjustDay(dayMinusOne, month)
                else:
                    if epact == gregorianischeEpakte:
                        if not (dayMinusOne==0 and month == 1):
                            yield adjustDay(dayMinusOne, month)
                            
                            
def calcVollmondFromNeulicht(dayMinusOne, month):
    # Vollmond ist 13 Tage nach dem Neulicht
    day = dayMinusOne + 14
    return adjustDay(day, month)
    
                            
# https://ems.press/content/serial-article-files/45579
def getVollmondeNachClaviusLilius(year):
    
    global outstring
    
    goldeneZahl = year % 19 + 1
    julianischeEpakte = (11 * (goldeneZahl - 1)) % 30
    c = int(year/100.0)
    S = int(3.0*(c+1.0)/4.0)
    L = int((8.0*c+13.0)/25.0)
    gregorianischeEpakte = (julianischeEpakte - S + L + 8) % 30
    
    neulichtKalenderClaviusLilius = {
        1: [0, 29, 28, 27, 26, 25, 24, 23, 22, 21, 20, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0],
        2: [29, 28, 27, 26, [25, 24], 23, 22, 21, 20, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1],
        3: [0, 29, 28, 27, 26, 25, 24, 23, 22, 21, 20, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0],
        4: [29, 28, 27, 26, [25, 24], 23, 22, 21, 20, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0, 29],
        5: [28, 27, 26, 25, 24, 23, 22, 21, 20, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0, 29, 28],
        6: [27, 26, [25, 24], 23, 22, 21, 20, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0, 29, 28, 27],
        7: [26, 25, 24, 23, 22, 21, 20, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0, 29, 28, 27, 26],
        8: [[25, 24], 23, 22, 21, 20, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0, 29, 28, 27, 26, 25, 24],
        9: [23, 22, 21, 20, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0, 29, 28, 27, 26, [25, 24], 23],
        10: [22, 21, 20, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0, 29, 28, 27, 26, 25, 24, 23, 22],
        11: [21, 20, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0, 29, 28, 27, 26, [25, 24], 23, 22, 21],
        12: [20, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0, 29, 28, 27, 26, 25, 24, 23, 22, 21, 20]
    }

    if gregorianischeEpakte == 25 and goldeneZahl > 11:
        for month in range(1, 13):
            if type(neulichtSpezialfall[month]) == type([]):
                for day in neulichtSpezialfall[month]:
                    dayMinusOne = day - 1
                
                    outstring += str(adjustDay(dayMinusOne, month))
                    result = calcVollmondFromNeulicht(dayMinusOne, month)
                    outstring += ' ' + str(result) + '\n'
                    yield result 
            else:
                dayMinusOne = neulichtSpezialfall[month] - 1
                
                outstring += str(adjustDay(dayMinusOne, month))
                result = calcVollmondFromNeulicht(dayMinusOne, month)
                outstring += ' ' + str(result) + '\n'
                yield result 
    else:
        for month in range(1, 13):
            for dayMinusOne in range(31):
                if len(neulichtKalenderClaviusLilius[month]) < dayMinusOne+1:
                    continue
                epact = neulichtKalenderClaviusLilius[month][dayMinusOne]
                if type(epact) == type([]):
                    if epact[0] == gregorianischeEpakte or epact[1] == gregorianischeEpakte:
                        outstring += str(adjustDay(dayMinusOne, month))
                        result = calcVollmondFromNeulicht(dayMinusOne, month)
                        outstring += ' ' + str(result) + '\n'
                        yield result 
                else:
                    if epact == gregorianischeEpakte:
                        outstring += str(adjustDay(dayMinusOne, month))
                        result = calcVollmondFromNeulicht(dayMinusOne, month)
                        outstring += ' ' + str(result) + '\n'
                        yield result 
            

for year in range(1970, 2100):
    goldeneZahl = year % 19 + 1
    julianischeEpakte = (11 * (goldeneZahl - 1)) % 30
    c = int(year/100.0)
    S = int(3.0*(c+1.0)/4.0)
    L = int((8.0*c+13.0)/25.0)
    gregorianischeEpakte = (julianischeEpakte - S + L + 8) % 30
    
    value1 = getFrühlingsvollmondNachEpakte(year)
    value2 = getFrühlingsvollmondNachClaviusLilius(year)
    print(year, value1, value2, 'error' if value1 != value2 else '', S, L)




countNeumonde = {}
countVollmonde = {}
for year in range(1970, 2100):
    outstring += str(year) + '\n'
    for neumond in getNeumondeNachClaviusLilius(year):
        if not neumond in countNeumonde:
            countNeumonde[neumond] = 0
        countNeumonde[neumond] += 1
        
    for vollmond in getVollmondeNachClaviusLilius(year):
        if not vollmond in countVollmonde:
            countVollmonde[vollmond] = 0
        if vollmond == (25, 11):
            print('HIER', year)
        countVollmonde[vollmond] += 1

with open('result.txt', 'w') as outfile:
    outfile.write(outstring)
    
year = 2033  
print([x for x in getVollmondeNachClaviusLilius(year)])    
pass


monthLength = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
calendar = {x: [] for x in range(1, 13)}
for month in calendar:
    calendar[month] = monthLength[month-1]*['']

for year in range(2000, 2019):
    goldenNumber = year % 19
    if goldenNumber == 0:
        goldenNumber = 19
    for neumond in getNeumondeNachClaviusLilius(year):
        day, month = neumond
        calendar[month][day-1] = '⚫' + str(goldenNumber)
        
for month in calendar:
    for i in range(len(calendar[month])):
        calendar[month][i] += (4 - len(calendar[month][i] )) * ' '
        
        
for year in range(2000, 2019):
    goldenNumber = year % 19
    if goldenNumber == 0:
        goldenNumber = 19
    previousMonth = 0
    for neumond in getVollmondeNachClaviusLilius(year):
        day, month = neumond
        if month < previousMonth:
            goldenNumber += 1
        previousMonth = month
        calendar[month][day-1] += '⚪' + str(goldenNumber)

for month in calendar:
    for i in range(len(calendar[month])):
        calendar[month][i] += (7 - len(calendar[month][i] )) * ' '

outstring = ''
monthNames = ['Januar', 'Februar', 'März', 'April', 'Mai', 'Juni', 'Juli', 'August', 'September', 'Oktober', 'November', 'Dezember']

for month in range(1,13):
    outstring += monthNames[month-1] + '\n'
    for i in range(len(calendar[month])):
        outstring += '{:02d}'.format(i+1) + calendar[month][i] + '\n'
    outstring += '\n\n'

with open('calendar.txt', 'w', encoding='utf8') as outfile:
    outfile.write(outstring)