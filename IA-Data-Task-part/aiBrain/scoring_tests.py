from FireDetector import FireDetector
from simulate_sensors import generate_sensor_data
import pandas as pd
import matplotlib.pyplot as plt

# Générer données de test
data = generate_sensor_data(50)

# Pondérations à tester
configs = {
    "A_0.3_0.7": (0.3, 0.7),
    "B_0.4_0.6": (0.4, 0.6),
    "C_0.5_0.5": (0.5, 0.5),
}

results = []

for name, (w_temp, w_smoke) in configs.items():
    detector = FireDetector(
        weight_temp=w_temp,
        weight_smoke=w_smoke,
        weight_ir=0
    )

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

# DataFrame
df = pd.DataFrame(results)
print(df)

#  Visualisation
df.plot(x="config", y=["fires_detected", "avg_score"], kind="bar", title="Comparaison pondérations")
plt.show()
