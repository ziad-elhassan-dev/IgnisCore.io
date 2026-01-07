# Fichier : pathfinding_a_star.py

import heapq
import random

class Node:
    """ Représente une cellule sur la grille pour l'algorithme A*. """
    def __init__(self, parent=None, position=None):
        self.parent = parent
        self.position = position # (row, col)

        self.g = 0  # Coût du départ à ce nœud
        self.h = 0  # Coût heuristique estimé à la fin
        self.f = 0  # Coût total (g + h)

    def __eq__(self, other):
        """ Pour vérifier l'égalité de deux nœuds par leur position. """
        return self.position == other.position

    def __lt__(self, other):
        """ Pour utiliser le nœud dans un tas (heapq) basé sur le coût f. """
        return self.f < other.f

def a_star(maze, start, end):
    """
    Algorithme A* optimisé pour trouver le chemin le plus court.
    Utilise un dictionnaire (open_set) en plus du tas (open_list)
    pour garantir une complexité temporelle proche de O(|V| log |V|).
    """
    start_node = Node(None, start)
    end_node = Node(None, end)
    
    # 1. Structures de données optimisées:
    open_list = []      # Tas binaire pour la priorité O(log k)
    open_set = {start: start_node} # Dictionnaire pour la vérification rapide O(1)
    closed_list = set() # Ensemble pour la vérification rapide O(1)

    heapq.heappush(open_list, start_node)

    rows, cols = len(maze), len(maze[0])
    move_directions = [(0, -1), (0, 1), (-1, 0), (1, 0)]

    while open_list:
        current_node = heapq.heappop(open_list)
        
        # S'assurer que le nœud n'est pas un duplicata obsolète (causé par la réinsertion)
        if current_node.position not in open_set or current_node != open_set[current_node.position]:
            # Ceci est un nœud obsolète avec un F plus élevé que celui dans open_set. On l'ignore.
            continue
            
        del open_set[current_node.position] # Suppression rapide du dictionnaire O(1)
        closed_list.add(current_node.position)

        if current_node == end_node:
            path = []
            current = current_node
            while current is not None:
                path.append(current.position)
                current = current.parent
            return path[::-1]

        for direction in move_directions:
            node_position = (current_node.position[0] + direction[0], 
                             current_node.position[1] + direction[1])

            if not (0 <= node_position[0] < rows and 0 <= node_position[1] < cols): continue
            if maze[node_position[0]][node_position[1]] != 0: continue
            if node_position in closed_list: continue

            # Calcul du coût G (distance réelle) pour le voisin
            tentative_g = current_node.g + 1

            # 2. Vérification rapide en O(1)
            if node_position in open_set:
                neighbor_node = open_set[node_position]
                if tentative_g >= neighbor_node.g:
                    continue # Le chemin existant est meilleur
            
                # Mise à jour: On a trouvé un meilleur chemin
                neighbor_node.parent = current_node
                neighbor_node.g = tentative_g
                neighbor_node.f = neighbor_node.g + neighbor_node.h
                
                # Réinsertion dans le tas (créant un duplicata, mais on traite l'ancien au pop)
                heapq.heappush(open_list, neighbor_node)
            else:
                # 3. Nouveau nœud, calcul complet et insertion
                new_node = Node(current_node, node_position)
                new_node.g = tentative_g
                new_node.h = abs(new_node.position[0] - end_node.position[0]) + abs(new_node.position[1] - end_node.position[1])
                new_node.f = new_node.g + new_node.h
                
                heapq.heappush(open_list, new_node)
                open_set[node_position] = new_node # Ajout au dictionnaire O(1)

    return None

def generate_large_maze(rows, cols, wall_percentage=0.1):
    """Génère une grande grille avec des obstacles aléatoires et des murs centraux."""
    
    # 1. Grille initiale vide (tout à 0)
    maze = [[0 for _ in range(cols)] for _ in range(rows)]
    
    # 2. Ajout d'obstacles aléatoires (pour 10% de la carte)
    for r in range(rows):
        for c in range(cols):
            if random.random() < wall_percentage:
                maze[r][c] = 1

    # 3. Ajout d'un grand mur central pour garantir un long chemin
    
    # Coordonnées du centre
    center_r = rows // 2
    center_c = cols // 2
    
    # Mur vertical épais au centre
    wall_start_r = center_r - 50
    wall_end_r = center_r + 50
    wall_col_start = center_c - 2
    wall_col_end = center_c + 2

    for r in range(wall_start_r, wall_end_r):
        for c in range(wall_col_start, wall_col_end):
            if 0 <= r < rows and 0 <= c < cols:
                maze[r][c] = 1

    return maze

# --- Exemple d'utilisation ---
if __name__ == "__main__":
    # 0 = Espace libre, 1 = Obstacle (mur, meuble, etc.)
    map_grid = [
        [0, 0, 0, 0, 0, 0, 1, 0, 0],
        [0, 1, 1, 1, 0, 0, 1, 0, 1],
        [0, 1, 0, 0, 0, 0, 0, 0, 1],
        [0, 1, 0, 1, 1, 0, 1, 0, 0],
        [0, 0, 0, 0, 1, 0, 1, 0, 1]
    ]
    
    start_pos = (3, 0) # Bas gauche
    end_pos = (3, 8)   # Haut droite

    print("Calcul du chemin de", start_pos, "à", end_pos)
    path = a_star(map_grid, start_pos, end_pos)

    if path:
        print("\nChemin trouvé (lignes, colonnes) :")
        for r, c in path:
            print(f"-> ({r}, {c})")
        
        # Visualisation du chemin sur la grille
        print("\nVisualisation du chemin (X = Robot, 1 = Obstacle) :")
        display_grid = [list(row) for row in map_grid]
        for r, c in path:
            if display_grid[r][c] == 0:
                display_grid[r][c] = 'X'
        
        for row in display_grid:
            print(" ".join(map(str, row)))
    else:
        print("Aucun chemin trouvé.")
    
    import time

    GRID_ROWS = 400
    GRID_COLS = 400
    
    print(f"--- Préparation de la Grille {GRID_ROWS}x{GRID_COLS} ---")
    map_grid = generate_large_maze(GRID_ROWS, GRID_COLS, wall_percentage=0.03) # 3% d'obstacles aléatoires
    
    start_pos = (0, 0) # Coin supérieur gauche
    end_pos = (GRID_ROWS - 1, GRID_COLS - 1) # Coin inférieur droit (399, 399)

    print("Calcul du chemin de", start_pos, "à", end_pos)
    
    start_time = time.time()
    path = a_star(map_grid, start_pos, end_pos)
    end_time = time.time()
    
    elapsed_time = end_time - start_time

    # --- Affichage des résultats ---
    
    if path:
        print(f"\n✅ Chemin trouvé en {elapsed_time:.4f} secondes.")
        print(f"Longueur du chemin : {len(path)} pas.")
        
        # NOTE : L'affichage d'une grille 400x400 est désactivé ici car il est trop long (160 000 caractères).
        # Nous n'affichons que le début et la fin du chemin.
        
        print("\nDébut du chemin (premiers 5 pas) :")
        for r, c in path[:5]:
            print(f"-> ({r}, {c})")

        print("...")
        
        print("Fin du chemin (derniers 5 pas) :")
        for r, c in path[-5:]:
            print(f"-> ({r}, {c})")
            
    else:
        print(f"\n❌ Aucun chemin trouvé. Temps d'exécution : {elapsed_time:.4f} secondes.")
        print("Cela peut indiquer que le chemin est bloqué par des murs.")