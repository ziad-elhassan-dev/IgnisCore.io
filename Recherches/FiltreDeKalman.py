from filterpy.kalman import KalmanFilter # type: ignore
import numpy as np # type: ignore
import matplotlib.pyplot as plt # type: ignore

kf = KalmanFilter(dim_x=1, dim_z=1)
kf.x = np.array([[0.]]) #etat inital
kf.P *= 1000. #incertitude inituale
kf.F = np.array([[1.]]) # matrice de transition
kf.H = np.array([[1.]]) #m atrice observation
kf.R = 5 # variance du bruit mesure
kf.Q = 0.01 # variance du processus

measurements = [50, 52, 53, 55, 54]
filtered = []

for z in measurements:
    kf.predict()
    kf.update(z)
    filtered.append(kf.x[0])

print("Filtered values:")
for f in filtered:
    print(f[0])   # kf.x is a 2D array, so take the first element

plt.plot(measurements, label='Raw measurements', marker='o')
plt.plot([f[0] for f in filtered], label='Kalman Filtered', marker='x')
plt.xlabel("Time step")
plt.ylabel("Temperature")
plt.title("Kalman Filter Example")
plt.legend()
plt.show()