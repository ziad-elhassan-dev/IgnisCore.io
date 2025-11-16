# Task 1: Rapid Rise Detection Prototype (Montée Rapide)

## Objective
Develop a prototype capable of detecting a rapid rise in temperature or smoke concentration from sensor data.  
The goal is to identify the early onset of a fire before the flame sensor activates, by analyzing abnormal trends in the measurements.

## Principle
The prototype analyzes the variation of sensor values (temperature, smoke, gas) over time.  
If the variation between two successive readings exceeds a defined threshold (ΔT/Δt > threshold), the system considers it a **rapid rise** and generates an alert.

The method relies on calculating the **rate of change**:
rate = (value_n - value_n-1) / Δt


Optional smoothing (moving average or Kalman filter) can reduce sensor noise and avoid false alarms.

## Proposed Approach
1. Generate or collect a time series of temperature and smoke readings.  
2. Compute the discrete derivative (change between consecutive points).  
3. Define a critical threshold (e.g., 2 °C/s).  
4. Detect and flag any period where the rise exceeds this threshold.  
5. Visualize the data curve to validate the threshold logic.

## Development Environment
- **Application:** Jupyter Lab (Notebook `.ipynb`)  
- **Language:** Python 3  
- **Libraries:** 
  - `NumPy` – numerical calculations and derivatives  
  - `Matplotlib` – visualization of trends  
  - `Pandas` – handling time series data  
  - *(Optional)* `SciPy` or `filterpy` for signal filtering  

## Required Materials
- **Software:** Jupyter Lab, Python 3  
- **Sensors:** DHT11/DHT22 (temperature), MQ2 or MQ135 (smoke/gas)  
- **Microcontroller:** ESP32 (for real-world testing)

## Expected Results
- A graph showing temperature/smoke over time, with rapid rise areas highlighted.  
- A Python function (example: `detect_rapid_rise(data, threshold, window)`) returning detected points.  
- Initial threshold parameters determined for fire detection.

## Deliverables
- `fire_trend_detection.ipynb` containing:
  - simulated sensor data  
  - rate-of-change calculation  
  - automatic detection of rapid rises  
  - visualizations  

- Short documentation explaining the logic and detection parameters.

## Final Goal
Validate the preliminary trend detection behavior before integrating the logic into the `FireDetector` class and the global system state machine.

# Task 2: Installer bibliothèques Python (numpy, scipy)

## Objective
Set up the Python environment for the IgnisCore project and install the essential libraries required for sensor data processing, numerical calculations, and signal analysis.  
The main libraries installed are:

- **NumPy** – for numerical operations and array manipulations.
- **SciPy** – for advanced mathematical functions and signal processing.

---

## Environment Setup

### 1. Create a Virtual Environment (Recommended)

A virtual environment isolates the project dependencies from the system Python, ensuring safe installation and preventing conflicts.

```bash
# Navigate to your project folder
cd /.../IgnisCore

# Create a virtual environment named 'venv'
python3 -m venv venv

# Activate the virtual environment
source venv/bin/activate   # On Linux / WSL
# Windows CMD: venv\Scripts\activate.bat
# PowerShell: venv\Scripts\Activate.ps1
```
### 2. Upgrade pip

```bash
pip install --upgrade pip
```

### 3. Install Required Libraries

```bash
pip install numpy scipy matplotlib pandas
```

- NumPy: array operations, numerical calculations, derivatives
- SciPy: signal processing, filtering, interpolation
- Matplotlib: data visualization and plotting
- Pandas: managing time series and sensor data

### 4. Verification

Open Python (or Jupyter Notebook) and run:

import numpy as np
import scipy
import matplotlib
import pandas as pd

print("NumPy version:", np.__version__)
print("SciPy version:", scipy.__version__)
print("Matplotlib version:", matplotlib.__version__)
print("Pandas version:", pd.__version__)

If no errors occur and the versions are printed, the installation is successful.

# Task 3: Définir les seuils de détection initiaux (incl. capteurs IR)

## Objective
Determine the **initial detection thresholds** for fire sensors, including temperature, smoke, gas, and infrared (IR) flame sensors.  
These thresholds will trigger early fire alerts before flames become visible, based on abnormal sensor readings.

---

## Principle

- Sensors have **normal ambient values** (room temperature, clean air, no flame).  
- Rapid increases or values above a threshold indicate potential fire.  
- Two types of thresholds:
  1. **Absolute threshold**: a fixed value that triggers an alert (e.g., temperature > 50°C).  
  2. **Rate-of-change threshold**: detects **rapid rises** in sensor readings (Δvalue/Δt).

- **IR flame sensors** detect actual flame radiation and can confirm the presence of fire even without smoke.

Initial thresholds are **starting points** and can be refined after real sensor testing or simulation.

---

## Approach to Define Thresholds

1. **Collect ambient data**:  
   - Measure temperature, smoke levels, and IR sensor output over time in normal conditions.  
   - Calculate mean and standard deviation for each sensor.

2. **Define absolute thresholds**:  
   - Temperature: mean + 3 × standard deviation  
   - Smoke / gas: mean + 3 × standard deviation  
   - IR flame sensor: define digital logic threshold (1 = flame detected)

3. **Define rate-of-change thresholds**:  
   - Calculate derivative of sensor readings over time: Δvalue/Δt  
   - Determine thresholds for rapid changes:  
     - ΔT > 2°C/s  
     - ΔSmoke > 50 ppm/s

4. **Simulation / Prototyping**:  
   - Generate simulated data with spikes to test thresholds.  
   - Include a simulated IR flame signal to test combined detection logic.  
   - Adjust thresholds as necessary.

---

## Development Environment

- **Python** with Jupyter Notebook for prototyping  
- **Libraries**: `NumPy`, `Pandas`, `Matplotlib`  
- **Sensors**:  
  - DHT22 (temperature)  
  - MQ2 / MQ135 (smoke/gas)  
  - IR flame sensor (digital output)  
- **Microcontroller**: ESP32 for real-world testing

---

## Deliverables

- Python dictionary of initial thresholds:

```python
thresholds = {
    "temperature_absolute": 50,    # °C
    "temperature_rate": 2,         # °C/s
    "smoke_absolute": 300,         # ppm
    "smoke_rate": 50,              # ppm/s
    "ir_flame": 1                   # digital 0 or 1, 1 = flame detected
}
```

- Plots of simulated data showing thresholds visually.
- Documentation explaining logic and rationale for chosen values.

## Example Detection Logic

```python
if flame_detected_ir or temperature > thresholds["temperature_absolute"] or smoke > thresholds["smoke_absolute"]:
    trigger_alert()

```

- Combines all sensors for reliable early fire detection.
- can also include rate-of-change detection for temperature and smoke for earlier warnings.

## Final Goal
- Provides baseline threshodls for the FireDetector module.
- Detect early-stage fires before they become critical.
- Thresholds can later be adjusted automatically or manually after testing.

# Task 4: Concevoir l’architecture de décision IA

## Objective
Design the AI decision architecture for the IgnisCore fire detection system.  
The goal is to process multiple sensor inputs and decide if a fire is detected, and which actions to trigger (alerts, water pump, logging).

---

## Principle

- Inputs: temperature, smoke/gas, IR/flame, optionally humidity or CO2.  
- Pre-processing: smoothing, derivative calculation (rate of change), normalization.  
- AI decision module: computes a risk score based on sensor inputs and thresholds.  
- Actions: triggers alerts and water pump if the risk exceeds a critical threshold.

---

## Architecture Overview

```
┌──────────────┐
│   Sensors    │
└──────────────┘
       │
       ▼
┌──────────────┐
│ Preprocessing│
│ Filtering    │
│ Normalization│
└──────────────┘
       │
       ▼
┌──────────────┐
│ Temp/Smoke/IR│
└──────────────┘
       │
       ▼
┌──────────────┐
│ AI / Decision│
│ Risk Score   │
│ Thresholds   │
└──────────────┘
       │
       ▼
┌──────────────┐
│ Actions      │
│ Alert/Pump   │
└──────────────┘

```

---

## Modules

| Module             | Role                                     |
|--------------------|------------------------------------------|
| `sensor_input.py`  | Read sensors (ESP32 or simulated data)   |
| `preprocessing.py` | Filter and normalize sensor data         |
| `fire_detector.py` | Calculate risk score and make decisions  |
| `actions.py`       | Trigger pump, buzzer, LEDs               |
| `logger.py`        | Store data for analytics and calibration |

---

## Example Decision Logic

```python
risk_score = 0.5 * temp_score + 0.3 * smoke_score + 0.2 * ir_score
if risk_score > critical_threshold:
    trigger_alert()
```
## Deliverables
- Diagram of AI decision architechture
- Python module skeletons
- Example simulation with sample sensor data to test risk score and decision logic

## Final Goal
- Provide a modular AI framework for fire detection 
- Enable a quick testing with simulated or real sensor data
- Integrate with ESP32 and the full project state machine

# Task 5: Définir le format de données capteurs (JSON)

## Objectif
Définir un format standardisé pour toutes les données des capteurs afin que :  

- Les lectures puissent être **stockées**,  
- Les données puissent être **transmises entre modules** (ESP32 → FireDetector → logger → analytics),  
- L’IA puisse **calculer le score de risque** efficacement.  

Le format choisi est **JSON**, pour sa légèreté, sa lisibilité et sa compatibilité avec Python et ESP32.

---

## Pourquoi JSON ?
- **Lisible par l’humain** et facilement manipulable en Python avec la librairie `json`.  
- **Flexible** : permet d’ajouter de nouveaux champs (`humidity`, `location`, `sensor_id`).  
- **Compatible IoT** : peut être transmis directement depuis l’ESP32 ou d’autres microcontrôleurs.

---

## Structure des données

| Champ          | Description                                                     |
|----------------|-----------------------------------------------------------------|
| `timestamp`    | Date et heure ISO de la mesure                                  |
| `temperature`  | Température en °C                                               |
| `smoke`        | Niveau de fumée / gaz en ppm                                    |
| `ir_flame`     | Détection de flamme IR (0 = pas de flamme, 1 = flamme détectée) |
| `humidity`     | Optionnel : humidité en %                                       |
| `location`     | Optionnel : emplacement du capteur ou nom du module             |

---

## Exemple de JSON

### Lecture unique
```json
{
  "timestamp": "2025-11-12T15:30:45",
  "temperature": 25.3,
  "smoke": 55.2,
  "ir_flame": 0,
  "proximity" : 220.5,
  "humidity": 40.5,
  "location": "robotic_arm_1"
}

```

### Plusieurs lectures json

```json
[
  {
    "timestamp": "2025-11-12T15:30:45",
    "temperature": 25.3,
    "smoke": 55.2,
    "ir_flame": 0,
    "proximity" : 120.5
  },
  {
    "timestamp": "2025-11-12T15:30:46",
    "temperature": 25.4,
    "smoke": 56.0,
    "ir_flame": 0,
    "proximity" : 20.5
  }
]
```

### Exemple Python pour generer Json

```python 
import json
from datetime import datetime

# Exemple de lecture simulée
sensor_data = {
    "timestamp": datetime.now().isoformat(),
    "temperature": 25.3,
    "smoke": 55.2,
    "ir_flame": 0,
    "humidity": 40.5,
    "location": "robotic_arm_1"
}

# Sauvegarder une lecture unique
with open("sensor_data.json", "w") as f:
    json.dump(sensor_data, f, indent=4)

# Pour plusieurs lectures
sensor_readings = [sensor_data]  # liste de lectures
with open("sensor_log.json", "w") as f:
    json.dump(sensor_readings, f, indent=4)
```

# Task 6: Module FireDetector (Prototype Python)

## Objectif
Créer un module Python réutilisable pour :
- Lire les données JSON des capteurs,
- Calculer un score de risque,
- Déterminer l’action à prendre (alerte / pompe).

## Utilisation
```python
from ai_brain.fire_detector import FireDetector

detector = FireDetector()
data = {
    "timestamp": "2025-11-12T15:30:45",
    "temperature": 55,
    "smoke": 350,
    "ir_flame": 1,
    "humidity": 40.5
}

preprocessed = detector.preprocess(data)
scores = detector.calculate_fire_risk(preprocessed)
action = detector.detect_fire(scores)
detector.log_result(scores, action)
```

## Structure du module:
- `read_data(file_path)` : lire un fichier JSON
- `preprocess(sensor_data)` : filtrer et normaliser
- `calc_score(sensor_data)` : calculer score global
- `decide_action(scores)` : déterminer l’action
- `log_result(scores, action)` : afficher ou sauvegarder le résultat

# Task 7 — Notebooks Jupyter pour expérimentations

## Objectif
- Tester et expérimenter le module `FireDetector`.
- Charger et prétraiter des données JSON simulées (ou réelles venant de l’ESP32).
- Calculer le score de risque de feu et détecter un incendie.
- Visualiser les scores avec des graphiques.
- Documenter les résultats et observations directement dans le notebook.

---

## Installation et setup

1. Activer votre environnement virtuel (venv) :

```bash
source env_jupyter/bin/activate   # Linux / WSL
# Windows CMD: env_jupyter\Scripts\activate.bat
# Windows PowerShell: env_jupyter\Scripts\Activate.ps1
```
2. Installer Jupyter et les bibliotheque necessaires :

```bash
pip install notebook matplotlib jupyterlab
```

3. Lancer Jupyter Notebook ou JupyterLab :

```bash
jupyter notebook
# ou
jupyter-lab
```
4. Le navigateur s'ouvrira automatiquement avec l'interface Jupyter.

## Structure recommandee du notebook
- Nom suggere : `FireDetector_Experiments.ipynb`

### Sections principales:
1. Imports et Setup
2. Chargement des donnees simulees
3. Calcul des scores et Detection
4. Visualisation
5. Experimentations et Notes

## Fichier JSON simule recommande
`simulated_fire.jason`:
```json
{
    "timestamp": "2025-11-16T18:00:00",
    "temperature": 55,
    "smoke": 350,
    "ir_flame": 1,
    "proximity": 20
}
```
## Livrables pour Task 7
1. `FireDetector_Experiment.ipynb` — Notebook d’expérimentation.
2. `simulated_fire.json` — Fichier JSON de test.
3. Graphiques et notes directement documentées dans le notebook.

# Task 8 — Algorithmes de fusion capteurs

## Objectif
- Étudier et documenter des méthodes pour combiner les données provenant de plusieurs capteurs (température, fumée, IR, proximité).
- Obtenir une estimation plus fiable du risque d'incendie.

## Méthodes étudiées

### 1. Filtre de Kalman
- Filtre récursif qui prend en compte l’incertitude des capteurs.
- Permet de prédire l’évolution des mesures et de filtrer le bruit.
- Bibliothèques Python : `filterpy`, `numpy`.

### 2. Moyenne mobile pondérée (Weighted Moving Average)
- Combine les mesures récentes avec des poids décroissants.
- Simple à implémenter et rapide.
- Sensible au choix des poids.

### 3. Lissage exponentiel (Exponential Smoothing)
- Poids exponentiellement décroissants pour les anciennes mesures.
- Réagit rapidement aux tendances récentes.
- Paramètre clé : alpha (facteur de lissage).

## Notes
- Ces méthodes serviront de base pour le Sprint 2.
- Chaque approche peut être testée sur des données simulées ou réelles.
- Comparer les performances pour choisir la meilleure fusion pour `FireDetector`.

# Task 9: Définir métriques de performance IA

## Objectif
Évaluer la performance du module FireDetector afin de garantir:
- Détection fiable des incendies
- Temps de réponse rapide
- Minimisation des fausses alertes

## Métriques définies

| Metric                   | Description                            | Target        |
|--------------------------|----------------------------------------|---------------|
| Précision                | Correct fire/no-fire detections        | >95%          |
| Faux positifs            | Alerts when no fire                    | <10%          |
| Latence décision         | Temps de décision AI                   | <100ms        |
| Temps réponse total      | End-to-end action                      | <5s           |
| Score de risque          | Corrélation avec incendies réels       | ≥0.9          |
| Robustesse bruit capteur | AI performance with noisy/missing data | Accuracy >90% |

## Méthode de mesure
1. Génération de données simulées pour différents scénarios
2. Comparaison avec les labels connus (fire/no-fire)
3. Mesure du temps de latence et du temps de réponse total
4. Tests de robustesse avec données bruitées ou manquantes

## Documentation
Tous les résultats et plots sont enregistrés dans Notion pour suivi et analyse.

# Task 10: Créer simulateur de données capteurs

## Objectif
Générer des données réalistes pour tester l'IA FireDetector sans utiliser le matériel réel.

## Fonctionnalités
- Température : 20–40°C avec bruit aléatoire
- Fumée : 200–1500 avec bruit
- Proximité : 10–200 cm
- IR Flame : 0 ou 1
- Timestamp : suivi temporel

## Utilisation
1. Exécuter le script `simulate_sensors.py` pour générer un fichier JSON avec les mesures simulées.
2. Charger les données simulées dans `FireDetector` pour tester l'algorithme.
3. Analyser les scores de risque et actions générées.

## Exemple de sortie
```json
{
  "temperature": 32.5,
  "smoke": 450,
  "proximity": 120.4,
  "ir_flame": 0,
  "timestamp": "2025-11-16T18:25:43.511234"
}
```

# Task 11: Étude des Patterns de Propagation du Feu

## 🎯 Objectif

L'objectif principal de cette tâche était de réaliser une recherche documentaire sur les mécanismes de propagation du feu dans trois environnements : 
- Espaces intérieurs (maisons, bâtiments)
- Environnements extérieurs (forêts, végétation)
- Véhicules (voitures, camions)

Cette étude visait à mieux comprendre les dynamiques de chaleur, de fumée, de vitesse de propagation, afin de guider le développement des algorithmes de détection et de décision de l’IA.

---

## 📄 Résultat

Un document PDF synthétique d’une page a été rédigé à partir de sources scientifiques et techniques. Il présente de façon structurée :
- La vitesse typique de propagation du feu
- Les profils de température et de fumée
- Les implications pour la détection précoce

---

## 📁 Emplacement du fichier

Le document est disponible ici :  
`docs\Modèles de propagation du feu.pdf`

---

## 🧠 Utilisation dans le projet

Les données extraites dans cette étude sont utilisées pour :

- Calibrer les seuils de détection de température, fumée et flamme (Task 3)
- Concevoir l’architecture de décision de l’IA (Task 4)
- Simuler des scénarios réalistes pour entraînement et tests (Task 10)
- Définir des métriques de performance réalistes pour la détection (Task 9)

Cette tâche constitue donc une base de référence essentielle pour assurer que l’IA est alignée avec les réalités physiques des incendies selon différents contextes d’usage.

---
