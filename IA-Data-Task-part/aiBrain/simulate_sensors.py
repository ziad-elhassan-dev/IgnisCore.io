import random
import json
from datetime import datetime, timedelta

def generate_sensor_data(n=100):
    data = []
    timestamp = datetime.now()

    for _ in range(n):
        timestamp += timedelta(seconds=1)

        # Température : conditions normales + pics incendie
        base_temp = random.uniform(20, 45)
        fire_temp = random.uniform(60, 120)
        temperature = fire_temp if random.random() < 0.15 else base_temp  # 15% chance fire

        # Fumée : conditions normales + fumée forte
        base_smk = random.uniform(50, 250)
        fire_smk = random.uniform(400, 2000)
        smoke = fire_smk if random.random() < 0.20 else base_smk  # 20% chance fire

        # Capteur IR : maintenant + nuancé + pas trop dominant
        ir_flame = 1 if random.random() < 0.10 else 0  # 10% chance of flame detection

        # Distance
        proximity = random.uniform(10, 200)

        data.append({
            "timestamp": timestamp.isoformat(),
            "temperature": temperature,
            "smoke": smoke,
            "ir_flame": ir_flame,
            "proximity": proximity
        })

    return data

def save_to_json(data, file_name="simulated_fire_data.json"):
    """
    Sauvegarde les données simulées dans un fichier JSON.
    
    Args:
        data (list): liste des mesures simulées
        file_name (str): nom du fichier de sortie
    """
    with open(file_name, "w") as f:
        json.dump(data, f, indent=4)
    print(f"Fichier de données simulées créé: {file_name}")
    
if __name__ == "__main__":
    simulated_data = generate_sensor_data(100)
    save_to_json(simulated_data)
    
    