import datetime
import ephem
import math
import os
import sys
import threading
import time
from PyQt5 import QtCore, QtGui, QtWidgets, uic 
from PyQt5.QtCore import QEvent, QPoint, Qt
from sonneundmond import getLines

try:
    from zoneinfo import ZoneInfo
except:
    from backports.zoneinfo import ZoneInfo

def findRootByBisection(arg1, arg2, delta, f):
    argM = 0.5*(arg1 + arg2)
    if abs(arg1-arg2) < delta:
        return argM

    y1 = f(arg1)
    yM = f(argM)

    if (y1 > 0) == (yM > 0):
        return findRootByBisection(argM, arg2, delta, f)
    else:
        return findRootByBisection(arg1, argM, delta, f)

   

class Config:
    FILE_NAME = 'astroclock.location'
    DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

    def __init__(self):
        self.lon = 13.066667   # Zschopau
        self.lat = 50.75
        self.timezone = 'Europe/Berlin'
        self.simulate = False
        self.show_planets = True
        self.simulation_redraw_s = 60
        self.simulation_time_step_s = 60
        self.simulation_start_time = None

    @staticmethod
    def parseDateString(date_string, timezone):
        temp = datetime.datetime.strptime(date_string, Config.DATE_FORMAT)
        return datetime.datetime(
            temp.year, temp.month, temp.day,
            temp.hour, temp.minute, temp.second,
            tzinfo=ZoneInfo(timezone)
        )
    
    @classmethod
    def load(cls):
        config = cls()

        if os.path.exists(cls.FILE_NAME):
            with open(cls.FILE_NAME) as infile:
                data = infile.read().strip().split('\n')
                for line in data:
                    parts = [x.strip() for x in line.split('=')]
                    if len(parts) != 2:
                        continue

                    key, value = parts[0].upper(), parts[1]

                    if key == 'LON':
                        config.lon = float(value)
                    elif key == 'LAT':
                        config.lat = float(value)
                    elif key == 'TIMEZONE':
                        config.timezone = value
                    elif key == 'SIMULATE':
                        config.simulate = (value.lower() == 'true')
                    elif key == 'SIMULATION_REDRAW_IN_S':
                        config.simulation_redraw_s = int(value)
                    elif key == 'SIMULATION_TIME_STEP_IN_S':
                        config.simulation_time_step_s = int(value)
                    elif key == 'SHOW_PLANETS':
                        config.show_planets = (value.lower() == 'true')
                    elif key == 'SIMULATION_START_TIME':
                        config.simulation_start_time = cls.parseDateString(value, config.timezone)
        else:
            config.save()
        return config
    

    def save(self):
        with open(self.FILE_NAME, 'w') as outfile:
            outfile.write(f'LON={self.lon}\n')
            outfile.write(f'LAT={self.lat}\n')
            outfile.write(f'TIMEZONE={self.timezone}\n')
            outfile.write(f'SIMULATE={self.simulate}\n')
            outfile.write(f'SIMULATION_REDRAW_IN_S={self.simulation_redraw_s}\n')
            outfile.write(f'SIMULATION_TIME_STEP_IN_S={self.simulation_time_step_s}\n')
            outfile.write(f'SHOW_PLANETS={self.show_planets}\n')

            start = self.simulation_start_time or datetime.datetime.now(ZoneInfo(self.timezone))
            outfile.write(f'SIMULATION_START_TIME={start.strftime(self.DATE_FORMAT)}\n')

config = Config.load()

    

class MainWindow(QtWidgets.QMainWindow):

    SUN = ephem.Sun()
    MOON = ephem.Moon()

    SIZE = 600
    RIM_1 = 20
    RIM_PLANET = 10
    TEXT_HEIGHT = 270
    SYMBOL_CLOCK = ['XII', 'I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X', 'XI', 'XII', 'I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X', 'XI']
    SYMBOL_ZODIAC = ['♈︎', '♉︎', '♊︎', '♋︎', '♌︎', '♍︎', '♎︎', '♏︎', '♐︎', '♑︎', '♒︎', '♓︎']
    SYMBOL_LUNAR_NODES = ['☊', '☋']
    PLANETS = [(ephem.Mercury(), '☿'), (ephem.Venus(), '♀'), (ephem.Mars(), '♂'), (ephem.Jupiter(), '♃'), (ephem.Saturn(), '♄')]
    DELTA_DECLINATION_SUN = 0.2

    def __init__(self, config):
        super().__init__()
        
        self.setWindowTitle('Astrologion')
        
        self.config = config
        self.location = ephem.Observer()
        self.location.lon, self.location.lat  = str(self.config.lon), str(self.config.lat)
        self.label = QtWidgets.QLabel()
        canvas = QtGui.QPixmap(self.SIZE,self. SIZE + self.TEXT_HEIGHT)
        canvas.fill(Qt.white)
        self.label.setPixmap(canvas)
        self.globalTime = None
        
        self.label.installEventFilter(self)
        self.drawAll()

    def eventFilter(self, obj, event):
        if event.type() == QEvent.MouseButtonPress:
            if event.button() == Qt.LeftButton:
                if event.y() <= self.RIM_1 and event.x() <= self.RIM_1:
                    self.startMovement = None
                    self.config.simulate = True
                    now = self.globalTime.datetime()
                    result = now + datetime.timedelta(days=-1)
                    self.globalTime = ephem.Date(result)
                    self.drawAll(False)
                    self.update()
                elif event.y() <= self.RIM_1 and event.x() >= self.SIZE-self.RIM_1:
                    self.startMovement = None
                    self.config.simulate = True
                    now = self.globalTime.datetime()
                    result = now + datetime.timedelta(days=1)
                    self.globalTime = ephem.Date(result)
                    self.drawAll(False)
                    self.update()
                else:
                    self.startMovement = (event.x(), event.y())
            elif event.button() == Qt.RightButton:
                self.config.simulate = False
                self.drawAll()
                self.update()
        elif event.type() == QEvent.MouseButtonRelease:
            if event.button() == Qt.LeftButton and self.startMovement is not None:
                self.config.simulate = True
                x1 = self.startMovement[0] - self.SIZE/2
                y1 = self.startMovement[1] - self.SIZE/2
                theta1 = math.atan2(y1, x1)
                x2 = event.x() - self.SIZE/2
                y2 = event.y() - self.SIZE/2
                theta2 = math.atan2(y2, x2)
                
                timeShiftInDays = (theta2-theta1)/2.0/math.pi
                if timeShiftInDays > 0.5:
                    timeShiftInDays -= 1.0
                if timeShiftInDays < -0.5:
                    timeShiftInDays += 1.0
                now = self.globalTime.datetime()
                result = now + datetime.timedelta(days=timeShiftInDays)
                self.globalTime = ephem.Date(result)
                    
                self.drawAll(False)
                self.update()
                            
        return super().eventFilter(obj, event)
        
    def drawAll(self, resetTime=True):
        if self.globalTime is None:
            if not self.config.simulate or self.config.simulation_start_time is None:
                self.globalTime = ephem.now()
            else:
                self.globalTime = ephem.Date(self.config.simulation_start_time)

        if resetTime:
            if not self.config.simulate:
                self.globalTime = ephem.now()
            else:
                self.globalTime = ephem.Date(self.globalTime.datetime() + datetime.timedelta(seconds=self.config.simulation_time_step_s))
        self.clear()
        self.setCentralWidget(self.label)
        self.drawBackground()
        self.drawZodiac()
        self.drawMoonNodes()
        if self.config.show_planets:
            self.drawPlanetsAndSun()
        else:
            self.drawSun()
        self.drawMoon()
        self.fillText()
        
    def clear(self):
        painter = QtGui.QPainter(self.label.pixmap())
        painter.fillRect(0, 0, self.SIZE, self.SIZE + self.TEXT_HEIGHT, Qt.white)

    def fillText(self):
        self.location.date = self.globalTime
       
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
        for line in getLines(self.location, self.config.timezone, self.globalTime):
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
            painter.drawText(self.RIM_1, self.SIZE + self.RIM_1 + i*15, text[i][0])
            if len(text[i]) < 2:
                continue
            painter.drawText(200, self.SIZE + self.RIM_1 + i*15, text[i][1])

        painter.end()

    def drawBackground(self):
        painter = QtGui.QPainter(self.label.pixmap())
        pen = QtGui.QPen()
        pen.setColor(Qt.blue)
        pen.setWidth(1)
        painter.setPen(pen)
        
        painter.drawEllipse(self.RIM_1, self.RIM_1, self.SIZE-2*self.RIM_1, self.SIZE-2*self.RIM_1)
        
        font=QtGui.QFont()
        font.setPixelSize(20)
        painter.setFont(font)
        
        painter.drawText(self.RIM_1//4, self.RIM_1, '<')
        painter.drawText(self.SIZE-self.RIM_1, self.RIM_1, '>')
        
        for i in range(24):
            angle = 2.0 * math.pi / 24.0 * i
            deltaX1 = int(math.sin(angle) * self.SIZE / 2.0 +0.5)
            deltaY1 = int(math.cos(angle) * self.SIZE / 2.0 +0.5) 
            deltaX2 = int(math.sin(angle) * (self.SIZE / 2.0 - self.RIM_1) +0.5)
            deltaY2 = int(math.cos(angle) * (self.SIZE / 2.0 - self.RIM_1) +0.5) 
            painter.drawLine(self.SIZE // 2 - deltaX2, self.SIZE // 2 + deltaY2, self.SIZE // 2 - deltaX1, self.SIZE // 2 + deltaY1)
            
            deltaX3 = int(math.sin(angle) * (self.SIZE / 2.0 - 2*self.RIM_1) +0.5)
            deltaY3 = int(math.cos(angle) * (self.SIZE / 2.0 - 2*self.RIM_1) +0.5)
            
            painter.save()
            painter.translate(self.SIZE // 2 - deltaX3, self.SIZE // 2 + deltaY3)
            painter.rotate(180+i*15)
            painter.drawText(-self.RIM_1//2, self.RIM_1//2, self.SYMBOL_CLOCK[i])
            painter.restore()
            
        painter.setPen(Qt.yellow)
        
        sizeEquinox = int(self.SIZE * 0.6)
        painter.drawEllipse( (self.SIZE - sizeEquinox)//2 , (self.SIZE - sizeEquinox)//2, sizeEquinox, sizeEquinox)
        sizeSummerSolstice = int(self.SIZE * (0.6 + self.DELTA_DECLINATION_SUN))
        painter.drawEllipse( (self.SIZE - sizeSummerSolstice)//2 , (self.SIZE - sizeSummerSolstice)//2, sizeSummerSolstice, sizeSummerSolstice)
        sizeWinterSolstice = int(self.SIZE * (0.6 - self.DELTA_DECLINATION_SUN))
        painter.drawEllipse( (self.SIZE - sizeWinterSolstice)//2 , (self.SIZE - sizeWinterSolstice)//2, sizeWinterSolstice, sizeWinterSolstice)
        
        phi = math.pi / 180.0 * config.lat
        for (hInDegree, color) in [(0.0, Qt.lightGray), (6.0, Qt.gray), (12.0, Qt.darkGray), (18.0, Qt.darkGray)]:
            painter.setPen(color)
            prev = None
            h = - hInDegree / 180.0 * math.pi
            N = 10000
            for i in range(0, N):
                azimut = 2.0 * math.pi / N * i
                declination = math.asin(math.sin(phi)*math.sin(h) - math.cos(phi)*math.cos(azimut)*math.cos(h))
                tau = math.atan2((math.sin(phi)*math.cos(azimut) + math.cos(phi)*math.tan(h)), math.sin(azimut)) + math.pi/2.0
                
                radius = self.SIZE * (0.6 + declination / math.pi * 180.0 / 23.44 * self.DELTA_DECLINATION_SUN) / 2.0
                if radius < self.SIZE/6.0 or radius > self.SIZE//2 - self.RIM_1:
                    continue
                deltaX = int(math.sin(tau) * radius +0.5)
                deltaY = int(math.cos(tau) * radius +0.5)
                
                if prev:
                    painter.drawPoint(self.SIZE // 2 - deltaX, self.SIZE // 2 + deltaY)
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
                radius = self.SIZE * (0.6 + declination / math.pi * 180.0 / 23.44 * self.DELTA_DECLINATION_SUN) / 2.0
                deltaX = int(math.sin(angle) * radius +0.5)
                deltaY = int(math.cos(angle) * radius +0.5)
            
                painter.drawPoint(self.SIZE // 2 - deltaX, self.SIZE // 2 + deltaY)
            prev = deltaX, deltaY 
                
        painter.end()
        
        
    def drawZodiac(self):
        self.location.date = self.globalTime
        
        painter = QtGui.QPainter(self.label.pixmap())
        painter.setPen(Qt.blue)
        localSize = self.SIZE//3
        painter.drawEllipse( (self.SIZE - localSize)//2, (self.SIZE - localSize)//2, localSize, localSize)
        painter.drawEllipse( (self.SIZE - localSize)//2 + self.RIM_1, (self.SIZE - localSize)//2 + self.RIM_1, localSize - 2*self.RIM_1, localSize - 2*self.RIM_1)
        
        angle0 = float(self.location.sidereal_time())
        for i in range(12):
            angle = angle0 - i * 2.0 * math.pi / 12.0
            deltaX1 = int(math.sin(angle) * localSize/2.0 +0.5)
            deltaY1 = int(math.cos(angle) * localSize/2.0 +0.5)
            deltaX2 = int(math.sin(angle) * (localSize/2.0-self.RIM_1) +0.5)
            deltaY2 = int(math.cos(angle) * (localSize/2.0-self.RIM_1)  +0.5)
            if i in [6]:
                painter.setPen(Qt.red)
            else:
                painter.setPen(Qt.blue)
            painter.drawLine(self.SIZE // 2 - deltaX2, self.SIZE // 2 + deltaY2, self.SIZE // 2 - deltaX1, self.SIZE // 2 + deltaY1)
            
        font=QtGui.QFont()
        font.setPixelSize(18)
        painter.setFont(font)            
            
        for i in range(12):
            angle = angle0 - i * 2.0 * math.pi / 12.0 - 2.0 * math.pi / 24.0
            deltaX3 = int(math.sin(angle) * (localSize/2.0-self.RIM_1/2.0+3.5)+0.5)
            deltaY3 = int(math.cos(angle) * (localSize/2.0-self.RIM_1/2.0+3.5) +0.5)
            
            painter.save()
            painter.translate(self.SIZE // 2 + deltaX3, self.SIZE // 2 - deltaY3)
            painter.rotate(angle * 180.0 / math.pi)
            painter.drawText(-self.RIM_1//2, self.RIM_1//2, self.SYMBOL_ZODIAC[i])
            painter.restore()
            
        self.sunDeclVsRa = []
        previous = None
        for i in range(365):
            self.location.date = ephem.Date(self.globalTime.datetime() + datetime.timedelta(days=i))
            self.SUN.compute(self.location)
            self.location.date = self.globalTime
            angle = float(self.location.sidereal_time()) - float(self.SUN.a_ra) + math.pi
            
            decInDegree = self.SUN.a_dec / math.pi * 180.0
            
            self.sunDeclVsRa.append([self.SUN.a_dec, self.SUN.a_ra])
        
            radius = self.SIZE * (0.6 + decInDegree / 23.44 * self.DELTA_DECLINATION_SUN) / 2.0
            deltaX1 = int(math.sin(angle) * radius +0.5)
            deltaY1 = int(math.cos(angle) * radius +0.5)
            if not previous is None:
                painter.drawLine(previous[0], previous[1], self.SIZE // 2 - deltaX1, self.SIZE // 2 + deltaY1)
            previous = self.SIZE // 2 - deltaX1, self.SIZE // 2 + deltaY1
        self.sunDeclVsRa.sort(key = lambda x: x[1])
        
        painter.setPen(Qt.black)
        for i in range(28 * 12):
            self.location.date = ephem.Date(self.globalTime.datetime() + datetime.timedelta(hours=i*2))
            self.MOON.compute(self.location)
            self.location.date = self.globalTime
            angle = float(self.location.sidereal_time()) - float(self.MOON.a_ra) + math.pi
            
            decInDegree = self.MOON.a_dec / math.pi * 180.0
        
            radius = self.SIZE * (0.6 + decInDegree / 23.44 * self.DELTA_DECLINATION_SUN) / 2.0
            deltaX1 = int(math.sin(angle) * radius +0.5)
            deltaY1 = int(math.cos(angle) * radius +0.5)
            painter.drawPoint(self.SIZE // 2 - deltaX1, self.SIZE // 2 + deltaY1)

        painter.end()
        

    def drawSun(self):
        self.location.date = self.globalTime
        self.SUN.compute(self.location)
        angle = float(self.location.sidereal_time()) - float(self.SUN.a_ra) + math.pi
        
        painter = QtGui.QPainter(self.label.pixmap())
        
        decInDegree = self.SUN.a_dec / math.pi * 180.0
        
        brush = QtGui.QBrush()
        brush.setStyle(Qt.SolidPattern)
        brush.setColor(Qt.yellow)
        painter.setBrush(brush)
        
        deltaX = int(math.sin(angle) * (self.SIZE / 2.0-self.RIM_1) +0.5)
        deltaY = int(math.cos(angle) * (self.SIZE / 2.0 - self.RIM_1) +0.5)
        painter.drawLine(self.SIZE // 2, self.SIZE // 2, self.SIZE // 2 - deltaX, self.SIZE // 2 + deltaY)
        
        radius = self.SIZE * (0.6 + decInDegree / 23.44 * self.DELTA_DECLINATION_SUN) / 2.0
        deltaX1 = int(math.sin(angle) * radius +0.5)
        deltaY1 = int(math.cos(angle) * radius +0.5)

        center = QPoint(self.SIZE // 2 - deltaX1, self.SIZE // 2 + deltaY1)
        radius1 = self.RIM_1//2

        # Fokuspunkt für schräge Beleuchtung von oben links
        focal_point = QPoint(self.SIZE // 2 - deltaX1 - self.RIM_1//5, self.SIZE // 2 + deltaY1 - self.RIM_1//5)  # Verschoben nach oben links

        # Radialer Gradient für goldene Farbe und Glanz
        gradient = QtGui.QRadialGradient(focal_point, radius1, focal_point)
        gradient.setColorAt(0.0, QtGui.QColor(255, 223, 186))  # Heller Goldton
        gradient.setColorAt(0.4, QtGui.QColor(212, 175, 55))   # Mittlerer Goldton
        gradient.setColorAt(0.8, QtGui.QColor(198, 155, 33))   # Dunkler Goldton
        gradient.setColorAt(1.0, QtGui.QColor(184, 134, 11))    # Dunkler Rand

        painter.setBrush(gradient)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(center, radius1, radius1)
        
        painter.end()


    def drawMoon(self):
        self.location.date = self.globalTime
        self.MOON.compute(self.location)
        angle = float(self.location.sidereal_time()) - float(self.MOON.a_ra) + math.pi
        
        painter = QtGui.QPainter(self.label.pixmap())
        brush = QtGui.QBrush()
        brush.setStyle(Qt.SolidPattern)
        brush.setColor(QtGui.QColor('darkgray'))
        painter.setBrush(brush)
        
        deltaX = int(math.sin(angle) * (self.SIZE / 2.0-self.RIM_1) +0.5)
        deltaY = int(math.cos(angle) * (self.SIZE / 2.0 - self.RIM_1) +0.5)
        painter.drawLine(self.SIZE // 2, self.SIZE // 2, self.SIZE // 2 - deltaX, self.SIZE // 2 + deltaY)
        
        decInDegree = self.MOON.a_dec / math.pi * 180.0
        
        radius = self.SIZE * (0.6 + decInDegree / 23.44 * self.DELTA_DECLINATION_SUN) / 2.0
        deltaX1 = int(math.sin(angle) * radius +0.5)
        deltaY1 = int(math.cos(angle) * radius +0.5)

        center = QPoint(self.SIZE // 2 - deltaX1, self.SIZE // 2 + deltaY1)
        radius1 = self.RIM_1 // 2

        # Fokuspunkt für schräge Beleuchtung von oben links
        focal_point = QPoint(self.SIZE // 2 - deltaX1 - self.RIM_1//5, self.SIZE // 2 + deltaY1 - self.RIM_1//5)  # Verschoben nach oben links

        # Radialer Gradient für goldene Farbe und Glanz
        gradient = QtGui.QRadialGradient(focal_point, radius1, focal_point)
        gradient.setColorAt(0.0, QtGui.QColor(223, 223, 223))  
        gradient.setColorAt(0.4, QtGui.QColor(199, 199, 199))   
        gradient.setColorAt(0.8, QtGui.QColor(187, 187, 187))   
        gradient.setColorAt(1.0, QtGui.QColor(175, 175, 175))   

        painter.setBrush(gradient)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(center, radius1, radius1)

        alphaResolution = 100.0
        betaResolution = 100.0
        x0 = self.SIZE // 2 - deltaX1
        y0 = self.SIZE // 2 + deltaY1
        r0 = self.RIM_1//2

        pixmap = self.label.pixmap()
        img = pixmap.toImage()

        painted = {}

        def paint(alpha, beta, r):
            deltaX0 = -math.sin(beta)*math.sin(alpha)*r
            deltaY0 = math.cos(beta)*r

            deltaX2 = int(deltaX0 * math.cos(angle) - deltaY0 * math.sin(angle))
            deltaY2 = int(deltaX0 * math.sin(angle) + deltaY0 * math.cos(angle))

            if (x0 + deltaX2, y0 + deltaY2) in painted:
                return          
            col = img.pixel(x0 + deltaX2, y0 + deltaY2)
            col_rgb = QtGui.QColor(col).getRgb()
            
            newgrayScale = col_rgb[0] - 100
            newColor = QtGui.QColor(newgrayScale, newgrayScale, newgrayScale)
            painter.setPen(newColor)
            painter.drawPoint(x0 + deltaX2, y0 + deltaY2)

            painted[(x0 + deltaX2, y0 + deltaY2)] = True


        
        for indexBeta in range(int(betaResolution)):
            beta = math.pi / betaResolution * indexBeta
            if ephem.next_full_moon(self.globalTime) < ephem.next_new_moon(self.globalTime):
                #zunehmend
                for indexAlpha in range(int(self.MOON.phase/100.0 * alphaResolution+0.5) + 1, int(alphaResolution)):
                    alpha = math.pi / alphaResolution * indexAlpha + 0.5 * math.pi
                    paint(alpha, beta, r0)
            else:
                #abnehmend
                for indexAlpha in range(int(alphaResolution - self.MOON.phase/100.0 * alphaResolution+0.5)-1):
                    alpha = math.pi / alphaResolution * indexAlpha + 0.5 * math.pi
                    paint(alpha, beta, r0)

        painter.end()


    def calcMoonEclLat(self, t):
        self.location.date = t
        self.MOON.compute(self.location)
        return ephem.Ecliptic(self.MOON).lat
    
    def calcSunRa(self, t):
        self.location.date = t
        self.SUN.compute(self.location)
        return self.SUN.a_ra

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

        self.location.date = tNode
        self.MOON.compute(self.location)
        
        
        raMoon = self.MOON.a_ra
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
        radius = self.SIZE * (0.6 + decInDegree / 23.44 * self.DELTA_DECLINATION_SUN) / 2.0
        
        raMoon = self.MOON.a_ra + math.pi
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
        radius_ = self.SIZE * (0.6 + decInDegree / 23.44 * self.DELTA_DECLINATION_SUN) / 2.0
        
        self.location.date = self.globalTime

        if nodeType == 0:
            radius0 = radius_
            radius1 = radius
            angle0 = float(self.location.sidereal_time()) - float(self.MOON.a_ra) 
            angle1 = float(self.location.sidereal_time()) - float(self.MOON.a_ra) + math.pi
        else:
            radius0 = radius
            radius1 = radius_
            angle0 = float(self.location.sidereal_time()) - float(self.MOON.a_ra) + math.pi
            angle1 = float(self.location.sidereal_time()) - float(self.MOON.a_ra) 

        self.location.date = tNode + 30

        painter = QtGui.QPainter(self.label.pixmap())
        
        deltaX = int(math.sin(angle0) * radius0 +0.5)
        deltaY = int(math.cos(angle0) * radius0 +0.5)
        painter.drawLine(self.SIZE // 2, self.SIZE // 2, self.SIZE // 2 - deltaX, self.SIZE // 2 + deltaY)

        deltaX1 = int(math.sin(angle0) * (radius0+ self.RIM_1//2) +0.5)
        deltaY1 = int(math.cos(angle0) * (radius0 + self.RIM_1//2) +0.5)
        painter.save()
        font=QtGui.QFont()
        font.setPixelSize(20)
        painter.setFont(font)
        painter.translate(self.SIZE // 2 - deltaX1, self.SIZE // 2 + deltaY1)
        painter.rotate(angle0 * 180.0 / math.pi)
        painter.drawText(-self.RIM_1//2, self.RIM_1//2, self.SYMBOL_LUNAR_NODES[0])
        painter.restore()

        deltaX = int(math.sin(angle1) * radius1 +0.5)
        deltaY = int(math.cos(angle1) * radius1 +0.5)
        painter.drawLine(self.SIZE // 2, self.SIZE // 2, self.SIZE // 2 - deltaX, self.SIZE // 2 + deltaY)

        deltaX1 = int(math.sin(angle1) * (radius1+ self.RIM_1//2) +0.5)
        deltaY1 = int(math.cos(angle1) * (radius1 + self.RIM_1//2) +0.5)
        painter.save()
        font=QtGui.QFont()
        font.setPixelSize(20)
        painter.setFont(font)
        painter.translate(self.SIZE // 2 - deltaX1, self.SIZE // 2 + deltaY1)
        painter.rotate(angle1 * 180.0 / math.pi)
        painter.drawText(-self.RIM_1//2, self.RIM_1//2, self.SYMBOL_LUNAR_NODES[1])
        painter.restore()

        painter.end()    
        
    def drawPlanetsAndSun(self):
        self.location.date = self.globalTime

        def drawPlanet(planet, symbol):
            painter = QtGui.QPainter(self.label.pixmap())
            planet.compute(self.location)
        
            raPlanet = planet.a_ra
            if raPlanet < 0.0:
                raPlanet += 2.0 * math.pi
            if raPlanet > 2.0 * math.pi:
                raPlanet -= 2.0 * math.pi
                
            angle = float(self.location.sidereal_time()) - float(raPlanet) + math.pi
        
            deltaX = int(math.sin(angle) * (self.SIZE / 2.0-self.RIM_PLANET) +0.5)
            deltaY = int(math.cos(angle) * (self.SIZE / 2.0 - self.RIM_PLANET) +0.5)
            painter.setPen(Qt.PenStyle(Qt.DotLine))
            painter.drawLine(self.SIZE // 2, self.SIZE // 2, self.SIZE // 2 - deltaX, self.SIZE // 2 + deltaY)
            
            decInDegree = planet.a_dec / math.pi * 180.0
            
            radius = self.SIZE * (0.6 + decInDegree / 23.44 * self.DELTA_DECLINATION_SUN) / 2.0
            deltaX1 = int(math.sin(angle) * radius +0.5)
            deltaY1 = int(math.cos(angle) * radius +0.5)
            painter.setPen(Qt.PenStyle(Qt.SolidLine))


            center = QPoint(self.SIZE // 2 - deltaX1, self.SIZE // 2 + deltaY1)
            radius1 = self.RIM_PLANET // 2

            # Fokuspunkt für schräge Beleuchtung von oben links
            focal_point = QPoint(self.SIZE // 2 - deltaX1 - self.RIM_PLANET//5, self.SIZE // 2 + deltaY1 - self.RIM_PLANET//5)  # Verschoben nach oben links

            # Radialer Gradient für goldene Farbe und Glanz
            gradient = QtGui.QRadialGradient(focal_point, radius1, focal_point)
            gradient.setColorAt(0.0, QtGui.QColor(223, 223, 223))  
            gradient.setColorAt(0.4, QtGui.QColor(175, 175, 175))   
            gradient.setColorAt(0.8, QtGui.QColor(155, 155, 155))   
            gradient.setColorAt(1.0, QtGui.QColor(134, 134, 134))   

            painter.setBrush(gradient)
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(center, radius1, radius1)
            painter.drawEllipse(self.SIZE // 2 - deltaX1 - self.RIM_PLANET//2, self.SIZE // 2 + deltaY1 - self.RIM_PLANET//2, self.RIM_PLANET - 1, self.RIM_PLANET - 1)
            
            pen = QtGui.QPen()
            pen.setColor(Qt.black)
            pen.setWidth(1)
            painter.setPen(pen)
            radius2 = self.SIZE * (0.6 + decInDegree / 23.44 * self.DELTA_DECLINATION_SUN) / 2.0 + self.RIM_1
            deltaX2 = int(math.sin(angle) * radius2+0.5)
            deltaY2 = int(math.cos(angle) * radius2+0.5)
            painter.save()
            font=QtGui.QFont()
            font.setPixelSize(18)
            painter.setFont(font)
            painter.translate(self.SIZE // 2 - deltaX2, self.SIZE // 2 + deltaY2)
            painter.rotate(angle * 180.0 / math.pi + 180.0)
            painter.drawText(-self.RIM_1//2, self.RIM_1//2, symbol)
            painter.restore()
            painter.end()

        celestialBodies = [(self.SUN.earth_distance, self.drawSun)]
        for (planet, symbol) in self.PLANETS:
            planet.compute(self.location)
            def outer():
                (planet1, symbol1) = (planet, symbol)
                return lambda: drawPlanet(planet1, symbol1)
            celestialBodies.append( (planet.earth_distance, outer()) )

        celestialBodies.sort(key=lambda x: x[0], reverse=True)
        
        for (distance, drawFunction) in celestialBodies:
            drawFunction()

        
          
       
        
app = QtWidgets.QApplication(sys.argv)
window = MainWindow(config)

def saveImage():
    imageVar = QtGui.QImage(window.size(), QtGui.QImage.Format.Format_ARGB32)
    window.render(imageVar)
    #imageVar.save("astroclock.png")

def redraw():
    window.drawAll()
    window.update()
    saveImage()

window.show()    

timer = QtCore.QTimer()
timer.timeout.connect(redraw)

timer.start(60000 if not config.simulate else config.simulation_redraw_s * 1000)

saveImage()
app.exec_()
