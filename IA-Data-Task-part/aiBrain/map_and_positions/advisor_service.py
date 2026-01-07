# Fichier : advisor_service.py

import time
import random

# --- Définitions de la carte (Basées sur la grille 5x5 de la Tâche 16) ---

# Définition simple des zones de la carte et leurs coordonnées centrales
# Ces coordonnées (tuples) correspondent aux cibles pour l'algorithme A* (T16).
# Format: {ID_ZONE: (ROW, COL), ...}
ZONE_CENTERS = {
    "A1": (0, 0), "A2": (0, 2), "A3": (0, 4), # Haut de la grille
    "B1": (2, 0), "B2": (2, 2), "B3": (2, 4), # Milieu de la grille
    "C1": (4, 0), "C2": (4, 2), "C3": (4, 4)  # Bas de la grille
}
ALL_ZONE_IDS = list(ZONE_CENTERS.keys())


class AdvisorService:
    """
    Simule l'IA côté serveur qui conseille le robot sur sa prochaine destination (T17).
    Gère l'historique des inspections et calcule la priorité de la prochaine cible.
    """
    def __init__(self):
        # Simulation d'une base de données ou de l'état de la carte
        self.zone_data = {
            zone_id: {
                "last_inspected": time.time(), # Timestamp de la dernière visite
                "avg_risk_score": 0.0,        # Score de risque moyen historique
                "unvisited_count": 1          # Initialiser à 1 pour prioriser la première visite
            }
            for zone_id in ALL_ZONE_IDS
        }
        
        # Simuler un scénario initial pour le test :
        # A3 est historiquement risquée. C1 n'a pas été inspectée depuis longtemps.
        self.zone_data["A3"]["avg_risk_score"] = 0.7 
        self.zone_data["C1"]["last_inspected"] = time.time() - 3600 * 5 # Dernière visite il y a 5h

    def update_zone_data(self, zone_id, risk_score):
        """Met à jour l'état d'une zone après l'inspection du robot (utilisé par T19)."""
        if zone_id in self.zone_data:
            data = self.zone_data[zone_id]
            data["last_inspected"] = time.time()
            data["unvisited_count"] = 0
            
            # Mise à jour du score moyen : moyenne pondérée pour ne pas écraser l'historique
            old_score = data["avg_risk_score"]
            data["avg_risk_score"] = (old_score * 0.8) + (risk_score * 0.2)
            
            print(f"[Advisor] Zone {zone_id} inspectée. Nouveau Risque moyen: {data['avg_risk_score']:.2f}")

    def calculate_priority_score(self, zone_id):
        """
        Calcule un score de priorité basé sur les heuristiques définies.
        Plus le score est élevé, plus la zone est urgente à visiter.
        """
        data = self.zone_data[zone_id]
        
        # Heuristique 1: Urgence temporelle (poids 0.6)
        # 3600 secondes = 1 heure. Plus le temps écoulé est grand, plus le score est élevé.
        time_elapsed = time.time() - data["last_inspected"]
        # Normalisation (ici, on donne une valeur arbitraire maximale de 5h = 1.0 pour le temps)
        time_score = min(time_elapsed / (3600 * 5), 1.0) * 0.6
        
        # Heuristique 2: Risque historique (poids 0.4)
        risk_score = data["avg_risk_score"] * 0.4
        
        # Score total
        priority = time_score + risk_score
        
        # Bonus pour les zones jamais vues
        if data["unvisited_count"] > 0:
             priority += 0.5 # Bonus pour forcer l'exploration initiale
             
        return priority

    def get_next_inspection_target(self, current_robot_pos):
        """
        Détermine la zone à inspecter avec la plus haute priorité.
        """
        best_zone = None
        max_priority = -1.0
        
        for zone_id in ALL_ZONE_IDS:
            priority = self.calculate_priority_score(zone_id)
            
            # 1. Sélection de la zone ayant la priorité maximale
            if priority > max_priority:
                max_priority = priority
                best_zone = zone_id
            
            # 2. Gestion de l'égalité (Tie-breaker): Choisir la zone la plus proche
            elif priority == max_priority and best_zone is not None:
                current_target_pos = ZONE_CENTERS[best_zone]
                new_target_pos = ZONE_CENTERS[zone_id]
                
                # Critère de proximité : Distance de Manhattan
                dist_current = abs(current_robot_pos[0] - current_target_pos[0]) + abs(current_robot_pos[1] - current_target_pos[1])
                dist_new = abs(current_robot_pos[0] - new_target_pos[0]) + abs(current_robot_pos[1] - new_target_pos[1])
                
                if dist_new < dist_current:
                    best_zone = zone_id
                    
        if best_zone:
            target_coords = ZONE_CENTERS[best_zone]
            print(f"[Advisor] Zone recommandée: {best_zone} (Priorité: {max_priority:.2f}). Coords: {target_coords}")
            return target_coords, best_zone
        
        return None, None 


# --- Exemple d'utilisation (pour tester le module) ---
if __name__ == "__main__":
    advisor = AdvisorService()
    current_pos = (4, 4) # Départ en bas à droite (Zone C3)
    
    print("--- Démarrage de l'Advisor (T17) ---")
    
    # 1. Première recommandation : C1 (temps écoulé) ou A3 (risque historique)
    target_1, zone_1 = advisor.get_next_inspection_target(current_pos)
    print(f"1. Robot à {current_pos}. Cible: {target_1} ({zone_1})")
    
    # 2. Le robot se déplace et inspecte la zone (simulons A3, avec un risque faible)
    current_pos = ZONE_CENTERS["A3"]
    advisor.update_zone_data("A3", 0.05) 
    
    # 3. Deuxième recommandation : le risque de A3 est descendu. C1 devrait maintenant gagner
    target_2, zone_2 = advisor.get_next_inspection_target(current_pos)
    print(f"\n2. Robot à {current_pos}. Cible: {target_2} ({zone_2})")
    
    # 4. Inspection de C1
    current_pos = ZONE_CENTERS["C1"]
    advisor.update_zone_data("C1", 0.0)
    
    # 5. Troisième recommandation : la zone la moins visitée ou la plus ancienne (par défaut)
    print("\n[Simu] Toutes les zones ont été visitées récemment...")
    target_3, zone_3 = advisor.get_next_inspection_target(current_pos)
    print(f"3. Robot à {current_pos}. Cible: {target_3} ({zone_3})")