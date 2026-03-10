# main.py

from fire_detection.FireDetector import FireDetector
from fire_detection.simulate_sensors import save_to_json, generate_balanced_data
from navigation.advisor_service import AdvisorService
from robot.robot_controller import RobotController

def main():
    # 1. Generate test data (optional — useful for standalone testing)
    data = generate_balanced_data(n_fire=50, n_normal=50)
    save_to_json(data, "test_data_100.json")

    # 2. Create FireDetector with tuned thresholds
    detector = FireDetector(
        temp_thresh=50,
        smoke_thresh=300,
        ir_thresh=1,
        weight_temp=0.4,
        weight_smoke=0.4,
        weight_ir=0.2,
        alert_thresh=0.5,
        temp_delta_thresh=10,
        smoke_delta_thresh=200
    )

    # 3. Create AdvisorService (zone patrol intelligence)
    advisor = AdvisorService()

    # 4. Create and run the RobotController FSM
    # Robot starts at bottom-left of the grid (row 4, col 0)
    robot = RobotController(detector=detector, advisor=advisor, initial_pos=(4, 0))
    robot.run(max_steps=100)


if __name__ == "__main__":
    main()