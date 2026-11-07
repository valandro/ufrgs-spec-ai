def transform(grid):
    R = len(grid)
    C = len(grid[0])
    
    candidates = []
    for r in range(R - 2):
        for c in range(C - 2):
            subgrid = [row[c:c+3] for row in grid[r:r+3]]
            if all(cell != 0 for row in subgrid for cell in row):
                colors = set(cell for row in subgrid for cell in row)
                candidates.append((len(colors), subgrid))
                
    if not candidates:
        return []
    
    candidates.sort(key=lambda x: x[0], reverse=True)
    return candidates[0][1]
