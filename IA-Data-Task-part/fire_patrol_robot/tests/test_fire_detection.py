# test_fire_detection.py

import time
import matplotlib.pyplot as plt
import pandas as pd
from fire_detection.FireDetector import FireDetector
from fire_detection.simulate_sensors import generate_balanced_data, save_to_json
from sklearn.metrics import precision_score, recall_score, f1_score

# 1. Generate and save simulated data
data = generate_balanced_data(n_fire=50, n_normal=50)
save_to_json(data, "test_data_100.json")

# 2. Create detector
detector = FireDetector(
    temp_thresh=50, smoke_thresh=300, ir_thresh=1,
    weight_temp=0.4, weight_smoke=0.4, weight_ir=0.2,
    alert_thresh=0.5
)

# 3. Run detection on all entries
true_labels = []
pred_labels = []
processing_times = []

for entry in data:
    true_label = 1 if (entry["temperature"] >= 60 or entry["smoke"] >= 400 or entry["ir_flame"] == 1) else 0
    true_labels.append(true_label)

    start = time.time()
    pre = detector.preprocess(entry)
    scores = detector.calculate_fire_risk(pre)
    action = detector.detect_fire(scores)
    end = time.time()

    pred_label = 1 if action == "WARNING: start alarm" else 0
    pred_labels.append(pred_label)
    processing_times.append(end - start)

# 4. Compute metrics
precision = precision_score(true_labels, pred_labels)
recall = recall_score(true_labels, pred_labels)
f1 = f1_score(true_labels, pred_labels)
avg_time = sum(processing_times) / len(processing_times)
total_time = sum(processing_times)

df_results = pd.DataFrame({
    "Precision": [precision],
    "Recall": [recall],
    "F1_score": [f1],
    "Avg_processing_time_s": [avg_time],
    "Total_processing_time_s": [total_time]
})

print(df_results)

# 5. Visualisation
plt.bar(["Precision", "Recall", "F1"], [precision, recall, f1])
plt.title("Performance FireDetector")
plt.ylim(0, 1)
plt.show()

plt.plot(processing_times, marker="o")
plt.title("Temps de traitement par scénario")
plt.xlabel("Scénario")
plt.ylabel("Temps (s)")
plt.show()