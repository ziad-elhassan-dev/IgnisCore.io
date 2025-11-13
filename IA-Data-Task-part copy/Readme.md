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

