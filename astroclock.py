import datetime
import ephem
import math
import os
import sys
import threading
import time
from PyQt5 import QtCore, QtGui, QtWidgets, uic 
from PyQt5.QtCore import Qt
from sonneundmond import getLines

def findRootByBisection(arg1, arg2, delta, f):
    argM = 0.5*(arg1 + arg2)
    if abs(arg1-arg2) < delta:
        return argM

    y1 = f(arg1)
    y2 = f(arg2)
    yM = f(argM)

    if (y1 > 0) == (yM > 0):
        return findRootByBisection(argM, arg2, delta, f)
    else:
        return findRootByBisection(arg1, argM, delta, f)

   
            


SUN = ephem.Sun()
MOON = ephem.Moon()

LON = 13.066667
LAT = 50.75
TIMEZONE = 'Europe/Berlin'
SIMULATE = False
SHOW_PLANETS = False
SIMULATION_REDRAW_IN_S = 1
SIMULATION_TIME_STEP_IN_S = 3600
CONFIG_FILE_NAME = 'astroclock.location'
if os.path.exists(CONFIG_FILE_NAME):
    with open(CONFIG_FILE_NAME) as infile:
        data = infile.read().strip().split('\n')
        for line in data:
            zeile = [x.strip() for x in line.split('=')]
            if zeile[0].upper() == 'LON':
                LON = float(zeile[1])
            elif zeile[0].upper() == 'LAT':
                LAT = float(zeile[1])
            elif zeile[0].upper() == 'TIMEZONE':
                TIMEZONE = zeile[1]
            elif zeile[0].upper() == 'SIMULATE':
                SIMULATE = (zeile[1].lower() == 'true')
            elif zeile[0].upper() == 'SIMULATION_REDRAW_IN_S':
                SIMULATION_REDRAW_IN_S = int(zeile[1])
            elif zeile[0].upper() == 'SIMULATION_TIME_STEP_IN_S':
                SIMULATION_TIME_STEP_IN_S = int(zeile[1])
            elif zeile[0].upper() == 'SHOW_PLANETS':
                SHOW_PLANETS = (zeile[1].lower() == 'true')
else:
    with open(CONFIG_FILE_NAME, 'w') as outfile:
        outfile.write('LON='+str(LON)+'\n')
        outfile.write('LAT='+str(LAT)+'\n')
        outfile.write('TIMEZONE='+str(TIMEZONE)+'\n')
        outfile.write('SIMULATE='+str(SIMULATE)+'\n')
        outfile.write('SIMULATION_REDRAW_IN_S='+str(SIMULATION_REDRAW_IN_S)+'\n')
        outfile.write('SIMULATION_TIME_STEP_IN_S='+str(SIMULATION_TIME_STEP_IN_S)+'\n')
        outfile.write('SHOW_PLANETS='+str(SHOW_PLANETS)+'\n')

LOCATION = ephem.Observer()
LOCATION.lon, LOCATION.lat  = str(LON), str(LAT)

SIZE = 600
RIM_1 = 20
RIM_PLANET = 10
TEXT_HEIGHT = 270
SYMBOL_CLOCK = ['XII', 'I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X', 'XI', 'XII', 'I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X', 'XI']
SYMBOL_ZODIAC = ['♈︎', '♉︎', '♊︎', '♋︎', '♌︎', '♍︎', '♎︎', '♏︎', '♐︎', '♑︎', '♒︎', '♓︎']
SYMBOL_LUNAR_NODES = ['☊', '☋']
PLANETS = [(ephem.Mercury(), '☿'), (ephem.Venus(), '♀'), (ephem.Mars(), '♂'), (ephem.Jupiter(), '♃'), (ephem.Saturn(), '♄')]
DELTA_DECLINATION_SUN = 0.2

    

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        self.label = QtWidgets.QLabel()
        canvas = QtGui.QPixmap(SIZE, SIZE + TEXT_HEIGHT)
        canvas.fill(Qt.white)
        self.label.setPixmap(canvas)
        self.globalTime = None
        
        self.drawAll()
        
    def drawAll(self):
        if not SIMULATE or self.globalTime is None:
            self.globalTime = ephem.now()
        else:
            self.globalTime = ephem.Date(self.globalTime.datetime() + datetime.timedelta(seconds=SIMULATION_TIME_STEP_IN_S))
        #self.globalTime = ephem.Date(datetime.datetime(2025, 6, 25, 10, 7, 0))
        self.clear()
        self.setCentralWidget(self.label)
        self.drawBackground()
        self.drawZodiac()
        if SHOW_PLANETS:
            self.drawPlanets()
        self.drawMoonNodes()
        self.drawMoon()
        self.drawSun()
        self.fillText()
        
    def clear(self):
        painter = QtGui.QPainter(self.label.pixmap())
        painter.fillRect(0, 0, SIZE, SIZE + TEXT_HEIGHT, Qt.white)

    def fillText(self):
        LOCATION.date = self.globalTime
       
        painter = QtGui.QPainter(self.label.pixmap())
        pen = QtGui.QPen()
        pen.setColor(Qt.black)
        pen.setWidth(1)
        painter.setPen(pen)
        
        font=QtGui.QFont()
        font.setPixelSize(12)
        painter.setFont(font)

        text = []
        counter = 0
        for line in getLines(LOCATION, TIMEZONE, self.globalTime):
            if counter < 5 and ':' in line:
                line = line[:-3]
            counter += 1
            zeile = []
            for word in line.split('\t'):
                temp = word.strip()
                if temp:
                    zeile.append(temp)
            text.append(zeile)
        for i in range(len(text)-1):
            if len(text[i]) < 1:
                continue
            painter.drawText(RIM_1, SIZE + RIM_1 + i*15, text[i][0])
            if len(text[i]) < 2:
                continue
            painter.drawText(200, SIZE + RIM_1 + i*15, text[i][1])

        painter.end()

    def drawBackground(self):
        painter = QtGui.QPainter(self.label.pixmap())
        pen = QtGui.QPen()
        pen.setColor(Qt.blue)
        pen.setWidth(1)
        painter.setPen(pen)
        
        painter.drawEllipse(RIM_1, RIM_1, SIZE-2*RIM_1, SIZE-2*RIM_1)
        
        font=QtGui.QFont()
        font.setPixelSize(20)
        painter.setFont(font)
        
        for i in range(24):
            angle = 2.0 * math.pi / 24.0 * i
            deltaX1 = int(math.sin(angle) * SIZE / 2.0 +0.5)
            deltaY1 = int(math.cos(angle) * SIZE / 2.0 +0.5) 
            deltaX2 = int(math.sin(angle) * (SIZE / 2.0 - RIM_1) +0.5)
            deltaY2 = int(math.cos(angle) * (SIZE / 2.0 - RIM_1) +0.5) 
            painter.drawLine(SIZE // 2 - deltaX2, SIZE // 2 + deltaY2, SIZE // 2 - deltaX1, SIZE // 2 + deltaY1)
            
            deltaX3 = int(math.sin(angle) * (SIZE / 2.0 - 2*RIM_1) +0.5)
            deltaY3 = int(math.cos(angle) * (SIZE / 2.0 - 2*RIM_1) +0.5)
            
            painter.save()
            painter.translate(SIZE // 2 - deltaX3, SIZE // 2 + deltaY3)
            painter.rotate(180+i*15)
            painter.drawText(-RIM_1//2, RIM_1//2, SYMBOL_CLOCK[i])
            painter.restore()
            
        painter.setPen(Qt.yellow)
        
        sizeEquinox = int(SIZE * 0.6)
        painter.drawEllipse( (SIZE - sizeEquinox)//2 , (SIZE - sizeEquinox)//2, sizeEquinox, sizeEquinox)
        sizeSummerSolstice = int(SIZE * (0.6 + DELTA_DECLINATION_SUN))
        painter.drawEllipse( (SIZE - sizeSummerSolstice)//2 , (SIZE - sizeSummerSolstice)//2, sizeSummerSolstice, sizeSummerSolstice)
        sizeWinterSolstice = int(SIZE * (0.6 - DELTA_DECLINATION_SUN))
        painter.drawEllipse( (SIZE - sizeWinterSolstice)//2 , (SIZE - sizeWinterSolstice)//2, sizeWinterSolstice, sizeWinterSolstice)
        
        phi = math.pi / 180.0 *LAT
        for (hInDegree, color) in [(0.0, Qt.lightGray), (6.0, Qt.gray), (12.0, Qt.darkGray), (18.0, Qt.darkGray)]:
            painter.setPen(color)
            prev = None
            h = - hInDegree / 180.0 * math.pi
            N = 10000
            for i in range(0, N):
                azimut = 2.0 * math.pi / N * i
                declination = math.asin(math.sin(phi)*math.sin(h) - math.cos(phi)*math.cos(azimut)*math.cos(h))
                tau = math.atan2((math.sin(phi)*math.cos(azimut) + math.cos(phi)*math.tan(h)), math.sin(azimut)) + math.pi/2.0
                
                radius = SIZE * (0.6 + declination / math.pi * 180.0 / 23.44 * DELTA_DECLINATION_SUN) / 2.0
                if radius < SIZE/6.0 or radius > SIZE//2 - RIM_1:
                    continue
                deltaX = int(math.sin(tau) * radius +0.5)
                deltaY = int(math.cos(tau) * radius +0.5)
                
                if prev:
                    painter.drawPoint(SIZE // 2 - deltaX, SIZE // 2 + deltaY)
                prev = deltaX, deltaY 
                
        painter.setPen(Qt.yellow)
        prev = None
        h = 0
        N = 10000
        for i in range(0, N):
            azimut = 2.0 * math.pi / N * i
            declination = math.asin(math.sin(phi)*math.sin(h) - math.cos(phi)*math.cos(azimut)*math.cos(h))
            tau = math.atan2((math.sin(phi)*math.cos(azimut) + math.cos(phi)*math.tan(h)), math.sin(azimut)) + math.pi/2.0

            declinationInDegree = declination / math.pi * 180.0
            if declinationInDegree < -23.44 or declinationInDegree > 23.44:
                continue
            
            
            if tau > 0.0 and tau < math.pi:
                pass
            elif tau > math.pi and tau < math.pi * 1.5: 
                pass
            else: 
                continue
            
            delta = (math.pi - tau) / 6.0
            for j in range(-5, 6):
                angle = math.pi + delta*j
                radius = SIZE * (0.6 + declination / math.pi * 180.0 / 23.44 * DELTA_DECLINATION_SUN) / 2.0
                deltaX = int(math.sin(angle) * radius +0.5)
                deltaY = int(math.cos(angle) * radius +0.5)
            
                painter.drawPoint(SIZE // 2 - deltaX, SIZE // 2 + deltaY)
            prev = deltaX, deltaY 
                
        painter.end()
        
        
    def drawZodiac(self):
        LOCATION.date = self.globalTime
        
        painter = QtGui.QPainter(self.label.pixmap())
        painter.setPen(Qt.blue)
        localSize = SIZE//3
        painter.drawEllipse( (SIZE - localSize)//2, (SIZE - localSize)//2, localSize, localSize)
        painter.drawEllipse( (SIZE - localSize)//2 + RIM_1, (SIZE - localSize)//2 + RIM_1, localSize - 2*RIM_1, localSize - 2*RIM_1)
        
        angle0 = float(LOCATION.sidereal_time())
        for i in range(12):
            angle = angle0 - i * 2.0 * math.pi / 12.0
            deltaX1 = int(math.sin(angle) * localSize/2.0 +0.5)
            deltaY1 = int(math.cos(angle) * localSize/2.0 +0.5)
            deltaX2 = int(math.sin(angle) * (localSize/2.0-RIM_1) +0.5)
            deltaY2 = int(math.cos(angle) * (localSize/2.0-RIM_1)  +0.5)
            if i in [6]:
                painter.setPen(Qt.red)
            else:
                painter.setPen(Qt.blue)
            painter.drawLine(SIZE // 2 - deltaX2, SIZE // 2 + deltaY2, SIZE // 2 - deltaX1, SIZE // 2 + deltaY1)
            
        font=QtGui.QFont()
        font.setPixelSize(18)
        painter.setFont(font)            
            
        for i in range(12):
            angle = angle0 - i * 2.0 * math.pi / 12.0 - 2.0 * math.pi / 24.0
            deltaX3 = int(math.sin(angle) * (localSize/2.0-RIM_1/2.0+3.5)+0.5)
            deltaY3 = int(math.cos(angle) * (localSize/2.0-RIM_1/2.0+3.5) +0.5)
            
            painter.save()
            painter.translate(SIZE // 2 + deltaX3, SIZE // 2 - deltaY3)
            painter.rotate(angle * 180.0 / math.pi)
            painter.drawText(-RIM_1//2, RIM_1//2, SYMBOL_ZODIAC[i])
            painter.restore()
            
        self.sunDeclVsRa = []
        previous = None
        for i in range(365):
            LOCATION.date = ephem.Date(self.globalTime.datetime() + datetime.timedelta(days=i))
            SUN.compute(LOCATION)
            LOCATION.date = self.globalTime
            angle = float(LOCATION.sidereal_time()) - float(SUN.a_ra) + math.pi
            
            decInDegree = SUN.a_dec / math.pi * 180.0
            
            self.sunDeclVsRa.append([SUN.a_dec, SUN.a_ra])
        
            radius = SIZE * (0.6 + decInDegree / 23.44 * DELTA_DECLINATION_SUN) / 2.0
            deltaX1 = int(math.sin(angle) * radius +0.5)
            deltaY1 = int(math.cos(angle) * radius +0.5)
            if not previous is None:
                painter.drawLine(previous[0], previous[1], SIZE // 2 - deltaX1, SIZE // 2 + deltaY1)
            previous = SIZE // 2 - deltaX1, SIZE // 2 + deltaY1
        self.sunDeclVsRa.sort(key = lambda x: x[1])
        
        painter.setPen(Qt.black)
        for i in range(28 * 12):
            LOCATION.date = ephem.Date(self.globalTime.datetime() + datetime.timedelta(hours=i*2))
            MOON.compute(LOCATION)
            LOCATION.date = self.globalTime
            angle = float(LOCATION.sidereal_time()) - float(MOON.a_ra) + math.pi
            
            decInDegree = MOON.a_dec / math.pi * 180.0
        
            radius = SIZE * (0.6 + decInDegree / 23.44 * DELTA_DECLINATION_SUN) / 2.0
            deltaX1 = int(math.sin(angle) * radius +0.5)
            deltaY1 = int(math.cos(angle) * radius +0.5)
            painter.drawPoint(SIZE // 2 - deltaX1, SIZE // 2 + deltaY1)

        painter.end()
        

    def drawSun(self):
        LOCATION.date = self.globalTime
        SUN.compute(LOCATION)
        angle = float(LOCATION.sidereal_time()) - float(SUN.a_ra) + math.pi
        
        painter = QtGui.QPainter(self.label.pixmap())
        
        decInDegree = SUN.a_dec / math.pi * 180.0
        
        brush = QtGui.QBrush()
        brush.setStyle(Qt.SolidPattern)
        brush.setColor(Qt.yellow)
        painter.setBrush(brush)
        
        deltaX = int(math.sin(angle) * (SIZE / 2.0-RIM_1) +0.5)
        deltaY = int(math.cos(angle) * (SIZE / 2.0 - RIM_1) +0.5)
        painter.drawLine(SIZE // 2, SIZE // 2, SIZE // 2 - deltaX, SIZE // 2 + deltaY)
        
        radius = SIZE * (0.6 + decInDegree / 23.44 * DELTA_DECLINATION_SUN) / 2.0
        deltaX1 = int(math.sin(angle) * radius +0.5)
        deltaY1 = int(math.cos(angle) * radius +0.5)
        painter.drawEllipse(SIZE // 2 - deltaX1 - RIM_1//2, SIZE // 2 + deltaY1 - RIM_1//2, RIM_1 - 1, RIM_1 - 1)
        
        painter.end()


    def drawMoon(self):
        LOCATION.date = self.globalTime
        MOON.compute(LOCATION)
        angle = float(LOCATION.sidereal_time()) - float(MOON.a_ra) + math.pi
        
        painter = QtGui.QPainter(self.label.pixmap())
        brush = QtGui.QBrush()
        brush.setStyle(Qt.SolidPattern)
        brush.setColor(QtGui.QColor('darkgray'))
        painter.setBrush(brush)
        
        deltaX = int(math.sin(angle) * (SIZE / 2.0-RIM_1) +0.5)
        deltaY = int(math.cos(angle) * (SIZE / 2.0 - RIM_1) +0.5)
        painter.drawLine(SIZE // 2, SIZE // 2, SIZE // 2 - deltaX, SIZE // 2 + deltaY)
        
        decInDegree = MOON.a_dec / math.pi * 180.0
        
        radius = SIZE * (0.6 + decInDegree / 23.44 * DELTA_DECLINATION_SUN) / 2.0
        deltaX1 = int(math.sin(angle) * radius +0.5)
        deltaY1 = int(math.cos(angle) * radius +0.5)
        painter.drawEllipse(SIZE // 2 - deltaX1 - RIM_1//2, SIZE // 2 + deltaY1 - RIM_1//2, RIM_1, RIM_1)
        
        alphaResolution = 100.0
        betaResolution = 100.0
        x0 = SIZE // 2 - deltaX1
        y0 = SIZE // 2 + deltaY1
        r0 = RIM_1//2
        
        def paint(alpha, beta, r, color):
            deltaX0 = -math.sin(beta)*math.sin(alpha)*r
            deltaY0 = math.cos(beta)*r

            deltaX2 = int(deltaX0 * math.cos(angle) - deltaY0 * math.sin(angle))
            deltaY2 = int(deltaX0 * math.sin(angle) + deltaY0 * math.cos(angle))
            
            painter.setPen(color)
            painter.drawPoint(x0 + deltaX2, y0 + deltaY2)
        
        for indexBeta in range(int(betaResolution)):
            beta = math.pi / betaResolution * indexBeta
            
            if ephem.next_full_moon(self.globalTime) < ephem.next_new_moon(self.globalTime):
                #zunehmend
                for indexAlpha in range(int(MOON.phase/100.0 * alphaResolution+0.5)):
                    alpha = math.pi / alphaResolution * indexAlpha + 0.5 * math.pi
                    paint(alpha, beta, r0, Qt.white)
            else:
                #abnehmend
                for indexAlpha in range(int(alphaResolution - MOON.phase/100.0 * alphaResolution+0.5), int(alphaResolution)):
                    alpha = math.pi / alphaResolution * indexAlpha + 0.5 * math.pi
                    paint(alpha, beta, r0, Qt.white)
        
        for indexBeta in range(int(betaResolution)):
            beta = math.pi / betaResolution * indexBeta
            paint(0.5 * math.pi, beta, r0+1, Qt.black)
            paint(math.pi + 0.5 * math.pi, beta, r0+1, Qt.black)
            
        painter.end()


    def calcMoonEclLat(self, t):
        LOCATION.date = t
        MOON.compute(LOCATION)
        return ephem.Ecliptic(MOON).lat
    
    def calcSunRa(self, t):
        LOCATION.date = t
        SUN.compute(LOCATION)
        return SUN.a_ra

    def drawMoonNodes(self):
        now = self.globalTime.datetime()

        time0 = ephem.Date(now + datetime.timedelta(days=-15))
        lat0 = self.calcMoonEclLat(time0)

        time1 = ephem.Date(now)
        lat1 = self.calcMoonEclLat(time1)

        time2 = ephem.Date(now + datetime.timedelta(days=15))
        lat2 = self.calcMoonEclLat(time2)

        if (lat0 > 0 and lat2 < 0) or (lat0 < 0 and lat2 > 0):
            t1, t2 = time0, time2
        elif (lat0 > 0 and lat1 < 0) or (lat0 < 0 and lat1 > 0):
            t1, t2 = time0, time1
        else:
            t1, t2 = time1, time2

        tNode = findRootByBisection(t1, t2, 0.000001, self.calcMoonEclLat)
        nodeType = 0
        if self.calcMoonEclLat(tNode - 1.0) > 0:
            nodeType = 1

        LOCATION.date = tNode
        MOON.compute(LOCATION)
        
        
        raMoon = MOON.a_ra
        if raMoon < 0.0:
            raMoon += 2.0 * math.pi
        if raMoon > 2.0 * math.pi:
            raMoon -= 2.0 * math.pi
        if self.sunDeclVsRa[0][1] > raMoon:
            decSun = self.sunDeclVsRa[0][0]
        else:
            for i in range(len(self.sunDeclVsRa)-1):
                if self.sunDeclVsRa[i][1] < raMoon and self.sunDeclVsRa[i+1][1] >= raMoon:
                    decSun = self.sunDeclVsRa[i+1][0]
                    break
            
        decInDegree = decSun / math.pi * 180.0
        radius = SIZE * (0.6 + decInDegree / 23.44 * DELTA_DECLINATION_SUN) / 2.0
        
        raMoon = MOON.a_ra + math.pi
        if raMoon < 0.0:
            raMoon += 2.0 * math.pi
        if raMoon > 2.0 * math.pi:
            raMoon -= 2.0 * math.pi
        if self.sunDeclVsRa[0][1] > raMoon:
            decSun = self.sunDeclVsRa[0][0]
        else:
            for i in range(len(self.sunDeclVsRa)-1):
                if self.sunDeclVsRa[i][1] < raMoon and self.sunDeclVsRa[i+1][1] >= raMoon:
                    decSun = self.sunDeclVsRa[i+1][0]
                    break
            
        decInDegree = decSun / math.pi * 180.0
        radius_ = SIZE * (0.6 + decInDegree / 23.44 * DELTA_DECLINATION_SUN) / 2.0
        
        LOCATION.date = self.globalTime

        if nodeType == 0:
            radius0 = radius_
            radius1 = radius
            angle0 = float(LOCATION.sidereal_time()) - float(MOON.a_ra) 
            angle1 = float(LOCATION.sidereal_time()) - float(MOON.a_ra) + math.pi
        else:
            radius0 = radius
            radius1 = radius_
            angle0 = float(LOCATION.sidereal_time()) - float(MOON.a_ra) + math.pi
            angle1 = float(LOCATION.sidereal_time()) - float(MOON.a_ra) 

        LOCATION.date = tNode + 30

        painter = QtGui.QPainter(self.label.pixmap())
        
        deltaX = int(math.sin(angle0) * radius0 +0.5)
        deltaY = int(math.cos(angle0) * radius0 +0.5)
        painter.drawLine(SIZE // 2, SIZE // 2, SIZE // 2 - deltaX, SIZE // 2 + deltaY)

        deltaX1 = int(math.sin(angle0) * (radius0+ RIM_1//2) +0.5)
        deltaY1 = int(math.cos(angle0) * (radius0 + RIM_1//2) +0.5)
        painter.save()
        font=QtGui.QFont()
        font.setPixelSize(20)
        painter.setFont(font)
        painter.translate(SIZE // 2 - deltaX1, SIZE // 2 + deltaY1)
        painter.rotate(angle0 * 180.0 / math.pi)
        painter.drawText(-RIM_1//2, RIM_1//2, SYMBOL_LUNAR_NODES[0])
        painter.restore()

        deltaX = int(math.sin(angle1) * radius1 +0.5)
        deltaY = int(math.cos(angle1) * radius1 +0.5)
        painter.drawLine(SIZE // 2, SIZE // 2, SIZE // 2 - deltaX, SIZE // 2 + deltaY)

        deltaX1 = int(math.sin(angle1) * (radius1+ RIM_1//2) +0.5)
        deltaY1 = int(math.cos(angle1) * (radius1 + RIM_1//2) +0.5)
        painter.save()
        font=QtGui.QFont()
        font.setPixelSize(20)
        painter.setFont(font)
        painter.translate(SIZE // 2 - deltaX1, SIZE // 2 + deltaY1)
        painter.rotate(angle1 * 180.0 / math.pi)
        painter.drawText(-RIM_1//2, RIM_1//2, SYMBOL_LUNAR_NODES[1])
        painter.restore()

        painter.end()    
        
    def drawPlanets(self):
        LOCATION.date = self.globalTime
        painter = QtGui.QPainter(self.label.pixmap())
        for (planet, symbol) in PLANETS:
            planet.compute(LOCATION)
        
            raPlanet = planet.a_ra
            if raPlanet < 0.0:
                raPlanet += 2.0 * math.pi
            if raPlanet > 2.0 * math.pi:
                raPlanet -= 2.0 * math.pi
                
            angle = float(LOCATION.sidereal_time()) - float(raPlanet) + math.pi
        
            deltaX = int(math.sin(angle) * (SIZE / 2.0-RIM_PLANET) +0.5)
            deltaY = int(math.cos(angle) * (SIZE / 2.0 - RIM_PLANET) +0.5)
            painter.setPen(Qt.PenStyle(Qt.DotLine))
            painter.drawLine(SIZE // 2, SIZE // 2, SIZE // 2 - deltaX, SIZE // 2 + deltaY)
            
            decInDegree = planet.a_dec / math.pi * 180.0
            
            radius = SIZE * (0.6 + decInDegree / 23.44 * DELTA_DECLINATION_SUN) / 2.0
            deltaX1 = int(math.sin(angle) * radius +0.5)
            deltaY1 = int(math.cos(angle) * radius +0.5)
            painter.setPen(Qt.PenStyle(Qt.SolidLine))
            painter.drawEllipse(SIZE // 2 - deltaX1 - RIM_PLANET//2, SIZE // 2 + deltaY1 - RIM_PLANET//2, RIM_PLANET - 1, RIM_PLANET - 1)
            
            
            radius2 = SIZE * (0.6 + decInDegree / 23.44 * DELTA_DECLINATION_SUN) / 2.0 + RIM_1
            deltaX2 = int(math.sin(angle) * radius2+0.5)
            deltaY2 = int(math.cos(angle) * radius2+0.5)
            painter.save()
            font=QtGui.QFont()
            font.setPixelSize(18)
            painter.setFont(font)
            painter.translate(SIZE // 2 - deltaX2, SIZE // 2 + deltaY2)
            painter.rotate(angle * 180.0 / math.pi + 180.0)
            painter.drawText(-RIM_1//2, RIM_1//2, symbol)
            painter.restore()
        
        painter.end()
          

        
        
app = QtWidgets.QApplication(sys.argv)
window = MainWindow()

def saveImage():
    imageVar = QtGui.QImage(window.size(), QtGui.QImage.Format.Format_ARGB32)
    window.render(imageVar)
    imageVar.save("astroclock.png")

def redraw():
    window.drawAll()
    window.update()
    saveImage()

window.show()    

timer = QtCore.QTimer()
timer.timeout.connect(redraw)

timer.start(60000 if not SIMULATE else SIMULATION_REDRAW_IN_S*1000)

saveImage()
app.exec_()
