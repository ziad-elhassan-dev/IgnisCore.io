# simulate_sensors.py

import random
import json
from datetime import datetime, timedelta


def generate_sensor_data(n=100):
    """Generate n random sensor readings with ~15% fire chance."""
    data = []
    timestamp = datetime.now()
    for _ in range(n):
        timestamp += timedelta(seconds=1)
        base_temp = random.uniform(20, 45)
        fire_temp = random.uniform(60, 120)
        temperature = fire_temp if random.random() < 0.15 else base_temp
        base_smk = random.uniform(50, 250)
        fire_smk = random.uniform(400, 2000)
        smoke = fire_smk if random.random() < 0.20 else base_smk
        ir_flame = 1 if random.random() < 0.10 else 0
        proximity = random.uniform(10, 200)
        data.append({
            "timestamp": timestamp.isoformat(),
            "temperature": temperature,
            "smoke": smoke,
            "ir_flame": ir_flame,
            "proximity": proximity
        })
    return data


def generate_balanced_data(n_fire=50, n_normal=50):
    """Generate perfectly balanced fire and normal scenarios."""
    data = []
    timestamp = datetime.now()
    for _ in range(n_fire):
        timestamp += timedelta(seconds=1)
        data.append({
            "timestamp": timestamp.isoformat(),
            "temperature": random.uniform(60, 120),
            "smoke": random.uniform(400, 2000),
            "ir_flame": 1,
            "proximity": random.uniform(10, 200)
        })
    for _ in range(n_normal):
        timestamp += timedelta(seconds=1)
        data.append({
            "timestamp": timestamp.isoformat(),
            "temperature": random.uniform(20, 45),
            "smoke": random.uniform(50, 250),
            "ir_flame": 0,
            "proximity": random.uniform(10, 200)
        })
    random.shuffle(data)
    return data


def generate_rapid_fire_scenarios(n=100):
    """
    Generate scenarios with 30% rapid-rise events.
    These are cases where values rise fast but may not cross absolute thresholds yet.
    Used to test delta-based detection.
    """
    data = []
    timestamp = datetime.now()
    for _ in range(n):
        timestamp += timedelta(seconds=1)
        is_rapid = random.random() < 0.30
        if is_rapid:
            data.append({
                "timestamp": timestamp.isoformat(),
                "temperature": random.uniform(50, 75),
                "smoke": random.uniform(250, 450),
                "ir_flame": 0,
                "proximity": random.uniform(10, 200)
            })
        else:
            data.append({
                "timestamp": timestamp.isoformat(),
                "temperature": random.uniform(20, 45),
                "smoke": random.uniform(50, 250),
                "ir_flame": 0,
                "proximity": random.uniform(10, 200)
            })
    return data


def save_to_json(data, filename):
    """Save sensor data list to a JSON file."""
    with open(filename, "w") as f:
        json.dump(data, f, indent=2)
    print(f"[simulate_sensors] Saved {len(data)} entries to '{filename}'")


if __name__ == "__main__":
    data = generate_balanced_data(n_fire=50, n_normal=50)
    save_to_json(data, "test_data_100.json")
    print(f"Generated {len(data)} entries.")