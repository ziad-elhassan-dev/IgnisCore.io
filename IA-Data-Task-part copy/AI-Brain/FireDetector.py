import json
from datetime import datetime

class FireDetector:
    def __init__(self, temp_thresh=50, smoke_thresh=300, ir_thresh=1, weight_temp=0.4, weight_smoke=0.4, weight_ir=0.2, alert_thresh=0.5):
        #Seuils capteurs
        self.temp_thresh = temp_thresh
        self.smoke_thresh = smoke_thresh
        self.ir_thresh = ir_thresh
        
        #Poids pour le score global
        self.weight_temp = weight_temp
        self.weight_smoke = weight_smoke
        self.weight_ir = weight_ir
        
        #Global alert to start action
        self.alert_thresh = alert_thresh
        
    def read_data(self, file_path):
        "To read a json file with sensor data"
        with open(file_path, "r") as f:
            return json.load
        
    def preprocess(self, sensor_data):
        "Normalisation or sorting if necessary"
        return sensor_data
    
    def calculate_fire_risk(self, sensor_data):
        "Calculates a score from sensor data"
        def score(value, threshold):
            return min(max((value-threshold)/threshold, 0), 1)
        
        temp_score = score(sensor_data['temperature'], self.temp_thresh)
        smoke_score = score(sensor_data['smoke'], self.smoke_thresh)
        ir_score = 1 if sensor_data['ir_flame'] >= self.ir_thresh else 0
        
        global_score = (temp_score * self.weight_temp) + (smoke_score * self.weight_smoke) + (ir_score * self.weight_ir)
        
        return {"temp" : temp_score, "smoke" : smoke_score, "ir": ir_score, "global" : global_score}
    
    def detect_fire(self, scores):
        #decides action based on global score
        if scores["global"] >= self.alert_thresh:
            return "WARNING: start alarm"
        else:
            return "Nothing to do"
        
    def log_result(self, scores, action):
        print(f"Scores: {scores}")
        print(f"Action: {action}")
        
    
 #Example
if __name__ == "__main__":
    detector = FireDetector()
    
    data = {
        "timestamp": datetime.now().isoformat(),
        "temperature": 55,
        "smoke": 350,
        "ir_flame": 1,
        "humidity": 40.5
    }
    
    preprocessed = detector.preprocess(data)
    scores = detector.calculate_fire_risk(preprocessed)
    action = detector.detect_fire(scores)
    detector.log_result(scores, action)       
    
