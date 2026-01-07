# Fichier : pathfinding_a_star.py

import heapq

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
    Algorithme A* pour trouver le chemin le plus court.

    :param maze: Carte 2D (0=libre, 1=obstacle).
    :param start: Tuple (row, col) du point de départ.
    :param end: Tuple (row, col) du point d'arrivée.
    :return: Liste des coordonnées du chemin, ou None si aucun chemin n'est trouvé.
    """
    # Création des nœuds de départ et d'arrivée
    start_node = Node(None, start)
    end_node = Node(None, end)
    
    # Initialisation des listes
    open_list = [] # Liste des nœuds à explorer (Priority Queue/Heap)
    closed_list = set() # Ensemble des nœuds déjà explorés

    # Ajout du nœud de départ à la liste ouverte
    heapq.heappush(open_list, start_node)

    # Limites de la grille
    rows, cols = len(maze), len(maze[0])
    
    # Directions possibles (haut, bas, gauche, droite, et diagonales - optionnel)
    # Pour un robot simple, on peut commencer par 4 directions (pas de diagonales)
    move_directions = [(0, -1), (0, 1), (-1, 0), (1, 0)]  # Ouest, Est, Nord, Sud

    while open_list:
        # Récupère le nœud courant avec le plus petit coût f (Priorité)
        current_node = heapq.heappop(open_list)
        closed_list.add(current_node.position)

        # Vérification si le but est atteint
        if current_node == end_node:
            path = []
            current = current_node
            while current is not None:
                path.append(current.position)
                current = current.parent
            return path[::-1] # Inverse le chemin pour aller du début à la fin

        # Exploration des voisins
        for direction in move_directions:
            node_position = (current_node.position[0] + direction[0], 
                             current_node.position[1] + direction[1])

            # Vérification si le voisin est dans la grille
            if not (0 <= node_position[0] < rows and 0 <= node_position[1] < cols):
                continue

            # Vérification si le voisin est un obstacle (maze[r][c] == 1)
            if maze[node_position[0]][node_position[1]] != 0:
                continue
            
            # Vérification si le voisin a déjà été exploré
            if node_position in closed_list:
                continue

            # Création du nouveau nœud voisin
            new_node = Node(current_node, node_position)

            # Calcul des coûts G, H et F
            # G = Coût du parent + Coût pour atteindre ce nœud (ici, 1 pour chaque pas)
            new_node.g = current_node.g + 1
            
            # H = Heuristique (Distance de Manhattan)
            new_node.h = abs(new_node.position[0] - end_node.position[0]) + abs(new_node.position[1] - end_node.position[1])
            
            # F = G + H
            new_node.f = new_node.g + new_node.h

            # Vérification si le nœud est déjà dans la liste ouverte avec un meilleur chemin
            # Cette vérification est simplifiée par l'utilisation de la Priority Queue.
            
            # Ajout du voisin à la liste ouverte (s'il n'est pas déjà présent)
            is_in_open = False
            for open_node in open_list:
                if new_node == open_node and new_node.g >= open_node.g:
                    is_in_open = True
                    break
            
            if not is_in_open:
                heapq.heappush(open_list, new_node)

    return None # Aucun chemin trouvé

# --- Exemple d'utilisation ---
if __name__ == "__main__":
    # 0 = Espace libre, 1 = Obstacle (mur, meuble, etc.)
    map_grid = [
        [0, 0, 0, 0, 0],
        [0, 1, 1, 1, 0],
        [0, 0, 0, 0, 0],
        [0, 1, 0, 1, 0],
        [0, 0, 0, 0, 0]
    ]
    
    start_pos = (4, 0) # Bas gauche
    end_pos = (0, 4)   # Haut droite

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