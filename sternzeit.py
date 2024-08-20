import datetime
import ephem
import math

# mittlere lokale Sternzeit nach https://squarewidget.com/astronomical-calculations-sidereal-time/
# Korrektur zu wahrer lokalen Sternzeit nach https://www.hcgreier.at/astronomie_at/sternzeit/

def julianDay(utc: datetime) -> float:
    year = utc.year
    month = utc.month
    day = utc.day
    hour = utc.hour
    minute = utc.minute
    second = utc.second + utc.microsecond / 1000000.0
    if month < 3:
        month += 12
        year -= 1
    a = int(year/100.0) 
    b = 2 - a + int(a/4.0)
    julianDay = int(365.25*(year+4716)) + int(30.6001*(month+1))  + day + hour/24.0 + minute/1440.0 + second/86400.0 + b - 1524.5
    return julianDay

def siderialTime(utc: datetime, longitude: float):
    jD = julianDay(utc)
    T = (jD - 2451545.0) / 36525.0
    theta0InDegree = (280.46061837 + 360.98564736629 * (jD - 2451545.0) + (0.000387933 * T * T) - (T * T * T / 38710000.0)) % 360.0
    
    # (mittlere lokale Sternzeit)
    localThetaInDegree = theta0InDegree + longitude
    localThetaInTimeSeconds = localThetaInDegree / 360.0 * 24.0 * 60.0 * 60.0
    
    # (Korrektur)
    epsilon = 23.43609/180.0 * math.pi # Schiefe der Ekliptik
    omega = (125.04452 
             - 1934.136261*T
             + 0.0020708 *T*T
             + T*T*T/450000.0)/180.0*math.pi
    l = (280.4665 + 36000.7698*T)/180.0*math.pi
    lstrich = (218.3165+481267.8813*T)/189.0*math.pi
    deltaPhi = (-17.20 * math.sin(omega) 
                -1.32*math.sin(2.0*l)
                -0.23*math.sin(2.0*lstrich)
                +0.21*math.sin(2.0*omega))
    deltaTInS = deltaPhi * math.cos(epsilon) / 15.0
    
    # wahre lokale Sternzeit
    realLocalThetaInTimeSeconds = localThetaInTimeSeconds + deltaTInS
    hour = realLocalThetaInTimeSeconds // 3600.0
    minute = (realLocalThetaInTimeSeconds - hour*3600) // 60.0
    second = realLocalThetaInTimeSeconds - hour*3600 - minute * 60.0
    
    return(hour, minute, second)

def compareSiderialTimeWithEphem():
    now = datetime.datetime.now().astimezone(datetime.timezone.utc)
    #bla = bla.replace(year=1957, month=10, day=4, hour=19, minute=29, second=0, microsecond=0)
    
    location = ephem.Observer()
    location.lon, location.lat  = '13.066667', '50.75'
    
    testTime = datetime.datetime.now().astimezone(datetime.timezone.utc)

    n = 0
    devSquare = 0.0
    devMax = 0.0
    while (testTime - now).days < 1000:
        hour, minute, second = siderialTime(testTime, 13.066667)
        if hour == 24:
            hour = 0
       
        location.date = ephem.date(testTime)
        hour1, minute1, second1 = [float(x) for x in str(location.sidereal_time()).split(':')]
        
        diff = abs( (hour1-hour)*3600.0+(minute1-minute)*60.0+second1-second)
        if (diff > 1.0):
            pass
        devSquare += diff*diff
        devMax = max(devMax, diff)
        n += 1
        
        testTime += datetime.timedelta(hours = 1)
        
    print('Mean error [s]: ', math.sqrt(devSquare / n))
    print('Max error [s]: ', devMax)
    
compareSiderialTimeWithEphem()

    


                
    
    