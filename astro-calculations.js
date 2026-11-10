import * as Astronomy from "astronomy-engine";

const BODY_NAMES = ["Mercury", "Venus", "Mars", "Jupiter", "Saturn"];
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

  return {
    date: new Date(date),
    utc: date.toISOString(),
    localDate,
    localTime: new Intl.DateTimeFormat("de-DE", {
      timeZone,
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
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