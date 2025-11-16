import matplotlib.pyplot as plt

data = [50, 52, 53, 55, 54]
alpha = 0.3
smoothed = [data[0]]  # première valeur

for i in range(1, len(data)):
    smoothed.append(alpha * data[i] + (1 - alpha) * smoothed[-1])
    
plt.plot(data, label='Raw measurements', marker='o')
plt.plot(smoothed, label='Exponential Smoothing', marker='x')
plt.xlabel('Time step')
plt.ylabel('Temperature')
plt.title('Exponential Smoothing Example')
plt.legend()
plt.show()