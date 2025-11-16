import random
import os
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

def generate_balanced_data(n_fire=50, n_normal=50):
    data = []
    timestamp = datetime.now()

    # Scénarios feu
    for _ in range(n_fire):
        timestamp += timedelta(seconds=1)
        data.append({
            "timestamp": timestamp.isoformat(),
            "temperature": random.uniform(60, 120),
            "smoke": random.uniform(400, 2000),
            "ir_flame": 1,
            "proximity": random.uniform(10, 200)
        })
    
    # Scénarios normaux
    for _ in range(n_normal):
        timestamp += timedelta(seconds=1)
        data.append({
            "timestamp": timestamp.isoformat(),
            "temperature": random.uniform(20, 45),
            "smoke": random.uniform(50, 250),
            "ir_flame": 0,
            "proximity": random.uniform(10, 200)
        })
    
    # Mélanger les données pour simuler l'ordre aléatoire
    random.shuffle(data)
    return data


def save_to_json(data, file_name="simulated_fire_data.json"):
    """
    Sauvegarde les données simulées dans le dossier 'data' à la racine du projet.
    """
    # Chemin absolu vers le dossier racine du projet
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    
    # Créer le dossier data dans le projet si nécessaire
    data_folder = os.path.join(project_root, "data")
    os.makedirs(data_folder, exist_ok=True)
    
    # Chemin complet vers le fichier
    file_path = os.path.join(data_folder, file_name)
    
    # Écriture du JSON
    with open(file_path, "w") as f:
        json.dump(data, f, indent=4)
    
    print(f"Fichier de données simulées créé: {file_path}")
    
if __name__ == "__main__":
    simulated_data = generate_sensor_data(100)
    save_to_json(simulated_data, "simulated_fire_random.json")
    simulated_balanced_data = generate_balanced_data(50, 50)
    save_to_json(simulated_balanced_data, "simulated_fire_balanced.json")
    
    