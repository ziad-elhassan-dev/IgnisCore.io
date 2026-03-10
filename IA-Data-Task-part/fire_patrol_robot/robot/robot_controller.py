# robot_controller.py

import time
from fire_detection.FireDetector import FireDetector
from navigation.advisor_service import AdvisorService, ZONE_CENTERS
from navigation.pathfinding_a_star import a_star


# ─────────────────────────────────────────
# MAP — same 5x9 grid used in pathfinding
# 0 = free, 1 = obstacle
# ─────────────────────────────────────────
MAP_GRID = [
    [0, 0, 0, 0, 0, 0, 1, 0, 0],
    [0, 1, 1, 1, 0, 0, 1, 0, 1],
    [0, 1, 0, 0, 0, 0, 0, 0, 1],
    [0, 1, 0, 1, 1, 0, 1, 0, 0],
    [0, 0, 0, 0, 1, 0, 1, 0, 1]
]


# ─────────────────────────────────────────
# FSM STATES
# ─────────────────────────────────────────
class RobotState:
    IDLE       = "IDLE"        # Waiting for first instruction
    PATROL     = "PATROL"      # Moving along path to target zone
    SUSPICION  = "SUSPICION"   # Sensor triggered — stopping to re-read
    CONFIRM    = "CONFIRM"     # Deep analysis: multiple reads + rapid-rise check
    EXTINGUISH = "EXTINGUISH"  # Fire confirmed — activate pump
    REPORT     = "REPORT"      # Incident logged — return to patrol


# ─────────────────────────────────────────
# SIMULATION HELPERS
# ─────────────────────────────────────────
def simulate_mqtt_publish(topic, payload):
    """Simulate sending a command over MQTT."""
    print(f"  [MQTT] >> Topic: '{topic}' | Payload: {payload}")


def simulate_ml_confirmation(risk_score, confidence_level=0.85):
    """
    Simulate a secondary ML model confirmation.
    Returns (confirmed: bool, severity: str)
    """
    if risk_score >= confidence_level:
        return True, "CRITICAL"
    elif risk_score >= 0.6:
        return True, "MODERATE"
    return False, "LOW"


def simulate_read_sensors(pos, fire_event=False):
    """
    Simulate reading sensors at a given grid position.
    fire_event=True means a fire was already detected here — readings stay hot.
    In a real robot this would call the actual sensor API.
    Returns a raw sensor dict.
    """
    import random
    from datetime import datetime

    # If fire already detected at this position, 75% chance readings stay hot
    # Otherwise normal patrol: 20% chance of fire-like conditions
    fire_chance = 0.75 if fire_event else 0.20
    is_fire = random.random() < fire_chance

    if is_fire:
        return {
            "timestamp": datetime.now().isoformat(),
            "temperature": random.uniform(65, 120),
            "smoke": random.uniform(420, 1800),
            "ir_flame": random.choice([0, 1]),
            "proximity": random.uniform(10, 80)
        }
    else:
        return {
            "timestamp": datetime.now().isoformat(),
            "temperature": random.uniform(20, 45),
            "smoke": random.uniform(50, 250),
            "ir_flame": 0,
            "proximity": random.uniform(50, 200)
        }


# ─────────────────────────────────────────
# ROBOT CONTROLLER (FSM)
# ─────────────────────────────────────────
class RobotController:
    """
    Finite State Machine (FSM) that drives the robot's decision-making.
    Integrates: FireDetector, AdvisorService, A* pathfinding.
    """

    def __init__(self, detector: FireDetector, advisor: AdvisorService, initial_pos=(4, 0)):
        self.detector = detector
        self.advisor = advisor

        self.current_state = RobotState.IDLE
        self.current_pos = initial_pos       # (row, col) on MAP_GRID
        self.current_path = []               # List of (row, col) steps
        self.destination_pos = None          # Target (row, col)
        self.destination_zone = None         # Zone ID e.g. "A3"

        self.suspicion_readings = []         # Buffer for CONFIRM state
        self.incident_log = []               # History of all fire events

    # ── State transitions ──────────────────
    def set_state(self, new_state):
        print(f"\n  [FSM] {self.current_state} --> {new_state}")
        self.current_state = new_state

    # ── IDLE ───────────────────────────────
    def handle_idle(self):
        """Ask the advisor for the first patrol target and start moving."""
        print("[IDLE] Robot en attente. Demande d'une cible au serveur...")
        target_pos, zone_id = self.advisor.get_next_inspection_target(self.current_pos)

        if target_pos is None:
            print("[IDLE] Aucune cible disponible. Attente...")
            time.sleep(1)
            return

        self._plan_path_to(target_pos, zone_id)
        self.set_state(RobotState.PATROL)

    # ── PATROL ─────────────────────────────
    def handle_patrol(self):
        """
        Move one step along the planned path.
        At each step, read sensors.
        If sensors trigger, switch to SUSPICION.
        If destination reached, read sensors then get new target.
        """
        if not self.current_path:
            # Destination reached
            print(f"[PATROL] Destination {self.destination_zone} atteinte en {self.current_pos}.")
            sensor_data = simulate_read_sensors(self.current_pos)
            preprocessed = self.detector.preprocess(sensor_data)
            scores = self.detector.calculate_fire_risk(preprocessed)
            action = self.detector.detect_fire(scores)

            print(f"  [PATROL] Lecture arrivée → score global: {scores['global']:.2f} | action: {action}")

            # Update advisor with this zone's risk score
            self.advisor.update_zone_data(self.destination_zone, scores["global"])

            if action == "WARNING: start alarm":
                self.suspicion_readings = [scores]
                self.set_state(RobotState.SUSPICION)
            else:
                # Get next target
                target_pos, zone_id = self.advisor.get_next_inspection_target(self.current_pos)
                if target_pos:
                    self._plan_path_to(target_pos, zone_id)
                else:
                    print("[PATROL] Aucune nouvelle cible. Retour en IDLE.")
                    self.set_state(RobotState.IDLE)
            return

        # Move one step
        next_pos = self.current_path.pop(0)
        print(f"[PATROL] Déplacement: {self.current_pos} -> {next_pos}  "
              f"(reste {len(self.current_path)} pas)")
        self.current_pos = next_pos

        # Read sensors mid-path
        sensor_data = simulate_read_sensors(self.current_pos)
        preprocessed = self.detector.preprocess(sensor_data)
        scores = self.detector.calculate_fire_risk(preprocessed)
        rapid_rise = self.detector.detect_rapid_rise(sensor_data)
        action = self.detector.detect_fire(scores, rapid_rise=rapid_rise)

        if action == "WARNING: start alarm":
            print(f"  [PATROL] ⚠️  Anomalie détectée! Score: {scores['global']:.2f}")
            self.suspicion_readings = [scores]
            self.set_state(RobotState.SUSPICION)

        time.sleep(0.05)  # Simulate movement time

    # ── SUSPICION ──────────────────────────
    def handle_suspicion(self):
        print("[SUSPICION] Robot arrêté. Lectures de vérification en cours...")
        confirm_count = 0
        total_reads = 3

        for i in range(total_reads):
            time.sleep(0.1)
            sensor_data = simulate_read_sensors(self.current_pos, fire_event=True)  # ← fire_event=True
            preprocessed = self.detector.preprocess(sensor_data)
            scores = self.detector.calculate_fire_risk(preprocessed)
            rapid_rise = self.detector.detect_rapid_rise(sensor_data)
            action = self.detector.detect_fire(scores, rapid_rise=rapid_rise)

            self.suspicion_readings.append(scores)
            print(f"  [SUSPICION] Lecture {i+1}/{total_reads}: global={scores['global']:.2f} | {action}")

            if action == "WARNING: start alarm":
                confirm_count += 1

        if confirm_count >= 2:
            print(f"  [SUSPICION] ⚠️  {confirm_count}/{total_reads} lectures positives → CONFIRM")
            self.set_state(RobotState.CONFIRM)
        else:
            print(f"  [SUSPICION] ✅ {confirm_count}/{total_reads} lectures positives → Fausse alarme. Retour PATROL.")
            self.set_state(RobotState.PATROL)

    # ── CONFIRM ────────────────────────────
    def handle_confirm(self):
        """
        Deep analysis: compute average risk from suspicion readings,
        then apply ML confirmation model.
        If confirmed → EXTINGUISH. Otherwise → PATROL.
        """
        print("[CONFIRM] Analyse approfondie en cours...")

        avg_global = sum(s["global"] for s in self.suspicion_readings) / len(self.suspicion_readings)
        avg_temp   = sum(s["temp"]   for s in self.suspicion_readings) / len(self.suspicion_readings)
        avg_smoke  = sum(s["smoke"]  for s in self.suspicion_readings) / len(self.suspicion_readings)

        print(f"  [CONFIRM] Scores moyens → global: {avg_global:.2f} | temp: {avg_temp:.2f} | smoke: {avg_smoke:.2f}")

        is_fire, severity = simulate_ml_confirmation(avg_global)

        if is_fire:
            print(f"  [CONFIRM] 🔥 Incendie CONFIRMÉ. Sévérité: {severity}")
            simulate_mqtt_publish("robot/alert", {
                "type": "FIRE_CONFIRMED",
                "severity": severity,
                "position": self.current_pos,
                "avg_score": round(avg_global, 3)
            })
            self.set_state(RobotState.EXTINGUISH)
        else:
            print(f"  [CONFIRM] ✅ Pas d'incendie confirmé (score moyen trop bas). Retour PATROL.")
            simulate_mqtt_publish("robot/alert", {
                "type": "FALSE_ALARM",
                "position": self.current_pos,
                "avg_score": round(avg_global, 3)
            })
            self.set_state(RobotState.PATROL)

    # ── EXTINGUISH ─────────────────────────
    def handle_extinguish(self):
        """
        Activate the pump. Simulate extinguishing for a few seconds.
        Then switch to REPORT.
        """
        print("[EXTINGUISH] 💧 Activation de la pompe...")
        simulate_mqtt_publish("robot/pump", {"command": "START", "position": self.current_pos})

        # Simulate pump running
        for i in range(3):
            time.sleep(0.3)
            print(f"  [EXTINGUISH] Pompe active... ({i+1}/3)")

        simulate_mqtt_publish("robot/pump", {"command": "STOP", "position": self.current_pos})
        print("[EXTINGUISH] ✅ Pompe arrêtée.")
        self.set_state(RobotState.REPORT)

    # ── REPORT ─────────────────────────────
    def handle_report(self):
        """
        Log the incident. Notify control center via MQTT. Resume patrol.
        """
        incident = {
            "timestamp": __import__("datetime").datetime.now().isoformat(),
            "position": self.current_pos,
            "zone": self._get_zone_from_pos(self.current_pos),
            "readings": len(self.suspicion_readings),
            "avg_score": round(
                sum(s["global"] for s in self.suspicion_readings) / len(self.suspicion_readings), 3
            )
        }
        self.incident_log.append(incident)
        print(f"[REPORT] 📋 Incident enregistré: {incident}")
        simulate_mqtt_publish("robot/report", incident)

        # Update advisor: this zone just had a fire, high risk score
        if self.destination_zone:
            self.advisor.update_zone_data(self.destination_zone, incident["avg_score"])

        # Clear suspicion buffer
        self.suspicion_readings = []
        self.set_state(RobotState.PATROL)
        
    def _get_zone_from_pos(self, pos):
        """Find the closest zone to the current position."""
        closest_zone = None
        min_dist = float("inf")
        for zone_id, center in ZONE_CENTERS.items():
            dist = abs(pos[0] - center[0]) + abs(pos[1] - center[1])
            if dist < min_dist:
                min_dist = dist
                closest_zone = zone_id
        return closest_zone

    # ── PATH PLANNING ──────────────────────
    def _plan_path_to(self, target_pos, zone_id):
        """Compute A* path to target and store it."""
        path = a_star(MAP_GRID, self.current_pos, target_pos)
        if path:
            self.current_path = path[1:]  # Exclude current position
            self.destination_pos = target_pos
            self.destination_zone = zone_id
            print(f"  [PATH] Route vers {zone_id} {target_pos}: {len(self.current_path)} pas.")
        else:
            print(f"  [PATH] ⚠️  Aucun chemin trouvé vers {zone_id} {target_pos}!")
            self.current_path = []
            self.destination_pos = None
            self.destination_zone = None

    # ── MAIN LOOP ──────────────────────────
    def step(self):
        """Execute one FSM step based on current state."""
        if self.current_state == RobotState.IDLE:
            self.handle_idle()
        elif self.current_state == RobotState.PATROL:
            self.handle_patrol()
        elif self.current_state == RobotState.SUSPICION:
            self.handle_suspicion()
        elif self.current_state == RobotState.CONFIRM:
            self.handle_confirm()
        elif self.current_state == RobotState.EXTINGUISH:
            self.handle_extinguish()
        elif self.current_state == RobotState.REPORT:
            self.handle_report()

    def run(self, max_steps=200):
        """
        Main loop. Runs the FSM for up to max_steps iterations.
        In a real robot this would be infinite (while True).
        """
        print("=" * 55)
        print("  🤖  ROBOT FIRE PATROL — DÉMARRAGE")
        print("=" * 55)

        for step_num in range(max_steps):
            print(f"\n--- Step {step_num + 1} | State: {self.current_state} | Pos: {self.current_pos} ---")
            self.step()

        print("\n" + "=" * 55)
        print(f"  Simulation terminée après {max_steps} steps.")
        print(f"  Incidents enregistrés: {len(self.incident_log)}")
        for inc in self.incident_log:
            print(f"    - Zone {inc['zone']} | Score: {inc['avg_score']} | {inc['timestamp']}")
        print("=" * 55)