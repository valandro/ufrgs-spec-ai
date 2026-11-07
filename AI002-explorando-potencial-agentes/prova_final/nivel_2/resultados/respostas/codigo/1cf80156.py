def transform(grid):
    coords = []
    for r in range(len(grid)):
        for c in range(len(grid[0])):
            if grid[r][c] != 0:
                coords.append((r, c))
                
    if not coords:
        return []
        
    min_r = min(r for r, c in coords)
    max_r = max(r for r, c in coords)
    min_c = min(c for r, c in coords)
    max_c = max(c for r, c in coords)
    
    output = []
    for r in range(min_r, max_r + 1):
        output.append(grid[r][min_c : max_c + 1])
        
    return output
