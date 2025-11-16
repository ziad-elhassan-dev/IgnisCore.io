import numpy as np
import matplotlib.pyplot as plt

data = [50,52,53,55,54]
weights = [0.5, 0.3, 0.2] # poids pour les 3 dernières mesures
wma =[]

for i in range(len(data)):
    if i < len(weights):
        wma.append(np.average(data[:i+1], weights=weights[-(i+1):]))
    else:
        wma.append(np.average(data[i-2:i+1], weights = weights))
        
plt.plot(data, label='Raw measurements', marker='o')
plt.plot(wma, label='Weighted Moving Average', marker='x')
plt.xlabel('Time step')
plt.ylabel('Temperature')
plt.title('Weighted Moving Average Example')
plt.legend()
plt.show()