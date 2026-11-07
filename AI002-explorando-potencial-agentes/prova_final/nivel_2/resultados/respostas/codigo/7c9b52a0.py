def transform(grid):
    bg = grid[0][0]
    R = len(grid)
    C = len(grid[0])
    
    visited = [[False] * C for _ in range(R)]
    components = []
    
    for r in range(R):
        for c in range(C):
            if grid[r][c] != bg and not visited[r][c]:
                comp = []
                queue = [(r, c)]
                visited[r][c] = True
                while queue:
                    cr, cc = queue.pop(0)
                    comp.append((cr, cc))
                    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        nr, nc = cr + dr, cc + dc
                        if 0 <= nr < R and 0 <= nc < C and not visited[nr][nc] and grid[nr][nc] != bg:
                            visited[nr][nc] = True
                            queue.append((nr, nc))
                components.append(comp)
                
    subgrids = []
    for comp in components:
        r_min = min(r for r, c in comp)
        r_max = max(r for r, c in comp)
        c_min = min(c for r, c in comp)
        c_max = max(c for r, c in comp)
        
        subgrid = []
        for r in range(r_min, r_max + 1):
            row = []
            for c in range(c_min, c_max + 1):
                row.append(grid[r][c])
            subgrid.append(row)
        subgrids.append(subgrid)
        
    if not subgrids:
        return []
        
    H = len(subgrids[0])
    W = len(subgrids[0][0])
    
    output = [[0] * W for _ in range(H)]
    for subgrid in subgrids:
        for r in range(H):
            for c in range(W):
                val = subgrid[r][c]
                if val != 0:
                    output[r][c] = val
                    
    return output
