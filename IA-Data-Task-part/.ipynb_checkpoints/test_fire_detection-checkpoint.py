import json
import time
import matplotlib.pyplot as plt # type: ignore
import pandas as pd # type: ignore
from aiBrain.fire_detection.FireDetector import FireDetector
from aiBrain.fire_detection.simulate_sensors import generate_balanced_data, save_to_json
from sklearn.metrics import precision_score, recall_score, f1_score # type: ignore

# -------------------------------
# 1. Générer et sauvegarder les données simulées
# -------------------------------
data = generate_balanced_data(n_fire=50, n_normal=50)
save_to_json(data, "test_data_100.json")

# -------------------------------
# 2. Créer le détecteur
# -------------------------------
detector = FireDetector(temp_thresh=50, smoke_thresh=300, ir_thresh=1, weight_temp=0.4, weight_smoke=0.4, weight_ir=0.2, alert_thresh=0.5)

# -------------------------------
# 3. Tester la détection
# -------------------------------
true_labels = []   # 1 = feu, 0 = normal
pred_labels = []   # 1 = alarme déclenchée, 0 = rien
processing_times = []

for entry in data:
    true_label = 1 if entry["temperature"] >= 60 or entry["smoke"] >= 400 or entry["ir_flame"] == 1 else 0
    true_labels.append(true_label)
    
    start = time.time()
    pre = detector.preprocess(entry)
    scores = detector.calculate_fire_risk(pre)
    action = detector.detect_fire(scores)
    end = time.time()
    
    pred_label = 1 if action == "WARNING: start alarm" else 0
    pred_labels.append(pred_label)
    processing_times.append(end - start)

# -------------------------------
# 4. Calculer les métriques
# -------------------------------
precision = precision_score(true_labels, pred_labels)
recall = recall_score(true_labels, pred_labels)
f1 = f1_score(true_labels, pred_labels)
avg_time = sum(processing_times)/len(processing_times)
total_time = sum(processing_times)

# -------------------------------
# 5. Afficher les résultats
# -------------------------------
df_results = pd.DataFrame({
    "Precision": [precision],
    "Recall": [recall],
    "F1_score": [f1],
    "Avg_processing_time_s": [avg_time],
    "Total_processing_time_s": [total_time]
})

print(df_results)

# -------------------------------
# 6. Optionnel: visualisation
# -------------------------------

plt.bar(["Precision","Recall","F1"], [precision, recall, f1])
plt.title("Performance FireDetector")
plt.ylim(0,1)
plt.show()

plt.plot(processing_times, marker="o")
plt.title("Temps de traitement par scénario")
plt.xlabel("Scénario")
plt.ylabel("Temps (s)")
plt.show()
