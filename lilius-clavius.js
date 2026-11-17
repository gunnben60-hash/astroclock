// Mondkalender nach Aloysius Lilius und Christoph Clavius (gregorianischer Kalender, auch rückwirkend).
// Die Tabellen entsprechen MooncalendarByAloysiusLiliusAndChristophClavius/rechneEpakte.py und dem PDF.
// Goldene Zahl ist die klassische Zählung: (Jahreszahl mod 19) + 1. Das PDF beschriftet dagegen mit Jahreszahl mod 19.

const MONTH_LENGTHS = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];

// Epakte je Tabellentag; ein Paar [25, 24] steht für zwei Epakten am selben Tag.
const NEW_LIGHT_TABLE = [
  [0, 29, 28, 27, 26, 25, 24, 23, 22, 21, 20, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0],
  [29, 28, 27, 26, [25, 24], 23, 22, 21, 20, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1],
  [0, 29, 28, 27, 26, 25, 24, 23, 22, 21, 20, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0],
  [29, 28, 27, 26, [25, 24], 23, 22, 21, 20, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0, 29],
  [28, 27, 26, 25, 24, 23, 22, 21, 20, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0, 29, 28],
  [27, 26, [25, 24], 23, 22, 21, 20, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0, 29, 28, 27],
  [26, 25, 24, 23, 22, 21, 20, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0, 29, 28, 27, 26],
  [[25, 24], 23, 22, 21, 20, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0, 29, 28, 27, 26, 25, 24],
  [23, 22, 21, 20, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0, 29, 28, 27, 26, [25, 24], 23],
  [22, 21, 20, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0, 29, 28, 27, 26, 25, 24, 23, 22],
  [21, 20, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0, 29, 28, 27, 26, [25, 24], 23, 22, 21],
  [20, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0, 29, 28, 27, 26, 25, 24, 23, 22, 21, 20],
];

// Tabellentage der Neulichter, wenn die Epakte 25 und die goldene Zahl (Jahr mod 19 + 1) größer als 11 ist.
const SPECIAL_NEW_LIGHT_DAYS = [6, 4, 6, 4, 4, 2, [2, 31], 30, 28, 28, 26, 26];

function modulo(value, divisor) {
  return ((value % divisor) + divisor) % divisor;
}

export function getGoldenNumber(year) {
  return modulo(year, 19) + 1;
}

function getEpact(year, goldenNumber) {
  const yearMod19 = goldenNumber - 1;
  const century = Math.floor(year / 100);
  const solarCorrection = Math.floor(3 * (century + 1) / 4);
  const lunarCorrection = Math.floor((8 * century + 13) / 25);
  return modulo(11 * yearMod19 - solarCorrection + lunarCorrection + 8, 30);
}

// Gleiche Tagesverschiebung wie adjustDay() in rechneEpakte.py; Februar hat dort 28 Tage.
function adjustDay(day, month) {
  if (day === 0) {
    month -= 1;
    day = MONTH_LENGTHS[modulo(month - 1, 12)];
    if (month < 1) month = 12;
  }
  if (day > MONTH_LENGTHS[month - 1]) {
    day -= MONTH_LENGTHS[month - 1];
    month += 1;
    if (month > 12) return { month: 1, day, nextYear: true };
  }
  return { month, day, nextYear: false };
}

// Neulichter eines Jahres als Tabellentage (Index 0-basiert); die Anzeige liegt einen Tag davor.
function getNewLightPositions(epact, goldenNumber) {
  const positions = [];
  if (epact === 25 && goldenNumber > 11) {
    SPECIAL_NEW_LIGHT_DAYS.forEach((days, monthIndex) => {
      for (const day of [days].flat()) positions.push({ month: monthIndex + 1, index: day - 1 });
    });
    return { positions, isSpecial: true };
  }
  NEW_LIGHT_TABLE.forEach((entries, monthIndex) => {
    entries.forEach((entry, index) => {
      const matches = Array.isArray(entry) ? entry.includes(epact) : entry === epact;
      if (matches) positions.push({ month: monthIndex + 1, index });
    });
  });
  return { positions, isSpecial: false };
}

/**
 * Neu- und Vollmonde nach Lilius und Clavius für ein Datum, für alle 19 goldenen Zahlen
 * des Jahrhunderts von `year`. Vollmond ist 14 Tage nach dem angezeigten Neumond; fällt er
 * in den Januar des Folgejahres, gehört er zur nächsten goldenen Zahl.
 */
export function getLiliusClaviusMoonDay(year, month, day) {
  const newMoon = [];
  const fullMoon = [];

  for (let goldenNumber = 1; goldenNumber <= 19; goldenNumber += 1) {
    const epact = getEpact(year, goldenNumber);
    const { positions, isSpecial } = getNewLightPositions(epact, goldenNumber);

    for (const { month: tableMonth, index } of positions) {
      const isFirstOfJanuary = !isSpecial && tableMonth === 1 && index === 0;
      if (!isFirstOfJanuary) {
        const shown = adjustDay(index, tableMonth);
        if (shown.month === month && shown.day === day) newMoon.push(goldenNumber);
      }

      const full = adjustDay(index + 14, tableMonth);
      if (full.month === month && full.day === day) {
        fullMoon.push(full.nextYear ? goldenNumber % 19 + 1 : goldenNumber);
      }
    }
  }

  const unique = (numbers) => [...new Set(numbers)].sort((left, right) => left - right);
  return { newMoon: unique(newMoon), fullMoon: unique(fullMoon) };
}
