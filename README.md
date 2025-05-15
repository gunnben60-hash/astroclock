# Astronomische Berechnungen zu Erde, Sonne und Mond

## Astronomische Uhr

Datei:

    astroclock.py

- zentrale Anwendung in PyQt5 inspiriert durch die Prager Rathausuhr
- hier werden alle Informationen zusammengeführt


## Sternzeit

Datei:

    sternzeit.py

- Berechnung der Sternzeit für einen gegebenen Zeitpunkt und Längengrad
- Vergleich mit Ephem liefert:
    - Standardabweichung: 0.017 s
    - Maximale Abweichung: 0.05 s

## Mondkalender

Datei:

    mondkalender.py

- Berechnung der Daten des aktuellen Mondmonats für einen Zeitpunkt oder Erstellen eines Mondkalenders für ein Jahr

## Aktuelle Berechnungen zu Erde, Sonne und Mond

Datei: 

    sonneundmond.py

- verwendet `mondkalender.py`
- zeigt die aktuelle Sternzeit, die wahre Sonnenzeit und Daten zu Mondmonat und Auf- und Untergangszeiten von Sonne und Mond an
