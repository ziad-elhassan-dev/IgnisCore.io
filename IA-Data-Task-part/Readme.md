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
source ~/venv/bin/activate   # Linux / WSL
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

# Task 12 – Prototype Système de Scoring avec Pondérations

## Objectif
Tester et choisir la meilleure configuration de pondérations pour le calcul du **score de risque incendie** dans le module `FireDetector`.  
Les pondérations ajustent l’influence des mesures de **température** et **fumée** sur le score global afin d’optimiser la détection des incendies tout en minimisant les faux positifs.

---

## Méthodologie

1. **Définir plusieurs configurations de pondérations** :
   - `A_0.3_0.7` : Température 30%, Fumée 70%
   - `B_0.4_0.6` : Température 40%, Fumée 60%
   - `C_0.5_0.5` : Température 50%, Fumée 50%

2. **Tester chaque configuration** sur un ensemble de données simulées (générées par `simulate_sensors.py`).

3. **Mesurer les métriques clés** :
   - Nombre d’alertes déclenchées (`fires_detected`)
   - Score moyen global (`avg_score`)

4. **Visualiser les résultats** :
   - Comparer les pondérations à l’aide d’un graphique barres pour voir l’impact sur les scores et les alertes.

---

## Exemple de code

```python
from FireDetector import FireDetector
from simulate_sensors import generate_sensor_data
import pandas as pd
import matplotlib.pyplot as plt

# Générer données de test
data = generate_sensor_data(50)

# Configurations de pondérations à tester
configs = {
    "A_0.3_0.7": (0.3, 0.7),
    "B_0.4_0.6": (0.4, 0.6),
    "C_0.5_0.5": (0.5, 0.5),
}

results = []

for name, (w_temp, w_smoke) in configs.items():
    detector = FireDetector(weight_temp=w_temp, weight_smoke=w_smoke, weight_ir=0)
    fire_count = 0
    scores_list = []

    for entry in data:
        pre = detector.preprocess(entry)
        scores = detector.calculate_fire_risk(pre)
        if detector.detect_fire(scores) == "WARNING: start alarm":
            fire_count += 1
        scores_list.append(scores["global"])

    avg_score = sum(scores_list) / len(scores_list)

    results.append({
        "config": name,
        "fires_detected": fire_count,
        "avg_score": avg_score
    })

# Visualisation
df = pd.DataFrame(results)
print(df)
df.plot(x="config", y=["fires_detected", "avg_score"], kind="bar", title="Comparaison pondérations")
plt.show()
```

# Task 13: Tester la détection avec données simulées

## Objectif
Tester le système FireDetector avec des scénarios simulés pour évaluer ses performances avant d’utiliser des capteurs réels.

## Description
- Génération de 100 scénarios simulés : 50 avec feu, 50 normaux.
- Utilisation du module `simulate_sensors.py` pour créer des données réalistes.
- Calcul des métriques :
  - **Précision** (Precision)
  - **Rappel** (Recall)
  - **F1-score**
  - Temps de traitement moyen et total

## Méthodologie
1. Charger le module `FireDetector`.
2. Générer les scénarios simulés via `generate_balanced_data()`.
3. Pour chaque scénario :
   - Prétraiter les données (`preprocess`)
   - Calculer le score de risque (`calculate_fire_risk`)
   - Détecter un incendie (`detect_fire`)
4. Comparer les résultats aux labels simulés pour calculer les métriques.

## Résultats (exemple)
| Métrique                | Valeur   |
|-------------------------|----------|
| Precision               | 1.0      |
| Recall                  | 0.98     |
| F1_score                | 0.9899   |
| Avg_processing_time_s   | 0.000002 |
| Total_processing_time_s | 0.00019  |

**Interprétation :**
- Tous les feux détectés sont corrects (aucun faux positif).
- Seulement 2 % des feux simulés n’ont pas été détectés.
- Traitement extrêmement rapide.

## Conclusion
Le FireDetector montre d’excellentes performances sur des données simulées, avec une détection précise et rapide. Prêt pour tests sur données réelles ou hardware.


# Task 14: Document Fire Detection Algorithm v1

## Objective
Create a technical document detailing the first version of the fire detection decision algorithm, including:
- Pseudocode
- Example scenarios
- Chosen thresholds and weights
- Justifications for parameter choices

## Files
- `Decision_Algorithm_v1.md` : full technical documentation.
- `README_Task14.md` : this summary file.

## Instructions
- Upload `Decision_Algorithm_v1.md` to the Notion project under documentation.
- Refer to it for understanding the decision logic and parameter settings.
- Update it in future versions (v2, v3) if thresholds or weights are adjusted.

## Notes
- v1 thresholds and weights were derived from experimental tests.
- Algorithm combines temperature, smoke, and IR sensor readings into a global score.
- Decision threshold is set to 0.5 for balanced detection.


# Task 15: Prototyper détection de tendance (montée rapide)

## Description 
Ce module implémente un algorithme de détection d’incendie basé sur :
- une analyse globale du risque (temperature, fumee, flamme IR),
- une detection de montee rapide (Rapid Rise Detection),
- des seuils parametrables,
- un systeme de score pondere,
- une gestion d'historique pour calculer les variations entre deux mesures.

## Fonctionnement de l'algorithme 
- Pretraitement
  1. Vérifie les clés nécessaires : `temperature`, `smoke`, `ir_flame`, `proximity`, `timestamp`.
  2. Remplace les valeurs manquantes par 0.

- Score global
Chaque capteur contribue a un score entre 0 et 1.

Formule:

```bash
GlobalScoreGlobalScore = 0.4 * TempScore + 0.4 * SmokeScore + 0.2 * IRScore
```
IR >= seuil ---> IRScore = 1.
Score final >= 0.5 ---> feu potentiel.

- Détection de montée rapide (Rapid Rise)
Compare les valeurs actuelles avec les dernieres valeurs recues

seuils par defaut: 
```bash
ΔTempérature ≥ 10°C
ΔFumée ≥ 200ppm
```
Si l’un des deux dépasse → alarme instantanée.

- Decision finale
L'alarme se declanche si:
  1. `global score >= alert_thresh`
  OU
  2. montee rapide detectee
Sinon: "Nothing to do"

## Tests et Resultats
### Code de test F1/Precision/Recall

```python
from sklearn.metrics import precision_score, recall_score, f1_score

y_true = [1]*50 + [0]*50
y_pred = [(1 if r["action"]=="WARNING: start alarm" else 0) for r in results]

precision = precision_score(y_true, y_pred)
recall = recall_score(y_true, y_pred)
f1 = f1_score(y_true, y_pred)

print(f"Precision: {precision:.2f}, Recall: {recall:.2f}, F1: {f1:.2f}")
```

Resultats actuels
```bash
Precision: 0.47
Recall: 0.56
F1: 0.51
```
- Interpretation 
  . Le prototype detecte plus d'un incendie sur deux (Recall).
  . Quelques faux positifs (Precision faible).
  . Correct pour un `prototype non calibre.
  . S'ameliorera avec donnees capteurs reels.
- Points forts 
  . Detection montee rapide fonctionnelle.
  . Architecture claire et modulaire.
  . Parametres facilement ajustables.
  . Basee sur ponderation (donc explicable).

- Limitations et Ameliorations prevues
  . Ajouter filtrage des signaux (moyenne glissante).
  . Calibration reelle sur ESP32.
  . Detection IR plus robuste.
  . Ajouter niveaux d'alerte (INFO / WARNING / CRITICAL)
  . Ajouter Δ/s (variation par seconde).
  . Historique multi-mesures (actuellement deux points).

## Exemple d'utilisation
```python
from aiBrain.FireDetector import FireDetector
import json

detector = FireDetector()

with open("data/simulated_fire.json") as f:
    raw = json.load(f)

data = detector.preprocess(raw)
rapid = detector.detect_rapid_rise(data)
scores = detector.calculate_fire_risk(data)

action = detector.detect_fire(scores, rapid)
detector.log_result(scores, action)
```

# Task 16: Implémentation de l'Algorithme A*

## Description
Ce module implémente l'algorithme de recherche de chemin A* (A-Star), essentiel pour la fonction de Pathfinding du robot. Il permet au robot de:

- Calculer le trajet le plus court entre sa position actuelle et la cible fournie par l'Advisor (T17).
- Éviter intelligemment les obstacles fixes ou connus sur la carte (murs, meubles, zones interdites).

## Fonctionnement de l'algorithme

L'algorithme A* est un algorithme de recherche de graphe basé sur une file de priorité (implémentée via heapq) qui garantit l'optimalité du chemin trouvé.

### Composants Clés
Chaque nœud (cellule de la grille) est évalué par trois coûts :
1. g (Coût réel) : Le coût cumulé (nombre de pas) pour aller du point de départ au nœud actuel.
2. h (Heuristique) : Le coût estimé pour aller du nœud actuel au point d'arrivée (utilisant la Distance de Manhattan dans cette implémentation).
3. f (Coût total) : f = g + h. Le nœud avec le plus petit $f$ est exploré en priorité.

### Entrée et Sortie
- Entrée `(maze)` : Une carte 2D (liste de listes) où `0` représente un espace libre (carrossable) et `1` représente un obstacle.
- Entrée (start, end) : Tuples (ligne, colonne) pour le début et la fin.
- Sortie : Une liste ordonnée de tuples (ligne, colonne) représentant le chemin optimal.

## Détails Techniques et Code

### Heuristique
L'heuristique utilisée est la Distance de Manhattan, qui est adaptée aux mouvements horizontaux et verticaux (4 directions) sur la grille.
 $$\mathbf{h} = |\mathbf{x_{current}} - \mathbf{x_{end}}| + |\mathbf{y_{current}} - \mathbf{y_{end}}|$$

## Tests et Résultats

```python
map_grid = [
    [0, 0, 0, 0, 0],
    [0, 1, 1, 1, 0], # Murs
    [0, 0, 0, 0, 0],
    [0, 1, 0, 1, 0], # Murs
    [0, 0, 0, 0, 0]
]
start_pos = (4, 0) # Bas gauche
end_pos = (0, 4)   # Haut droite
```
### Résultat Actuel
L'algorithme réussit à naviguer autour des obstacles et à trouver le chemin le plus court.

```bash
Chemin trouvé (lignes, colonnes) :
-> (4, 0) -> (3, 0) -> (2, 0) -> (2, 1) -> (2, 2) -> (2, 3) -> (1, 4) -> (0, 4)

Visualisation du chemin (X = Robot, 1 = Obstacle) :
X 0 0 0 X
0 1 1 1 X
X X X X 0
0 1 0 1 0
0 0 0 0 X
```

### Interprétation
- Validé : L'algorithme A* fonctionne et trouve un chemin optimal en évitant les cellules 1.
- Efficacité : L'utilisation de heapq garantit une performance rapide, essentielle pour la faible latence requise en robotique.

## Exemple d'utilisation

```python
from aiBrain.pathfinding_a_star import a_star
# ... Définition de map_grid ...

start_pos = (4, 0) 
end_pos = (0, 4) 

path = a_star(map_grid, start_pos, end_pos)

if path:
    print(f"Le premier pas est : {path[1]}") # Le robot passe de (4,0) à (3,0)
```

# Task 17: Développement du "Simulator Advisor"

## Description

Ce module simule l'intelligence côté serveur qui guide le robot YBOOST pendant sa phase de patrouille (PATROL dans la Tâche 19). Le service analyse les données historiques et les zones de la carte pour recommander une cible d'inspection.

L'objectif est de s'assurer que le robot explore l'environnement de manière intelligente plutôt que de suivre un chemin aléatoire ou prédéfini.

## Fonctionnement de l'algorithme : Heuristiques de Priorité

Chaque zone de la carte reçoit un Score de Priorité basé sur deux heuristiques principales :

1. Urgence Temporelle (Poids 60%) : Plus le temps écoulé depuis la dernière inspection de la zone est important, plus la zone est prioritaire. Cela garantit une couverture complète de l'environnement.

2. Risque Historique (Poids 40%) : Les zones où les capteurs ont historiquement signalé des pics (score de risque élevé) reçoivent un bonus de priorité, les rendant plus susceptibles d'être visitées en premier.

$$\mathbf{Score_{Priorité}} = (0.6 \times \mathbf{Score_{Temps}}) + (0.4 \times \mathbf{Score_{Risque}})$$

Critère de Décision (Tie-breaker) : Si deux zones ont le même score de priorité élevé, l'Advisor choisit celle qui est la plus proche de la position actuelle du robot (utilisant la Distance de Manhattan).

## Entrée et Sortie

- Entrée : Position actuelle du robot (row, col), état de l'historique de toutes les zones (temps de la dernière visite, score de risque moyen).

- Sortie : Coordonnées (row, col) de la zone recommandée par l'Advisor. (Ces coordonnées sont l'entrée de l'algorithme A* de la Tâche 16).

## Exemple d'Utilisation

```python
from aiBrain.advisor_service import AdvisorService

advisor = AdvisorService()
current_pos = (4, 0) # Robot en C1

# L'Advisor calcule et envoie la cible
target, zone = advisor.get_next_inspection_target(current_pos)

print(f"L'Advisor recommande au robot de se rendre à {target} (Zone {zone})")
# Ces coordonnées sont ensuite utilisées par le module T16 pour calculer le chemin.

# Simulation de l'inspection (mis à jour par T19)
advisor.update_zone_data(zone, 0.1)
```

