import random
import json
from datetime import datetime, timedelta

def generate_sensor_data(num_samples=50):
    """
    Génère des données simulées pour les capteurs.
    
    Args:
        num_samples (int): nombre de mesures à générer.
        
    Returns:
        list: liste de dictionnaires représentant les mesures.
    """
    data = []
    timestamp = datetime.now()
    
    for _ in range(num_samples):
        sample = {
            "temperature": round(random.uniform(20,40) + random.gauss(0, 1), 2),
            "smoke": int(random.uniform(200, 1500) + random.gauss(0,50)),
            "proximity": round(random.uniform(10,200), 1),
            "ir_flame": random.choice([0,1]),
            "timestamp": timestamp.isoformat()
        }
        data.append(sample)
        timestamp += timedelta(seconds=1)
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
    
    