#!/usr/bin/env python3
"""
Generate raw sensor dataset for fire patrol robot.
Only contains: timer + raw sensor readings (ppm, temp, humidity).
Nothing else. No warnings. No alerts. No motor data.
All logic (warnings, FSM, movement) computed live by the software.

Sensor simulation:
  MQ-4 gas sensor  -> ppm (methane/smoke proxy)
  DHT11            -> temperature (°C) + humidity (%RH)

Real-world profile:
  0-299   : normal environment, stable readings with natural noise
  300-329 : smoke starts building (gradual ppm rise, slightly warmer)
  330-499 : fire event (ppm and temp rise sharply)
  500-549 : fire dies down (ppm/temp slowly return)
  550-599 : back to normal

600 frames x 500ms = 5 minutes total
"""

import json
import random
import math
from datetime import datetime, timedelta


random.seed(42)


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def lerp(a, b, t):
    return a + (b - a) * clamp(t, 0.0, 1.0)


def mq4_raw(ppm):
    """Simulate MQ-4 ADC and voltage from ppm value."""
    rs_r0   = round(clamp(5.0 * (80.0 / ppm) ** 0.6, 0.3, 5.5), 3)
    voltage = round(clamp(5.0 * rs_r0 / (rs_r0 + 1.0), 0.4, 4.9), 2)
    adc     = int(voltage / 5.0 * 1023)
    return adc, voltage, rs_r0


def heat_index(temp, hum):
    """Simplified Steadman heat index."""
    hi = temp + 0.33 * (hum / 100 * 6.105 * math.exp(17.27 * temp / (237.7 + temp))) - 4.0
    return round(hi, 1)


def generate():
    data      = []
    timestamp = datetime(2026, 3, 10, 14, 32, 0)
    uptime_ms = 0

    for i in range(600):
        # ── Raw sensor values ─────────────────────────────────────────────────
        # Small random noise on every frame (realistic sensor jitter)
        n_ppm  = random.gauss(0, 1.2)
        n_temp = random.gauss(0, 0.2)
        n_hum  = random.gauss(0, 0.8)

        if i < 300:
            ppm  = clamp(78.0 + n_ppm  + math.sin(i * 0.04) * 1.2, 74.0, 84.0)
            temp = clamp(24.0 + n_temp + math.sin(i * 0.02) * 0.4, 23.0, 25.5)
            hum  = clamp(60.0 + n_hum,  54.0, 66.0)

        elif i < 330:
            t    = (i - 300) / 29.0
            ppm  = clamp(lerp(79.0, 135.0, t)  + n_ppm  * 2.0, 76.0, 140.0)
            temp = clamp(lerp(24.0,  29.0, t)  + n_temp,        23.0,  31.0)
            hum  = clamp(lerp(60.0,  50.0, t)  + n_hum,         46.0,  63.0)

        elif i < 400:
            t    = (i - 330) / 69.0
            ppm  = clamp(lerp(135.0, 540.0, t ** 0.65) + n_ppm  * 6.0, 130.0, 550.0)
            temp = clamp(lerp( 29.0,  58.0, t ** 0.75) + n_temp,         27.0,  60.0)
            hum  = clamp(lerp( 50.0,  20.0, t)         + n_hum,          16.0,  52.0)

        elif i < 500:
            t    = (i - 400) / 99.0
            ppm  = clamp(lerp(540.0, 615.0, t) + n_ppm  * 10.0, 525.0, 628.0)
            temp = clamp(lerp( 58.0,  63.0, t) + n_temp,          56.0,  65.0)
            hum  = clamp(lerp( 20.0,  16.0, t) + n_hum,           13.0,  22.0)

        elif i < 550:
            t    = (i - 500) / 49.0
            ppm  = clamp(lerp(615.0, 160.0, t ** 0.55) + n_ppm  * 7.0, 155.0, 620.0)
            temp = clamp(lerp( 63.0,  36.0, t ** 0.65) + n_temp,         34.0,  65.0)
            hum  = clamp(lerp( 16.0,  42.0, t)         + n_hum,          14.0,  46.0)

        else:
            t    = (i - 550) / 49.0
            ppm  = clamp(lerp(160.0,  79.0, t) + n_ppm  * 2.0, 75.0, 165.0)
            temp = clamp(lerp( 36.0,  24.0, t) + n_temp,         23.0,  38.0)
            hum  = clamp(lerp( 42.0,  60.0, t) + n_hum,          40.0,  64.0)

        ppm  = round(ppm,  1)
        temp = round(temp, 1)
        hum  = round(hum,  1)

        adc, voltage, rs_r0 = mq4_raw(ppm)
        hi = heat_index(temp, hum)

        entry = {
            "timer": {
                "timestamp_utc": timestamp.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                "uptime_ms":     uptime_ms,
            },
            "air_quality": {
                "sensor": {"id": "mq4-001", "type": "MQ-4"},
                "readings": {
                    "raw": {
                        "adc_value": adc,
                        "voltage":   voltage,
                        "rs_r0":     rs_r0,
                    },
                    "processed": {
                        "ppm":  ppm,
                        "unit": "ppm",
                    },
                },
            },
            "temperature": {
                "sensor": {"id": "dht11-001", "type": "DHT11"},
                "readings": {
                    "temperature": {"value": temp, "unit": "C"},
                    "humidity":    {"value": hum,  "unit": "%RH"},
                    "heat_index":  {"value": hi,   "unit": "C"},
                },
            },
        }

        data.append(entry)
        timestamp += timedelta(milliseconds=500)
        uptime_ms += 500

    return data


if __name__ == "__main__":
    data = generate()

    out = "dataset_robot_fire_detection_001.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    ppms  = [e["air_quality"]["readings"]["processed"]["ppm"] for e in data]
    temps = [e["temperature"]["readings"]["temperature"]["value"] for e in data]

    print(f"Generated {len(data)} frames -> {out}")
    print(f"Duration : {len(data) * 0.5:.0f}s  ({len(data) * 0.5 / 60:.1f} min)")
    print(f"PPM      : {min(ppms):.1f} - {max(ppms):.1f}")
    print(f"Temp     : {min(temps):.1f} - {max(temps):.1f} C")
    print()
    print("Sample frames:")
    print(f"  {'Frame':>5}  {'PPM':>7}  {'Temp':>6}  {'Hum':>5}")
    for i in [0, 100, 299, 315, 335, 370, 420, 499, 520, 560, 599]:
        e    = data[i]
        ppm  = e["air_quality"]["readings"]["processed"]["ppm"]
        temp = e["temperature"]["readings"]["temperature"]["value"]
        hum  = e["temperature"]["readings"]["humidity"]["value"]
        print(f"  {i:5d}  {ppm:7.1f}  {temp:6.1f}  {hum:5.1f}")
    print()
    print("First entry:")
    import json as j
    print(j.dumps(data[0], indent=2))