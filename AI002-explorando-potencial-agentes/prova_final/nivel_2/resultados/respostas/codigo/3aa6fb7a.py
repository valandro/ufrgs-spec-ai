import copy

def transform(grid):
    R = len(grid)
    C = len(grid[0])
    output = copy.deepcopy(grid)
    
    visited = [[False] * C for _ in range(R)]
    
    for r in range(R):
        for c in range(C):
            if grid[r][c] == 8 and not visited[r][c]:
                # Find connected component of 8s (8-connectivity)
                comp = []
                queue = [(r, c)]
                visited[r][c] = True
                
                while queue:
                    cr, cc = queue.pop(0)
                    comp.append((cr, cc))
                    for dr in [-1, 0, 1]:
                        for dc in [-1, 0, 1]:
                            if dr == 0 and dc == 0:
                                continue
                            nr, nc = cr + dr, cc + dc
                            if 0 <= nr < R and 0 <= nc < C:
                                if grid[nr][nc] == 8 and not visited[nr][nc]:
                                    visited[nr][nc] = True
                                    queue.append((nr, nc))
                
                # Determine the bounding box of the component
                min_r = min(p[0] for p in comp)
                max_r = max(p[0] for p in comp)
                min_c = min(p[1] for p in comp)
                max_c = max(p[1] for p in comp)
                
                comp_set = set(comp)
                # Find the missing corner in the 2x2 bounding box and set it to 1
                for br in range(min_r, max_r + 1):
                    for bc in range(min_c, max_c + 1):
                        if (br, bc) not in comp_set:
                            output[br][bc] = 1
                            
    return output
