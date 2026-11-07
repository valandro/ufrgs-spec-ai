def transform(grid):
    R = len(grid)
    C = len(grid[0])
    
    # 1. Find background 0s connected to the border
    visited_bg = [[False]*C for _ in range(R)]
    queue = []
    
    for r in range(R):
        for c in range(C):
            if (r == 0 or r == R-1 or c == 0 or c == C-1) and grid[r][c] == 0:
                if not visited_bg[r][c]:
                    visited_bg[r][c] = True
                    queue.append((r, c))
                    
    head = 0
    while head < len(queue):
        r, c = queue[head]
        head += 1
        for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < R and 0 <= nc < C:
                if not visited_bg[nr][nc] and grid[nr][nc] == 0:
                    visited_bg[nr][nc] = True
                    queue.append((nr, nc))
                    
    # 2. Find holes (0-cells that are not connected to the background)
    visited_hole = [[False]*C for _ in range(R)]
    holes = []
    
    for r in range(R):
        for c in range(C):
            if grid[r][c] == 0 and not visited_bg[r][c] and not visited_hole[r][c]:
                hole_cells = []
                q = [(r, c)]
                visited_hole[r][c] = True
                
                h_head = 0
                while h_head < len(q):
                    hr, hc = q[h_head]
                    h_head += 1
                    hole_cells.append((hr, hc))
                    for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)]:
                        nnr, nnc = hr + dr, hc + dc
                        if 0 <= nnr < R and 0 <= nnc < C:
                            if grid[nnr][nnc] == 0 and not visited_bg[nnr][nnc] and not visited_hole[nnr][nnc]:
                                visited_hole[nnr][nnc] = True
                                q.append((nnr, nnc))
                                
                holes.append(hole_cells)
                
    # 3. Process each hole and fill with 2 if it's a solid square
    output_grid = [row[:] for row in grid]
    
    for hole in holes:
        min_r = min(r for r, c in hole)
        max_r = max(r for r, c in hole)
        min_c = min(c for r, c in hole)
        max_c = max(c for r, c in hole)
        
        height = max_r - min_r + 1
        width = max_c - min_c + 1
        
        if height == width:
            is_solid_square = True
            for r in range(min_r, max_r + 1):
                for c in range(min_c, max_c + 1):
                    if grid[r][c] != 0 or visited_bg[r][c]:
                        is_solid_square = False
                        break
                if not is_solid_square:
                    break
                    
            if is_solid_square:
                for r in range(min_r, max_r + 1):
                    for c in range(min_c, max_c + 1):
                        output_grid[r][c] = 2
                        
    return output_grid
