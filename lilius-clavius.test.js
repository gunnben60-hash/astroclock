import test from "node:test";
import assert from "node:assert/strict";
import { getGoldenNumber, getLiliusClaviusMoonDay } from "./lilius-clavius.js";

test("goldene Zahl ist (Jahreszahl mod 19) + 1", () => {
  assert.equal(getGoldenNumber(2025), 12);
  assert.equal(getGoldenNumber(1995), 1);
  assert.equal(getGoldenNumber(-5), 15);
});

test("Zeilen des PDFs (1900-2199), dort mit Jahreszahl mod 19 beschriftet, hier +1", () => {
  assert.deepEqual(getLiliusClaviusMoonDay(2025, 1, 1), { newMoon: [1], fullMoon: [5] });
  assert.deepEqual(getLiliusClaviusMoonDay(2025, 1, 3), { newMoon: [9], fullMoon: [13] });
  assert.deepEqual(getLiliusClaviusMoonDay(2025, 1, 4), { newMoon: [], fullMoon: [2] });
  assert.deepEqual(getLiliusClaviusMoonDay(2025, 1, 5), { newMoon: [17], fullMoon: [] });
  assert.deepEqual(getLiliusClaviusMoonDay(2025, 1, 2), { newMoon: [], fullMoon: [] });
  assert.deepEqual(getLiliusClaviusMoonDay(2025, 6, 6), { newMoon: [], fullMoon: [7] });
});

test("Tabelle gilt für 1900 bis 2199 gleich", () => {
  for (const year of [1900, 1999, 2025, 2199]) {
    assert.deepEqual(getLiliusClaviusMoonDay(year, 1, 1), getLiliusClaviusMoonDay(2025, 1, 1));
  }
});

test("vor 1900 weicht die Tabelle ab", () => {
  assert.notDeepEqual(getLiliusClaviusMoonDay(1850, 1, 1), getLiliusClaviusMoonDay(2025, 1, 1));
  assert.notDeepEqual(getLiliusClaviusMoonDay(2200, 1, 1), getLiliusClaviusMoonDay(2025, 1, 1));
});

test("jede goldene Zahl hat 12 oder 13 Neumonde und Vollmonde im Zyklus", () => {
  const monthLengths = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
  for (const year of [1583, 1700, 1850, 2025, 2300, -400]) {
    const newCounts = new Map();
    const fullCounts = new Map();
    monthLengths.forEach((length, monthIndex) => {
      for (let day = 1; day <= length; day += 1) {
        const moons = getLiliusClaviusMoonDay(year, monthIndex + 1, day);
        moons.newMoon.forEach((n) => newCounts.set(n, (newCounts.get(n) ?? 0) + 1));
        moons.fullMoon.forEach((n) => fullCounts.set(n, (fullCounts.get(n) ?? 0) + 1));
      }
    });
    for (let number = 1; number <= 19; number += 1) {
      assert.ok([11, 12, 13].includes(newCounts.get(number)), `${year}: Neumond ${number}`);
      assert.ok([11, 12, 13].includes(fullCounts.get(number)), `${year}: Vollmond ${number}`);
    }
  }
});
