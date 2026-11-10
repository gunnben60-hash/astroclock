import { calculateAstroData } from "../astro-calculations.js";

const DEFAULT_LOCATION = {
  latitude: 50.75,
  longitude: 13.066667,
  timeZone: "Europe/Berlin",
};
const SYMBOLS = ["♈︎", "♉︎", "♊︎", "♋︎", "♌︎", "♍︎", "♎︎", "♏︎", "♐︎", "♑︎", "♒︎", "♓︎"];
const OBLIQUITY_RADIANS = 23.43928 * Math.PI / 180;
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
const locationForm = document.querySelector("#location-form");
const settingsError = document.querySelector("#settings-error");
const formatterCache = new Map();
let location = readLocation();
let selectedDate = new Date();
let live = true;
let lastCalculatedMinute = -1;
let currentData;
let dragStart = null;

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
  return `${String(parts.year).padStart(4, "0")}-${String(parts.month).padStart(2, "0")}-${String(parts.day).padStart(2, "0")}T${String(parts.hour).padStart(2, "0")}:${String(parts.minute).padStart(2, "0")}:${String(parts.second).padStart(2, "0")}`;
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
  document.querySelector("#place-label").textContent = location.latitude === DEFAULT_LOCATION.latitude
    && location.longitude === DEFAULT_LOCATION.longitude ? "Zschopau, Deutschland" : "Beobachtungsort";
  document.querySelector("#solar-time").textContent = formatClockHours(data.trueSolarTimeHours);
  document.querySelector("#sidereal-time").textContent = formatClockHours(data.siderealTimeHours);
  document.querySelector("#sunrise").textContent = formatEvent(data.events.sunrise);
  document.querySelector("#solar-noon").textContent = formatEvent(data.events.solarNoon);
  document.querySelector("#sunset").textContent = formatEvent(data.events.sunset);
  document.querySelector("#moonrise").textContent = formatEvent(data.events.moonrise);
  document.querySelector("#moonset").textContent = formatEvent(data.events.moonset);
  document.querySelector("#daylight").textContent = formatDuration(data.events.daylightHours);
  document.querySelector("#daylight-bar").style.width = `${Math.max(0, Math.min(100, (data.events.daylightHours ?? 0) / 24 * 100))}%`;
  document.querySelector("#moon-illumination").textContent = `${Math.round(data.moon.illuminationPercent)} % beleuchtet`;
  document.querySelector("#moon-phase").textContent = getMoonPhase(data.moon.illuminationPercent, data.moon.waxing);
  document.querySelector("#moon-disc").style.setProperty("--phase", `${data.moon.illuminationPercent}%`);
  document.querySelector("#moon-disc").classList.toggle("waxing", data.moon.waxing);
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

function getMoonPhase(illumination, waxing) {
  if (illumination < 2) return "Neumond";
  if (illumination > 98) return "Vollmond";
  if (illumination < 48) return waxing ? "Zunehmende Sichel" : "Abnehmende Sichel";
  if (illumination < 52) return waxing ? "Erstes Viertel" : "Letztes Viertel";
  return waxing ? "Zunehmender Mond" : "Abnehmender Mond";
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
    context.strokeStyle = radius === 216 ? "#e4b458" : "#e3e3da";
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
    const labelPosition = polar(angle, 280);
    context.fillStyle = "#29362e";
    context.font = `${index % 2 === 0 ? "700 14px" : "500 11px"} 'DM Mono', monospace`;
    context.textAlign = "center";
    context.textBaseline = "middle";
    context.fillText(["XII", "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI"][index % 12], labelPosition.x, labelPosition.y);
  }

  const siderealAngle = data.siderealTimeHours * Math.PI / 12;
  for (let index = 0; index < 12; index += 1) {
    const boundaryRightAscension = eclipticLongitudeToRightAscension(index * 30);
    const angle = siderealAngle - boundaryRightAscension + Math.PI;
    const inner = polar(angle, 176);
    const outer = polar(angle, 216);
    context.beginPath();
    context.moveTo(inner.x, inner.y);
    context.lineTo(outer.x, outer.y);
    context.strokeStyle = index === 0 ? "#d46a4b" : "#9ba69a";
    context.lineWidth = index === 0 ? 1.8 : 1;
    context.stroke();
    const signRightAscension = eclipticLongitudeToRightAscension(index * 30 + 15);
    const sign = polar(siderealAngle - signRightAscension + Math.PI, 195);
    context.fillStyle = "#68776b";
    context.font = "18px 'Segoe UI Symbol', 'Noto Sans Symbols 2', serif";
    context.fillText(SYMBOLS[index], sign.x, sign.y);
  }

  const bodies = [
    { name: "Sonne", body: data.sun, color: "#d89432", symbol: "☉", size: 9 },
    { name: "Mond", body: data.moon, color: "#667b83", symbol: "☾", size: 8 },
    ...data.planets.map((planet) => ({
      name: planet.name, body: planet, color: "#d46a4b", symbol: PLANET_SYMBOLS[planet.name], size: 5,
    })),
  ];
  for (const item of bodies) {
    const angle = siderealAngle - item.body.rightAscensionHours * Math.PI / 12 + Math.PI;
    const radius = 216 + Math.max(-1, Math.min(1, item.body.declinationDegrees / 23.44)) * 72;
    const point = polar(angle, radius);
    context.beginPath();
    context.moveTo(center, center);
    context.lineTo(point.x, point.y);
    context.strokeStyle = `${item.color}55`;
    context.lineWidth = 1;
    context.stroke();
    context.beginPath();
    context.arc(point.x, point.y, item.size, 0, Math.PI * 2);
    context.fillStyle = item.color;
    context.fill();
    context.fillStyle = "#28332d";
    context.font = `${item.name === "Sonne" || item.name === "Mond" ? "17px" : "15px"} 'Manrope', serif`;
    context.textAlign = "center";
    context.textBaseline = "middle";
    context.fillText(item.symbol, point.x, point.y);
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
    localStorage.setItem("astroclock-location", JSON.stringify(location));
    document.querySelector("#settings-panel").open = false;
    render();
  } catch (error) {
    settingsError.textContent = `Standort konnte nicht übernommen werden: ${error.message}`;
  }
});

canvas.addEventListener("pointerdown", (event) => {
  const bounds = canvas.getBoundingClientRect();
  const x = (event.clientX - bounds.left) / bounds.width * 720 - 360;
  const y = (event.clientY - bounds.top) / bounds.height * 720 - 360;
  dragStart = Math.atan2(y, x);
  canvas.setPointerCapture(event.pointerId);
});
canvas.addEventListener("pointerup", (event) => {
  if (dragStart === null) return;
  const bounds = canvas.getBoundingClientRect();
  const x = (event.clientX - bounds.left) / bounds.width * 720 - 360;
  const y = (event.clientY - bounds.top) / bounds.height * 720 - 360;
  const end = Math.atan2(y, x);
  let shift = (end - dragStart) / (Math.PI * 2);
  if (shift > 0.5) shift -= 1;
  if (shift < -0.5) shift += 1;
  dragStart = null;
  if (Math.abs(shift) > 0.005) {
    live = false;
    selectedDate = new Date(selectedDate.getTime() + shift * 86400000);
    render();
  }
});
canvas.addEventListener("pointercancel", () => { dragStart = null; });

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