import { calculateAstroData } from "../astro-calculations.js";

const DEFAULT_LOCATION = {
  latitude: 50.75,
  longitude: 13.066667,
  timeZone: "Europe/Berlin",
};
const CLIENT_TIME_ZONE = new Intl.DateTimeFormat().resolvedOptions().timeZone
  || DEFAULT_LOCATION.timeZone;
const SYMBOLS = ["♈︎", "♉︎", "♊︎", "♋︎", "♌︎", "♍︎", "♎︎", "♏︎", "♐︎", "♑︎", "♒︎", "♓︎"];
const OBLIQUITY_RADIANS = 23.43928 * Math.PI / 180;
const LUNAR_ORBIT_INCLINATION_RADIANS = 5.145 * Math.PI / 180;
const PLANET_SYMBOLS = {
  Mercury: "☿",
  Venus: "♀",
  Mars: "♂",
  Jupiter: "♃",
  Saturn: "♄",
};
const canvas = document.querySelector("#astro-clock");
const context = canvas.getContext("2d");
const dateInput = document.querySelector("#datetime-input");
const historicalEventInput = document.querySelector("#historical-event");
const locationForm = document.querySelector("#location-form");
const settingsError = document.querySelector("#settings-error");
const formatterCache = new Map();
let location = { ...readLocation(), timeZone: CLIENT_TIME_ZONE };
let locationSource = "detecting";
let selectedDate = new Date();
let live = true;
let lastCalculatedMinute = -1;
let currentData;
let dragStart = null;
let pendingDragShift = 0;
let dragFrame = null;

function readLocation() {
  try {
    const saved = JSON.parse(localStorage.getItem("astroclock-location"));
    if (saved && Number.isFinite(saved.latitude) && Number.isFinite(saved.longitude)
      && typeof saved.timeZone === "string") {
      return saved;
    }
  } catch {
    // Ignore unavailable or malformed browser storage.
  }
  return { ...DEFAULT_LOCATION };
}

function getBrowserLocation() {
  return new Promise((resolve, reject) => {
    if (!navigator.geolocation) {
      reject(new Error("Browser-Geolokalisierung ist nicht verfügbar."));
      return;
    }
    navigator.geolocation.getCurrentPosition(resolve, reject, {
      enableHighAccuracy: true,
      maximumAge: 300000,
      timeout: 10000,
    });
  });
}

async function getApproximateLocation() {
  const response = await fetch("https://ipapi.co/json/", {
    headers: { Accept: "application/json" },
  });
  if (!response.ok) throw new Error("IP-Standortdienst ist nicht erreichbar.");

  const result = await response.json();
  const latitude = Number(result.latitude);
  const longitude = Number(result.longitude);
  if (result.error || !Number.isFinite(latitude) || Math.abs(latitude) > 90
    || !Number.isFinite(longitude) || Math.abs(longitude) > 180) {
    throw new Error("IP-Standortdienst lieferte keine gültigen Koordinaten.");
  }
  return { latitude, longitude };
}

async function detectClientLocation() {
  try {
    const position = await getBrowserLocation();
    location = {
      ...location,
      latitude: position.coords.latitude,
      longitude: position.coords.longitude,
      timeZone: CLIENT_TIME_ZONE,
    };
    locationSource = position.coords.accuracy > 1000 ? "approximate" : "exact";
  } catch {
    try {
      const approximateLocation = await getApproximateLocation();
      location = { ...location, ...approximateLocation, timeZone: CLIENT_TIME_ZONE };
      locationSource = "approximate";
    } catch {
      locationSource = "fallback";
    }
  }

  try {
    localStorage.setItem("astroclock-location", JSON.stringify(location));
  } catch {
    // Keep the detected location for this session if storage is unavailable.
  }
  render();
}

function getFormatter(timeZone, options) {
  const key = `${timeZone}:${JSON.stringify(options)}`;
  if (!formatterCache.has(key)) {
    formatterCache.set(key, new Intl.DateTimeFormat("de-DE", { timeZone, ...options }));
  }
  return formatterCache.get(key);
}

function zonedParts(date, timeZone) {
  return Object.fromEntries(getFormatter(timeZone, {
    year: "numeric", month: "2-digit", day: "2-digit",
    hour: "2-digit", minute: "2-digit", second: "2-digit", hourCycle: "h23",
  }).formatToParts(date)
    .filter((part) => part.type !== "literal")
    .map((part) => [part.type, Number(part.value)]));
}

function localDateTimeToDate(value, timeZone) {
  const [datePart, timePart = "00:00:00"] = value.split("T");
  const [year, month, day] = datePart.split("-").map(Number);
  const [hour, minute, second = 0] = timePart.split(":").map(Number);
  const desiredUtc = Date.UTC(year, month - 1, day, hour, minute, second);
  let guess = desiredUtc;
  for (let attempt = 0; attempt < 4; attempt += 1) {
    const parts = zonedParts(new Date(guess), timeZone);
    const representedUtc = Date.UTC(parts.year, parts.month - 1, parts.day,
      parts.hour, parts.minute, parts.second);
    const adjustment = desiredUtc - representedUtc;
    guess += adjustment;
    if (adjustment === 0) break;
  }
  return new Date(guess);
}

function localInputValue(date) {
  const parts = zonedParts(date, location.timeZone);
  return `${String(parts.year).padStart(4, "0")}-${String(parts.month).padStart(2, "0")}-${String(parts.day).padStart(2, "0")}T${String(parts.hour).padStart(2, "0")}:${String(parts.minute).padStart(2, "0")}`;
}

function formatClockHours(hours) {
  const totalMinutes = Math.floor((((hours % 24) + 24) % 24) * 60 + 0.5);
  return `${String(Math.floor(totalMinutes / 60) % 24).padStart(2, "0")}:${String(totalMinutes % 60).padStart(2, "0")}`;
}

function formatEvent(date) {
  if (!date) return "—";
  return getFormatter(location.timeZone, { hour: "2-digit", minute: "2-digit", hourCycle: "h23" }).format(date);
}

function formatDuration(hours) {
  if (hours === null) return "Nicht verfügbar";
  const roundedMinutes = Math.round(hours * 60);
  return `${Math.floor(roundedMinutes / 60)} Std. ${String(roundedMinutes % 60).padStart(2, "0")} Min.`;
}

function eclipticLongitudeToRightAscension(longitudeDegrees) {
  const longitude = longitudeDegrees * Math.PI / 180;
  const rightAscension = Math.atan2(
    Math.sin(longitude) * Math.cos(OBLIQUITY_RADIANS),
    Math.cos(longitude),
  );
  return (rightAscension + Math.PI * 2) % (Math.PI * 2);
}

function eclipticToEquatorial(longitudeDegrees, latitudeDegrees) {
  const longitude = longitudeDegrees * Math.PI / 180;
  const latitude = latitudeDegrees * Math.PI / 180;
  const rightAscension = Math.atan2(
    Math.sin(longitude) * Math.cos(OBLIQUITY_RADIANS)
      - Math.tan(latitude) * Math.sin(OBLIQUITY_RADIANS),
    Math.cos(longitude),
  );
  const declination = Math.asin(
    Math.sin(latitude) * Math.cos(OBLIQUITY_RADIANS)
      + Math.cos(latitude) * Math.sin(OBLIQUITY_RADIANS) * Math.sin(longitude),
  );
  const normalizedRightAscension = (rightAscension + Math.PI * 2) % (Math.PI * 2);
  return {
    rightAscension: normalizedRightAscension,
    rightAscensionHours: normalizedRightAscension * 12 / Math.PI,
    declinationDegrees: declination * 180 / Math.PI,
  };
}

function render() {
  try {
    currentData = calculateAstroData({ date: selectedDate, ...location });
    lastCalculatedMinute = Math.floor(selectedDate.getTime() / 60000);
    updateDisplay(currentData);
    drawClock(currentData);
    settingsError.textContent = "";
  } catch (error) {
    settingsError.textContent = error.message;
    document.querySelector("#status-label").textContent = "ZEITZONE PRÜFEN";
  }
}

function updateDisplay(data) {
  const parts = zonedParts(selectedDate, location.timeZone);
  const shortZone = getFormatter(location.timeZone, { timeZoneName: "short" })
    .formatToParts(selectedDate).find((part) => part.type === "timeZoneName")?.value ?? location.timeZone;
  document.querySelector("#clock-time").textContent = data.localTime;
  document.querySelector("#date-label").textContent = getFormatter(location.timeZone, {
    weekday: "long", day: "numeric", month: "long", year: "numeric",
  }).format(selectedDate);
  document.querySelector("#zone-tag").textContent = shortZone;
  document.querySelector("#timezone-label").textContent = location.timeZone.toUpperCase();
  document.querySelector("#coordinates-label").textContent = `${Math.abs(location.latitude).toFixed(4)}° ${location.latitude >= 0 ? "N" : "S"} · ${Math.abs(location.longitude).toFixed(4)}° ${location.longitude >= 0 ? "E" : "W"}`;
  const placeLabels = {
    detecting: "Standort wird ermittelt…",
    exact: "Aktueller Standort",
    approximate: "Ungefährer Standort",
    manual: "Manuell eingestellt",
    fallback: "Standort nicht ermittelt",
  };
  document.querySelector("#place-label").textContent = locationSource === "exact"
    && location.latitude === DEFAULT_LOCATION.latitude
    && location.longitude === DEFAULT_LOCATION.longitude
    ? "Zschopau, Deutschland"
    : placeLabels[locationSource] ?? "Beobachtungsort";
  document.querySelector("#solar-time").textContent = formatClockHours(data.trueSolarTimeHours);
  document.querySelector("#sidereal-time").textContent = formatClockHours(data.siderealTimeHours);
  document.querySelector("#sunrise").textContent = formatEvent(data.events.sunrise);
  document.querySelector("#solar-noon").textContent = formatEvent(data.events.solarNoon);
  document.querySelector("#sunset").textContent = formatEvent(data.events.sunset);
  document.querySelector("#moonrise").textContent = formatEvent(data.events.moonrise);
  document.querySelector("#moonset").textContent = formatEvent(data.events.moonset);
  document.querySelector("#daylight").textContent = formatDuration(data.events.daylightHours);
  document.querySelector("#daylight-bar").style.width = `${Math.max(0, Math.min(100, (data.events.daylightHours ?? 0) / 24 * 100))}%`;
  document.querySelector("#moon-above-duration").textContent = formatDuration(data.events.moonAboveHorizonHours);
  document.querySelector("#moon-above-bar").style.width = `${Math.max(0, Math.min(100, (data.events.moonAboveHorizonHours ?? 0) / 24 * 100))}%`;
  document.querySelector("#moon-illumination").textContent = `${Math.round(data.moon.illuminationPercent)} % beleuchtet`;
  document.querySelector("#moon-phase").textContent = getMoonPhase(data.moon.phaseAngleDegrees);
  drawMoonDisc(data.moon.phaseAngleDegrees);
  updateMoonPhaseEvents(data.moon);
  document.querySelector("#astronomical-month-name").textContent = data.moon.astronomicalMonth;
  document.querySelector("#babylonian-month-name").textContent = data.moon.babylonianMonth;
  document.querySelector("#hijri-month-name").textContent = new Intl.DateTimeFormat(
    "ar-SA-u-ca-islamic-umalqura",
    { calendar: "islamic-umalqura", timeZone: location.timeZone, month: "long" },
  ).format(selectedDate);
  dateInput.value = localInputValue(selectedDate);
  document.querySelector("#latitude-input").value = location.latitude;
  document.querySelector("#longitude-input").value = location.longitude;
  document.querySelector("#timezone-input").value = location.timeZone;
  document.querySelector("#status-label").textContent = "HIMMELSDATEN";
  document.querySelector("#live-button").classList.toggle("is-live", live);
  document.querySelector("#live-button").setAttribute("aria-pressed", String(live));
  document.querySelector("#live-button").innerHTML = `<span class="live-dot"></span> ${live ? "LIVE" : "PAUSIERT"}`;
  if (!Number.isFinite(parts.year)) throw new Error("Die gewählte Zeitzone ist ungültig.");
}

function getMoonPhase(phaseAngleDegrees) {
  const phaseAngle = ((phaseAngleDegrees % 360) + 360) % 360;
  if (phaseAngle <= 15 || phaseAngle >= 345) return "Neumond";
  if (phaseAngle < 83) return "Zunehmende Sichel";
  if (phaseAngle <= 97) return "Erstes Viertel";
  if (phaseAngle < 165) return "Zunehmender Mond";
  if (phaseAngle <= 195) return "Vollmond";
  if (phaseAngle < 263) return "Abnehmender Mond";
  if (phaseAngle <= 277) return "Letztes Viertel";
  return "Abnehmende Sichel";
}

function updateMoonPhaseEvents(moon) {
  const upcomingPhases = [
    { name: "Neumond", date: moon.nextNewMoon },
    { name: "Vollmond", date: moon.nextFullMoon },
  ].sort((left, right) => left.date - right.date);
  const formatter = getFormatter(location.timeZone, {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    hourCycle: "h23",
  });
  const list = document.querySelector("#moon-phase-events");
  list.replaceChildren(...upcomingPhases.map(({ name, date }) => {
    const row = document.createElement("div");
    row.className = "moon-phase-event";
    const phaseName = document.createElement("span");
    phaseName.textContent = name;
    const phaseDate = document.createElement("time");
    phaseDate.dateTime = date.toISOString();
    phaseDate.textContent = formatter.format(date);
    row.append(phaseName, phaseDate);
    return row;
  }));
}

function drawMoonDisc(phaseAngleDegrees) {
  const moonCanvas = document.querySelector("#moon-disc");
  const moonContext = moonCanvas.getContext("2d");
  const size = moonCanvas.width;
  const center = size / 2;
  const radius = center - 3;
  const phaseAngle = ((phaseAngleDegrees % 360) + 360) % 360 * Math.PI / 180;
  const lightX = Math.sin(phaseAngle);
  const lightZ = -Math.cos(phaseAngle);
  const image = moonContext.createImageData(size, size);

  for (let y = 0; y < size; y += 1) {
    for (let x = 0; x < size; x += 1) {
      const normalX = (x + 0.5 - center) / radius;
      const normalY = (y + 0.5 - center) / radius;
      const squaredDistance = normalX * normalX + normalY * normalY;
      if (squaredDistance > 1) continue;

      const normalZ = Math.sqrt(1 - squaredDistance);
      const illumination = normalX * lightX + normalZ * lightZ;
      const blend = Math.max(0, Math.min(1, (illumination + 0.025) / 0.05));
      const surfaceShade = 0.68 + 0.32 * Math.max(0, illumination);
      const pixel = (y * size + x) * 4;
      image.data[pixel] = 77 + (218 * surfaceShade - 77) * blend;
      image.data[pixel + 1] = 94 + (219 * surfaceShade - 94) * blend;
      image.data[pixel + 2] = 99 + (211 * surfaceShade - 99) * blend;
      image.data[pixel + 3] = 255;
    }
  }

  moonContext.clearRect(0, 0, size, size);
  moonContext.putImageData(image, 0, 0);
}

function drawSunSphere(targetContext, x, y, radius) {
  targetContext.save();
  targetContext.shadowColor = "rgba(218, 164, 54, 0.55)";
  targetContext.shadowBlur = radius * 0.65;
  targetContext.beginPath();
  targetContext.arc(x, y, radius, 0, Math.PI * 2);
  const gradient = targetContext.createRadialGradient(
    x - radius * 0.34,
    y - radius * 0.4,
    radius * 0.08,
    x,
    y,
    radius,
  );
  gradient.addColorStop(0, "#fff3c4");
  gradient.addColorStop(0.35, "#f6d875");
  gradient.addColorStop(0.74, "#d79e31");
  gradient.addColorStop(1, "#8c5a1d");
  targetContext.fillStyle = gradient;
  targetContext.fill();
  targetContext.shadowBlur = 0;
  targetContext.strokeStyle = "#fff0b0";
  targetContext.lineWidth = radius * 0.08;
  targetContext.stroke();
  targetContext.restore();
}

function drawSilverSphere(targetContext, x, y, radius) {
  targetContext.save();
  targetContext.shadowColor = "rgba(35, 48, 57, 0.4)";
  targetContext.shadowBlur = radius * 0.55;
  targetContext.beginPath();
  targetContext.arc(x, y, radius, 0, Math.PI * 2);
  const gradient = targetContext.createRadialGradient(
    x - radius * 0.34,
    y - radius * 0.4,
    radius * 0.08,
    x,
    y,
    radius,
  );
  gradient.addColorStop(0, "#ffffff");
  gradient.addColorStop(0.38, "#dce3e5");
  gradient.addColorStop(0.76, "#9aa8ae");
  gradient.addColorStop(1, "#596970");
  targetContext.fillStyle = gradient;
  targetContext.fill();
  targetContext.shadowBlur = 0;
  targetContext.strokeStyle = "rgba(247, 249, 242, 0.9)";
  targetContext.lineWidth = radius * 0.1;
  targetContext.stroke();
  targetContext.restore();
}

function getMoonLightDirection(moon, sun, siderealAngle) {
  const moonRa = moon.rightAscension;
  const moonDec = moon.declinationDegrees * Math.PI / 180;
  const sunRa = sun.rightAscension;
  const sunDec = sun.declinationDegrees * Math.PI / 180;
  const moonVector = [
    Math.cos(moonDec) * Math.cos(moonRa),
    Math.cos(moonDec) * Math.sin(moonRa),
    Math.sin(moonDec),
  ];
  const sunVector = [
    Math.cos(sunDec) * Math.cos(sunRa),
    Math.cos(sunDec) * Math.sin(sunRa),
    Math.sin(sunDec),
  ];
  const alignment = sunVector.reduce((sum, component, index) => (
    sum + component * moonVector[index]
  ), 0);
  const dialPoint = (body) => {
    const angle = siderealAngle - body.rightAscension + Math.PI;
    const radius = 216 + body.declinationDegrees / 23.44 * 72;
    return {
      x: 360 - Math.sin(angle) * radius,
      y: 360 + Math.cos(angle) * radius,
    };
  };
  const moonPoint = dialPoint(moon);
  const sunPoint = dialPoint(sun);
  const screenX = sunPoint.x - moonPoint.x;
  const screenY = sunPoint.y - moonPoint.y;
  const screenLength = Math.hypot(screenX, screenY);
  const transverseLight = Math.sqrt(Math.max(0, 1 - alignment * alignment));

  if (screenLength < 1e-8) return { x: 0, y: 0, z: -alignment };
  return {
    x: screenX / screenLength * transverseLight,
    y: screenY / screenLength * transverseLight,
    z: -alignment,
  };
}

function drawMoonSphere(targetContext, x, y, radius, lightDirection) {
  const textureSize = 128;
  const texture = document.createElement("canvas");
  texture.width = textureSize;
  texture.height = textureSize;
  const textureContext = texture.getContext("2d");
  const image = textureContext.createImageData(textureSize, textureSize);
  const center = textureSize / 2;
  const sphereRadius = center - 2;

  for (let pixelY = 0; pixelY < textureSize; pixelY += 1) {
    for (let pixelX = 0; pixelX < textureSize; pixelX += 1) {
      const normalX = (pixelX + 0.5 - center) / sphereRadius;
      const normalY = (pixelY + 0.5 - center) / sphereRadius;
      const squaredDistance = normalX * normalX + normalY * normalY;
      if (squaredDistance > 1) continue;

      const normalZ = Math.sqrt(1 - squaredDistance);
      const illumination = normalX * lightDirection.x
        + normalY * lightDirection.y
        + normalZ * lightDirection.z;
      const blend = Math.max(0, Math.min(1, (illumination + 0.025) / 0.05));
      const darkSilver = 0.58 + 0.42 * normalZ;
      const litSilver = 0.76 + 0.24 * normalZ;
      const pixel = (pixelY * textureSize + pixelX) * 4;
      image.data[pixel] = 74 * darkSilver + (226 * litSilver - 74 * darkSilver) * blend;
      image.data[pixel + 1] = 82 * darkSilver + (231 * litSilver - 82 * darkSilver) * blend;
      image.data[pixel + 2] = 91 * darkSilver + (234 * litSilver - 91 * darkSilver) * blend;
      image.data[pixel + 3] = 255;
    }
  }

  textureContext.putImageData(image, 0, 0);
  targetContext.save();
  targetContext.shadowColor = "rgba(17, 29, 38, 0.55)";
  targetContext.shadowBlur = radius * 0.35;
  targetContext.drawImage(texture, x - radius, y - radius, radius * 2, radius * 2);
  targetContext.shadowBlur = 0;
  targetContext.beginPath();
  targetContext.arc(x, y, radius - 0.4, 0, Math.PI * 2);
  targetContext.strokeStyle = "rgba(248, 249, 239, 0.8)";
  targetContext.lineWidth = radius * 0.068;
  targetContext.stroke();
  targetContext.restore();
}

function drawTwilightShading(targetContext, latitudeRadians) {
  const layerSize = 720;
  const center = layerSize / 2;
  const layer = document.createElement("canvas");
  layer.width = layerSize;
  layer.height = layerSize;
  const layerContext = layer.getContext("2d");
  const image = layerContext.createImageData(layerSize, layerSize);
  const sinLatitude = Math.sin(latitudeRadians);
  const cosLatitude = Math.cos(latitudeRadians);

  for (let y = 0; y < layerSize; y += 1) {
    const deltaY = y + 0.5 - center;
    for (let x = 0; x < layerSize; x += 1) {
      const deltaX = x + 0.5 - center;
      const radius = Math.hypot(deltaX, deltaY);
      if (radius > 327) continue;

      const declination = (radius - 216) / 72 * 23.44 * Math.PI / 180;
      const cosHourAngle = radius > 0 ? -deltaY / radius : -1;
      const sinAltitude = sinLatitude * Math.sin(declination)
        + cosLatitude * Math.cos(declination) * cosHourAngle;
      const altitude = Math.asin(Math.max(-1, Math.min(1, sinAltitude))) * 180 / Math.PI;
      let shade;
      if (altitude < -18) shade = [34, 52, 67, 36];
      else if (altitude < -12) shade = [49, 68, 81, 29];
      else if (altitude < -6) shade = [69, 86, 96, 21];
      else if (altitude < 0) shade = [93, 107, 114, 13];
      else continue;

      const pixel = (y * layerSize + x) * 4;
      image.data[pixel] = shade[0];
      image.data[pixel + 1] = shade[1];
      image.data[pixel + 2] = shade[2];
      image.data[pixel + 3] = shade[3];
    }
  }

  layerContext.putImageData(image, 0, 0);
  targetContext.drawImage(layer, 0, 0);
}

function drawClock(data) {
  const scale = window.devicePixelRatio || 1;
  canvas.width = 720 * scale;
  canvas.height = 720 * scale;
  context.setTransform(scale, 0, 0, scale, 0, 0);
  context.clearRect(0, 0, 720, 720);
  const center = 360;
  const polar = (angle, radius) => ({
    x: center - Math.sin(angle) * radius,
    y: center + Math.cos(angle) * radius,
  });

  context.strokeStyle = "#d8d9cf";
  context.lineWidth = 1;
  context.beginPath();
  context.arc(center, center, 327, 0, Math.PI * 2);
  context.stroke();
  for (const radius of [288, 216, 144]) {
    context.beginPath();
    context.arc(center, center, radius, 0, Math.PI * 2);
    context.strokeStyle = radius === 216 ? "#e4b458" : "#d2ad43";
    context.lineWidth = radius === 216 ? 1 : 1.15;
    context.stroke();
  }

  const latitude = location.latitude * Math.PI / 180;
  drawTwilightShading(context, latitude);
  const horizonSamples = 720;
  const altitudeLines = [
    { degrees: 0, color: "#66766e", width: 1.8 },
    { degrees: -6, color: "#929894", width: 1 },
    { degrees: -12, color: "#818783", width: 1 },
    { degrees: -18, color: "#818783", width: 1 },
  ];
  for (const altitudeLine of altitudeLines) {
    const altitude = altitudeLine.degrees * Math.PI / 180;
    let drawingLine = false;
    context.beginPath();
    for (let sample = 0; sample <= horizonSamples; sample += 1) {
      const azimuth = Math.PI * 2 * sample / horizonSamples;
      const declination = Math.asin(
        Math.sin(latitude) * Math.sin(altitude)
        - Math.cos(latitude) * Math.cos(azimuth) * Math.cos(altitude),
      );
      const hourAngle = Math.atan2(
        Math.sin(latitude) * Math.cos(azimuth)
          + Math.cos(latitude) * Math.tan(altitude),
        Math.sin(azimuth),
      ) + Math.PI / 2;
      const declinationDegrees = declination * 180 / Math.PI;
      const radius = 216 + declinationDegrees / 23.44 * 72;
      if (radius <= 0 || radius > 327) {
        drawingLine = false;
        continue;
      }
      const point = polar(hourAngle, radius);
      if (drawingLine) context.lineTo(point.x, point.y);
      else context.moveTo(point.x, point.y);
      drawingLine = true;
    }
    context.strokeStyle = altitudeLine.color;
    context.lineWidth = altitudeLine.width;
    context.stroke();
  }

  context.strokeStyle = "#d2ad43";
  context.lineWidth = 1.15;
  for (let hourDivision = -5; hourDivision <= 5; hourDivision += 1) {
    let drawingTemporalLine = false;
    context.beginPath();
    for (let sample = 0; sample <= horizonSamples; sample += 1) {
      const azimuth = Math.PI * 2 * sample / horizonSamples;
      const declination = Math.asin(
        -Math.cos(latitude) * Math.cos(azimuth),
      );
      const hourAngle = Math.atan2(
        Math.sin(latitude) * Math.cos(azimuth),
        Math.sin(azimuth),
      ) + Math.PI / 2;
      const declinationDegrees = declination * 180 / Math.PI;
      const visibleDayArc = (hourAngle > 0 && hourAngle < Math.PI)
        || (hourAngle > Math.PI && hourAngle < Math.PI * 1.5);
      if (!visibleDayArc || declinationDegrees < -23.44 || declinationDegrees > 23.44) {
        drawingTemporalLine = false;
        continue;
      }

      const spanFromMeridian = (Math.PI - hourAngle) / 6;
      const angle = Math.PI + spanFromMeridian * hourDivision;
      const radius = 216 + declinationDegrees / 23.44 * 72;
      const point = polar(angle, radius);
      if (drawingTemporalLine) context.lineTo(point.x, point.y);
      else context.moveTo(point.x, point.y);
      drawingTemporalLine = true;
    }
    context.stroke();
  }

  for (let index = 0; index < 24; index += 1) {
    const angle = index * Math.PI / 12;
    const outer = polar(angle, 327);
    const inner = polar(angle, index % 2 === 0 ? 306 : 316);
    context.beginPath();
    context.moveTo(inner.x, inner.y);
    context.lineTo(outer.x, outer.y);
    context.strokeStyle = index % 6 === 0 ? "#4d5e51" : "#aeb4a9";
    context.lineWidth = index % 6 === 0 ? 1.7 : 1;
    context.stroke();
    const labelPosition = polar(angle, 294);
    context.fillStyle = "#29362e";
    context.font = "500 13px 'DM Mono', monospace";
    context.textAlign = "center";
    context.textBaseline = "middle";
    context.fillText(["XII", "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI"][index % 12], labelPosition.x, labelPosition.y);
  }

  const siderealAngle = data.siderealTimeHours * Math.PI / 12;
  for (let index = 0; index < 12; index += 1) {
    const boundaryRightAscension = eclipticLongitudeToRightAscension(index * 30);
    const angle = siderealAngle - boundaryRightAscension + Math.PI;
    const inner = polar(angle, 112);
    const outer = polar(angle, 144);
    context.beginPath();
    context.moveTo(inner.x, inner.y);
    context.lineTo(outer.x, outer.y);
    context.strokeStyle = index === 0 ? "#d46a4b" : "#b4a16e";
    context.lineWidth = index === 0 ? 1.8 : 1.15;
    context.stroke();
    const signRightAscension = eclipticLongitudeToRightAscension(index * 30 + 15);
    const sign = polar(siderealAngle - signRightAscension + Math.PI, 127);
    context.fillStyle = "#4e6258";
    context.font = "17px 'Segoe UI Symbol', 'Noto Sans Symbols 2', serif";
    context.fillText(SYMBOLS[index], sign.x, sign.y);
  }

  const eclipticLongitudeAt = (fraction) => fraction * 360;
  const drawOrbitalPlane = (latitudeAt, color, lineWidth, dotted = false) => {
    context.beginPath();
    for (let sample = 0; sample <= 360; sample += 1) {
      const longitude = eclipticLongitudeAt(sample / 360);
      const equatorial = eclipticToEquatorial(longitude, latitudeAt(longitude));
      const angle = siderealAngle - equatorial.rightAscension + Math.PI;
      const radius = 216 + equatorial.declinationDegrees / 23.44 * 72;
      const point = polar(angle, radius);
      if (sample === 0) context.moveTo(point.x, point.y);
      else context.lineTo(point.x, point.y);
    }
    context.strokeStyle = color;
    context.lineWidth = lineWidth;
    context.setLineDash(dotted ? [2, 4] : []);
    context.stroke();
    context.setLineDash([]);
  };

  drawOrbitalPlane(() => 0, "#477caa", 1.7);
  const moonLongitudeRadians = data.moon.eclipticLongitudeDegrees * Math.PI / 180;
  const moonLatitudeRadians = data.moon.eclipticLatitudeDegrees * Math.PI / 180;
  const ascendingNodeRadians = data.lunarNode.ascendingLongitudeDegrees * Math.PI / 180;
  const longitudeFromNode = Math.sin(moonLongitudeRadians - ascendingNodeRadians);
  let instantaneousInclination = LUNAR_ORBIT_INCLINATION_RADIANS;
  if (Math.abs(longitudeFromNode) > 0.05) {
    const sineInclination = Math.sin(moonLatitudeRadians) / longitudeFromNode;
    if (Math.abs(sineInclination) <= 1) {
      instantaneousInclination = Math.asin(sineInclination);
    }
  }
  drawOrbitalPlane(
    (longitude) => Math.asin(
      Math.sin(instantaneousInclination)
        * Math.sin((longitude - data.lunarNode.ascendingLongitudeDegrees) * Math.PI / 180),
    ) * 180 / Math.PI,
    "#477caa",
    1.35,
    true,
  );

  for (const node of [
    { longitude: data.lunarNode.ascendingLongitudeDegrees, symbol: "☊" },
    { longitude: (data.lunarNode.ascendingLongitudeDegrees + 180) % 360, symbol: "☋" },
  ]) {
    const equatorial = eclipticToEquatorial(node.longitude, 0);
    const angle = siderealAngle - equatorial.rightAscension + Math.PI;
    const radius = 216 + equatorial.declinationDegrees / 23.44 * 72;
    const point = polar(angle, radius);
    context.beginPath();
    context.arc(point.x, point.y, 9, 0, Math.PI * 2);
    context.fillStyle = "#fbfaf5";
    context.fill();
    context.strokeStyle = "#477caa";
    context.lineWidth = 2;
    context.stroke();
    context.fillStyle = "#315d80";
    context.font = "bold 12px 'Segoe UI Symbol', 'Noto Sans Symbols 2', serif";
    context.textAlign = "center";
    context.textBaseline = "middle";
    context.fillText(node.symbol, point.x, point.y);
  }

  const geocentricMoon = eclipticToEquatorial(
    data.moon.eclipticLongitudeDegrees,
    data.moon.eclipticLatitudeDegrees,
  );
  const geocentricSun = eclipticToEquatorial(data.sun.eclipticLongitudeDegrees, 0);
  const moonLightDirection = getMoonLightDirection(
    geocentricMoon,
    geocentricSun,
    siderealAngle,
  );
  const bodies = [
    { name: "Sonne", body: data.sun, color: "#d89432" },
    {
      name: "Mond",
      body: { ...data.moon, ...geocentricMoon },
      color: "#667b83",
    },
    ...data.planets.map((planet) => ({
      name: planet.name,
      body: planet,
      color: "#aeb9bd",
      symbol: PLANET_SYMBOLS[planet.name],
    })),
  ].sort((left, right) => right.body.distanceAU - left.body.distanceAU);
  for (const item of bodies) {
    const angle = siderealAngle - item.body.rightAscensionHours * Math.PI / 12 + Math.PI;
    const radius = 216 + item.body.declinationDegrees / 23.44 * 72;
    const point = polar(angle, radius);
    context.beginPath();
    context.moveTo(center, center);
    context.lineTo(point.x, point.y);
    context.strokeStyle = `${item.color}55`;
    context.lineWidth = 1;
    context.stroke();
    if (item.name === "Sonne") {
      drawSunSphere(context, point.x, point.y, 12);
    } else if (item.name === "Mond") {
      drawMoonSphere(context, point.x, point.y, 11.3, moonLightDirection);
    } else {
      drawSilverSphere(context, point.x, point.y, 6);
      const symbolPoint = polar(angle, radius + 18);
      context.font = "bold 18px 'Segoe UI Symbol', 'Noto Sans Symbols 2', serif";
      context.textAlign = "center";
      context.textBaseline = "middle";
      context.lineWidth = 3;
      context.strokeStyle = "rgba(251, 250, 245, 0.94)";
      context.strokeText(item.symbol, symbolPoint.x, symbolPoint.y);
      context.fillStyle = "#435761";
      context.fillText(item.symbol, symbolPoint.x, symbolPoint.y);
    }
  }

  context.beginPath();
  context.arc(center, center, 5, 0, Math.PI * 2);
  context.fillStyle = "#34473a";
  context.fill();
}

function changeDay(amount) {
  live = false;
  selectedDate = new Date(selectedDate.getTime() + amount * 86400000);
  render();
}

function pointerAngle(event) {
  const bounds = canvas.getBoundingClientRect();
  const x = (event.clientX - bounds.left) / bounds.width * 720 - 360;
  const y = (event.clientY - bounds.top) / bounds.height * 720 - 360;
  return Math.atan2(y, x);
}

function queueDragShift(angle) {
  let shift = (angle - dragStart) / (Math.PI * 2);
  if (shift > 0.5) shift -= 1;
  if (shift < -0.5) shift += 1;
  dragStart = angle;
  pendingDragShift += shift;
  if (dragFrame === null) {
    dragFrame = window.requestAnimationFrame(applyDragShift);
  }
}

function applyDragShift() {
  dragFrame = null;
  if (pendingDragShift === 0) return;
  live = false;
  selectedDate = new Date(selectedDate.getTime() + pendingDragShift * 86400000);
  pendingDragShift = 0;
  render();
}

dateInput.addEventListener("change", () => {
  if (!dateInput.value) return;
  live = false;
  try {
    selectedDate = localDateTimeToDate(dateInput.value, location.timeZone);
    render();
  } catch (error) {
    settingsError.textContent = error.message;
  }
});

historicalEventInput.addEventListener("change", () => {
  if (!historicalEventInput.value) return;
  live = false;
  try {
    selectedDate = localDateTimeToDate(
      `${historicalEventInput.value}T12:00`,
      location.timeZone,
    );
    render();
  } catch (error) {
    settingsError.textContent = error.message;
  } finally {
    historicalEventInput.value = "";
  }
});

document.querySelector("#previous-day").addEventListener("click", () => changeDay(-1));
document.querySelector("#next-day").addEventListener("click", () => changeDay(1));
document.querySelector("#now-button").addEventListener("click", () => {
  selectedDate = new Date();
  live = true;
  render();
});
document.querySelector("#live-button").addEventListener("click", () => {
  live = !live;
  if (live) selectedDate = new Date();
  render();
});

locationForm.addEventListener("submit", (event) => {
  event.preventDefault();
  const nextLocation = {
    latitude: Number(document.querySelector("#latitude-input").value),
    longitude: Number(document.querySelector("#longitude-input").value),
    timeZone: document.querySelector("#timezone-input").value.trim(),
  };
  try {
    new Intl.DateTimeFormat("de-DE", { timeZone: nextLocation.timeZone }).format(selectedDate);
    if (!Number.isFinite(nextLocation.latitude) || Math.abs(nextLocation.latitude) > 90
      || !Number.isFinite(nextLocation.longitude) || Math.abs(nextLocation.longitude) > 180) {
      throw new RangeError("Breiten- oder Längengrad liegt außerhalb des gültigen Bereichs.");
    }
    location = nextLocation;
    locationSource = "manual";
    localStorage.setItem("astroclock-location", JSON.stringify(location));
    document.querySelector("#settings-panel").open = false;
    render();
  } catch (error) {
    settingsError.textContent = `Standort konnte nicht übernommen werden: ${error.message}`;
  }
});

canvas.addEventListener("pointerdown", (event) => {
  dragStart = pointerAngle(event);
  pendingDragShift = 0;
  canvas.setPointerCapture(event.pointerId);
});
canvas.addEventListener("pointermove", (event) => {
  if (dragStart === null) return;
  queueDragShift(pointerAngle(event));
});
canvas.addEventListener("pointerup", (event) => {
  if (dragStart === null) return;
  queueDragShift(pointerAngle(event));
  dragStart = null;
  if (dragFrame !== null) {
    window.cancelAnimationFrame(dragFrame);
    applyDragShift();
  }
});
canvas.addEventListener("pointercancel", () => {
  dragStart = null;
  if (dragFrame !== null) {
    window.cancelAnimationFrame(dragFrame);
    applyDragShift();
  }
});

window.setInterval(() => {
  if (!live) return;
  const now = new Date();
  const minute = Math.floor(now.getTime() / 60000);
  if (minute !== lastCalculatedMinute) {
    selectedDate = now;
    render();
  }
}, 1000);

render();
detectClientLocation();