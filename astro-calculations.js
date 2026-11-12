import * as Astronomy from "astronomy-engine";

const BODY_NAMES = ["Mercury", "Venus", "Mars", "Jupiter", "Saturn"];
const BABYLONIAN_MONTH_NAMES = [
  "Nisannu",
  "Ajaru",
  "Simanu",
  "Du'uzu",
  "Abu",
  "Ululu",
  "Tašritu",
  "Araḫsamna",
  "Kislimu",
  "Tebetu",
  "Šabatu",
  "Addaru",
];
const LILIUS_CLAVIUS_EPACT_STARTS = [0, 29, 0, 29, 28, 27, 26, 25, 23, 22, 21, 20];
const LILIUS_CLAVIUS_MONTH_LENGTHS = [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
const LILIUS_CLAVIUS_DOUBLE_EPACT_DAYS = new Set([
  "2:5",
  "4:5",
  "6:3",
  "8:1",
  "9:29",
  "11:27",
]);
const LILIUS_CLAVIUS_SPECIAL_NEW_LIGHT_DAYS = [6, 4, 6, 4, 4, 2, [2, 31], 30, 28, 28, 26, 26];
const KM_PER_AU = 149597870.7;
const MEAN_MOON_DISTANCE_KM = 381000;
const SIDEREAL_HOURS_PER_CIRCLE = 24;

function modulo(value, divisor) {
  return ((value % divisor) + divisor) % divisor;
}

function assertFiniteNumber(value, name, min, max) {
  if (!Number.isFinite(value) || value < min || value > max) {
    throw new RangeError(`${name} must be a number from ${min} to ${max}.`);
  }
}

function getZonedParts(date, timeZone) {
  const formatter = new Intl.DateTimeFormat("en-CA", {
    timeZone,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hourCycle: "h23",
  });
  return Object.fromEntries(
    formatter.formatToParts(date)
      .filter((part) => part.type !== "literal")
      .map((part) => [part.type, Number(part.value)]),
  );
}

function localMidnight(date, timeZone) {
  const local = getZonedParts(date, timeZone);
  const targetUtcValue = Date.UTC(local.year, local.month - 1, local.day);
  let guess = targetUtcValue;

  // Reconcile the requested local midnight with the zone's UTC offset, including DST.
  for (let attempt = 0; attempt < 4; attempt += 1) {
    const parts = getZonedParts(new Date(guess), timeZone);
    const representedUtcValue = Date.UTC(
      parts.year,
      parts.month - 1,
      parts.day,
      parts.hour,
      parts.minute,
      parts.second,
    );
    const adjustment = targetUtcValue - representedUtcValue;
    guess += adjustment;
    if (adjustment === 0) break;
  }

  return new Date(guess);
}

function eventDate(result) {
  return result ? result.date : null;
}

function getBodyPosition(body, date, observer) {
  const equatorial = Astronomy.Equator(body, date, observer, true, true);
  const horizontal = Astronomy.Horizon(
    date,
    observer,
    equatorial.ra,
    equatorial.dec,
    "normal",
  );

  return {
    rightAscensionHours: equatorial.ra,
    declinationDegrees: equatorial.dec,
    distanceAU: equatorial.dist,
    azimuthDegrees: horizontal.azimuth,
    altitudeDegrees: horizontal.altitude,
  };
}

function getDailyEvents(body, observer, start) {
  const transit = Astronomy.SearchHourAngle(body, observer, 0, start, 1);
  return {
    rise: eventDate(Astronomy.SearchRiseSet(body, observer, 1, start, 1)),
    transit: transit ? transit.time.date : null,
    set: eventDate(Astronomy.SearchRiseSet(body, observer, -1, start, 1)),
  };
}

function getMoonNode(date) {
  const first = Astronomy.SearchMoonNode(
    new Date(date.getTime() - 15 * 86400000),
  );
  const following = Astronomy.NextMoonNode(first);
  const firstDifference = Math.abs(first.time.date - date);
  const followingDifference = Math.abs(following.time.date - date);
  const nearest = firstDifference <= followingDifference ? first : following;

  return {
    time: nearest.time.date,
    direction: nearest.kind === Astronomy.NodeEventKind.Ascending
      ? "ascending"
      : "descending",
    ascendingLongitudeDegrees: modulo(
      Astronomy.EclipticGeoMoon(nearest.time.date).lon
        + (nearest.kind === Astronomy.NodeEventKind.Ascending ? 0 : 180),
      360,
    ),
  };
}

function getAstronomicalMoonMonth(date) {
  const searchStart = new Date(date.getTime() - 40 * 86400000);
  const firstNewMoon = Astronomy.SearchMoonPhase(0, searchStart, 40);
  if (!firstNewMoon) throw new RangeError("Could not find the surrounding new moon.");

  const followingNewMoon = Astronomy.SearchMoonPhase(
    0,
    new Date(firstNewMoon.date.getTime() + 1000),
    40,
  );
  const previousNewMoon = followingNewMoon && followingNewMoon.date <= date
    ? followingNewMoon
    : firstNewMoon;
  const currentFullMoon = Astronomy.SearchMoonPhase(
    180,
    new Date(previousNewMoon.date.getTime() + 1000),
    40,
  );
  if (!currentFullMoon) throw new RangeError("Could not find the full moon for this lunation.");

  const year = date.getUTCFullYear();
  const seasonStarts = [];
  for (let seasonYear = year - 1; seasonYear <= year + 1; seasonYear += 1) {
    const seasons = Astronomy.Seasons(seasonYear);
    seasonStarts.push(
      { date: seasons.dec_solstice.date, name: "Wintermond" },
      { date: seasons.mar_equinox.date, name: "Frühlingsmond" },
      { date: seasons.jun_solstice.date, name: "Sommermond" },
      { date: seasons.sep_equinox.date, name: "Herbstmond" },
    );
  }

  const firstFullMoons = seasonStarts
    .map((season) => ({
      ...season,
      firstFullMoon: Astronomy.SearchMoonPhase(
        180,
        new Date(season.date.getTime() + 1000),
        40,
      ),
    }))
    .filter((season) => season.firstFullMoon
      && season.firstFullMoon.date <= currentFullMoon.date)
    .sort((left, right) => left.date - right.date);
  const currentSeason = firstFullMoons.at(-1);
  if (!currentSeason) throw new RangeError("Could not determine the astronomical moon season.");

  let ordinal = 1;
  let fullMoon = currentSeason.firstFullMoon;
  while (fullMoon.date.getTime() < currentFullMoon.date.getTime() - 60000) {
    const nextFullMoon = Astronomy.SearchMoonPhase(
      180,
      new Date(fullMoon.date.getTime() + 1000),
      40,
    );
    if (!nextFullMoon || nextFullMoon.date > currentFullMoon.date) break;
    fullMoon = nextFullMoon;
    ordinal += 1;
  }

  return {
    name: `${currentSeason.name}${ordinal > 1 ? ` ${ordinal}` : ""}`,
    start: previousNewMoon.date,
  };
}

function getAstronomicalBabylonianMonthName(beginOfMonth, observer) {
  const getBaseMonthName = (monthStart) => {
    const fullMoon = Astronomy.SearchMoonPhase(
      180,
      new Date(monthStart.getTime() + 1000),
      40,
    );
    if (!fullMoon) throw new RangeError("Could not find the full moon for the Babylonian month.");

    const sun = Astronomy.Equator(
      Astronomy.Body.Sun,
      fullMoon.date,
      observer,
      true,
      true,
    );
    const monthIndex = Math.floor(sun.ra / 2);
    return BABYLONIAN_MONTH_NAMES[monthIndex];
  };

  const monthName = getBaseMonthName(beginOfMonth);
  const previousMonthName = getBaseMonthName(new Date(beginOfMonth.getTime() - 28 * 86400000));
  if (previousMonthName === monthName) return `${monthName} 2`;

  const followingMonthName = getBaseMonthName(new Date(beginOfMonth.getTime() + 28 * 86400000));
  if (followingMonthName === monthName) return `${monthName} 1`;
  return monthName;
}

function getGregorianEpact(year) {
  const goldenNumber = year % 19 + 1;
  const julianEpact = (11 * (goldenNumber - 1)) % 30;
  const century = Math.floor(year / 100);
  const solarCorrection = Math.floor(3 * (century + 1) / 4);
  const lunarCorrection = Math.floor((8 * century + 13) / 25);
  return {
    goldenNumber,
    epact: modulo(julianEpact - solarCorrection + lunarCorrection + 8, 30),
  };
}

function normalizeFixedCalendarDate(year, month, day) {
  const monthLength = LILIUS_CLAVIUS_MONTH_LENGTHS[month - 1];
  if (day > monthLength) {
    day -= monthLength;
    month += 1;
    if (month > 12) {
      month = 1;
      year += 1;
    }
  }
  return { year, month, day };
}

function getLiliusClaviusFullMoons(year) {
  const { goldenNumber, epact } = getGregorianEpact(year);
  const dates = [];

  if (epact === 25 && goldenNumber > 11) {
    for (let month = 1; month <= 12; month += 1) {
      const newLightDays = LILIUS_CLAVIUS_SPECIAL_NEW_LIGHT_DAYS[month - 1];
      const days = Array.isArray(newLightDays) ? newLightDays : [newLightDays];
      for (const day of days) {
        dates.push(normalizeFixedCalendarDate(year, month, day + 13));
      }
    }
    return dates;
  }

  for (let month = 1; month <= 12; month += 1) {
    const monthIndex = month - 1;
    for (let dayIndex = 0; dayIndex < LILIUS_CLAVIUS_MONTH_LENGTHS[monthIndex]; dayIndex += 1) {
      if (month === 3 && dayIndex < 6) continue;
      const predictedEpact = modulo(LILIUS_CLAVIUS_EPACT_STARTS[monthIndex] - dayIndex, 30);
      const hasDoubleEpact = LILIUS_CLAVIUS_DOUBLE_EPACT_DAYS.has(`${month}:${dayIndex + 1}`);
      if (epact === predictedEpact || (hasDoubleEpact && epact === 24)) {
        dates.push(normalizeFixedCalendarDate(year, month, dayIndex + 14));
      }
    }
  }
  return dates;
}

function getNextLiliusClaviusFullMoon(monthStart, timeZone) {
  const localStart = getZonedParts(monthStart, timeZone);
  const localStartValue = Date.UTC(
    localStart.year,
    localStart.month - 1,
    localStart.day,
    localStart.hour,
    localStart.minute,
    localStart.second,
  );
  const candidates = [];
  for (let year = localStart.year - 1; year <= localStart.year + 1; year += 1) {
    for (const fixedDate of getLiliusClaviusFullMoons(year)) {
      const candidateValue = Date.UTC(fixedDate.year, fixedDate.month - 1, fixedDate.day);
      if (candidateValue > localStartValue) candidates.push(fixedDate);
    }
  }
  candidates.sort((left, right) => Date.UTC(left.year, left.month - 1, left.day)
    - Date.UTC(right.year, right.month - 1, right.day));
  const nextFullMoon = candidates[0];
  if (!nextFullMoon) throw new RangeError("Could not find the next Lilius-Clavius full moon.");
  return nextFullMoon;
}

function getLiliusClaviusMonthName(beginOfMonth, timeZone) {
  const nextFullMoon = getNextLiliusClaviusFullMoon(beginOfMonth, timeZone);
  const monthDay = nextFullMoon.month * 100 + nextFullMoon.day;
  let seasonName;
  let seasonStartMonth;
  let seasonStartDay;
  let seasonStartYear = nextFullMoon.year;

  if (monthDay >= 321 && monthDay <= 621) {
    seasonName = "Frühlingsmond";
    seasonStartMonth = 3;
    seasonStartDay = 21;
  } else if (monthDay >= 622 && monthDay <= 922) {
    seasonName = "Sommermond";
    seasonStartMonth = 6;
    seasonStartDay = 22;
  } else if (monthDay >= 923 && monthDay <= 1220) {
    seasonName = "Herbstmond";
    seasonStartMonth = 9;
    seasonStartDay = 23;
  } else {
    seasonName = "Wintermond";
    seasonStartMonth = 12;
    seasonStartDay = 21;
    if (monthDay <= 320) seasonStartYear -= 1;
  }

  const seasonStartValue = Date.UTC(seasonStartYear, seasonStartMonth - 1, seasonStartDay);
  const targetFullMoonValue = Date.UTC(nextFullMoon.year, nextFullMoon.month - 1, nextFullMoon.day);
  const fixedFullMoons = new Map();
  for (let year = seasonStartYear; year <= nextFullMoon.year; year += 1) {
    for (const fullMoon of getLiliusClaviusFullMoons(year)) {
      const value = Date.UTC(fullMoon.year, fullMoon.month - 1, fullMoon.day);
      if (value >= seasonStartValue && value <= targetFullMoonValue) {
        fixedFullMoons.set(value, fullMoon);
      }
    }
  }

  const ordinal = fixedFullMoons.size;
  if (ordinal < 1) throw new RangeError("Could not count Lilius-Clavius full moons in the season.");
  return `${seasonName}${ordinal > 1 ? ` ${ordinal}` : ""}`;
}

function getMoonAboveHorizonDuration(observer, transit) {
  if (!transit) return null;

  const rise = Astronomy.SearchRiseSet(
    Astronomy.Body.Moon,
    observer,
    1,
    transit,
    -1,
  );
  const set = Astronomy.SearchRiseSet(
    Astronomy.Body.Moon,
    observer,
    -1,
    transit,
    1,
  );

  if (!rise || !set || set.date <= rise.date) return null;
  return (set.date - rise.date) / 3600000;
}

function getTrueSolarTimeHours(date, observer) {
  const hourAngle = Astronomy.HourAngle(Astronomy.Body.Sun, date, observer);
  const signedHourAngle = hourAngle >= 12 ? hourAngle - 24 : hourAngle;
  return modulo(12 + signedHourAngle, SIDEREAL_HOURS_PER_CIRCLE);
}

/**
 * Calculate the data needed by Astroclock for one instant and observer.
 * Dates are JavaScript Date objects; all returned event dates are UTC Date objects.
 */
export function calculateAstroData({
  date = new Date(),
  latitude = 50.75,
  longitude = 13.066667,
  elevationMeters = 0,
  timeZone = "Europe/Berlin",
} = {}) {
  if (!(date instanceof Date) || Number.isNaN(date.getTime())) {
    throw new TypeError("date must be a valid JavaScript Date.");
  }
  assertFiniteNumber(latitude, "latitude", -90, 90);
  assertFiniteNumber(longitude, "longitude", -180, 180);
  assertFiniteNumber(elevationMeters, "elevationMeters", -500, 100000);

  // Validate the IANA timezone before starting any astronomical searches.
  new Intl.DateTimeFormat("en", { timeZone }).format(date);

  const observer = new Astronomy.Observer(latitude, longitude, elevationMeters);
  const dayStart = localMidnight(date, timeZone);
  const sunPosition = getBodyPosition(Astronomy.Body.Sun, date, observer);
  const moonPosition = getBodyPosition(Astronomy.Body.Moon, date, observer);
  const moonIllumination = Astronomy.Illumination(Astronomy.Body.Moon, date);
  const moonPhaseAngle = Astronomy.MoonPhase(date);
  const moonEcliptic = Astronomy.EclipticGeoMoon(date);
  const nextNewMoon = Astronomy.SearchMoonPhase(0, date, 40);
  const nextFullMoon = Astronomy.SearchMoonPhase(180, date, 40);
  const solarEvents = getDailyEvents(Astronomy.Body.Sun, observer, dayStart);
  const lunarEvents = getDailyEvents(Astronomy.Body.Moon, observer, dayStart);
  const moonDistanceKm = moonPosition.distanceAU * KM_PER_AU;

  const planets = BODY_NAMES.map((name) => ({
    name,
    ...getBodyPosition(Astronomy.Body[name], date, observer),
  })).sort((left, right) => right.distanceAU - left.distanceAU);

  const localParts = getZonedParts(date, timeZone);
  const localDate = [
    String(localParts.year).padStart(4, "0"),
    String(localParts.month).padStart(2, "0"),
    String(localParts.day).padStart(2, "0"),
  ].join("-");

  const daylightHours = solarEvents.rise && solarEvents.set
    ? (solarEvents.set - solarEvents.rise) / 3600000
    : null;
  const astronomicalMonth = getAstronomicalMoonMonth(date);

  return {
    date: new Date(date),
    utc: date.toISOString(),
    localDate,
    localTime: new Intl.DateTimeFormat("de-DE", {
      timeZone,
      hour: "2-digit",
      minute: "2-digit",
      hourCycle: "h23",
    }).format(date),
    timeZone,
    location: { latitude, longitude, elevationMeters },
    siderealTimeHours: modulo(
      Astronomy.SiderealTime(date) + longitude / 15,
      SIDEREAL_HOURS_PER_CIRCLE,
    ),
    trueSolarTimeHours: getTrueSolarTimeHours(date, observer),
    sun: {
      ...sunPosition,
      eclipticLongitudeDegrees: Astronomy.SunPosition(date).elon,
    },
    moon: {
      ...moonPosition,
      astronomicalMonth: astronomicalMonth.name,
      babylonianMonth: getAstronomicalBabylonianMonthName(astronomicalMonth.start, observer),
      liliusClaviusMonth: getLiliusClaviusMonthName(astronomicalMonth.start, timeZone),
      phaseAngleDegrees: moonPhaseAngle,
      illuminationPercent: moonIllumination.phase_fraction * 100,
      waxing: nextFullMoon.date < nextNewMoon.date,
      eclipticLongitudeDegrees: moonEcliptic.lon,
      eclipticLatitudeDegrees: moonEcliptic.lat,
      distanceKm: moonDistanceKm,
      relativeBrightnessPercent: Math.round(
        -((moonDistanceKm - MEAN_MOON_DISTANCE_KM)
          / MEAN_MOON_DISTANCE_KM) * 200,
      ),
      nextNewMoon: nextNewMoon.date,
      nextFullMoon: nextFullMoon.date,
    },
    planets,
    events: {
      sunrise: solarEvents.rise,
      solarNoon: solarEvents.transit,
      sunset: solarEvents.set,
      moonrise: lunarEvents.rise,
      moonTransit: lunarEvents.transit,
      moonset: lunarEvents.set,
      daylightHours,
      moonAboveHorizonHours: getMoonAboveHorizonDuration(
        observer,
        lunarEvents.transit,
      ),
    },
    lunarNode: getMoonNode(date),
  };
}

/** Format an event Date in the configured timezone; null stays null. */
export function formatLocalDateTime(date, timeZone = "Europe/Berlin") {
  if (date === null || date === undefined) return null;
  return new Intl.DateTimeFormat("de-DE", {
    timeZone,
    dateStyle: "short",
    timeStyle: "medium",
  }).format(date);
}