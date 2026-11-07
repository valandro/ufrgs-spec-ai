def transform(grid):
    rows = len(grid)
    cols = len(grid[0])
    
    r8_coords = [(r, c) for r in range(rows) for c in range(cols) if grid[r][c] == 8]
    
    if not r8_coords:
        return [row[:] for row in grid]
        
    min_r = min(r for r, c in r8_coords)
    max_r = max(r for r, c in r8_coords)
    min_c = min(c for r, c in r8_coords)
    max_c = max(c for r, c in r8_coords)
    
    output = [row[:] for row in grid]
    for r in range(min_r, max_r + 1):
        for c in range(min_c, max_c + 1):
            if output[r][c] == 1:
                output[r][c] = 3
                
    return output
