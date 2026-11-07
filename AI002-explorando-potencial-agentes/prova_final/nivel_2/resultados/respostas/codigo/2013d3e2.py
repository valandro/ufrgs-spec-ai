def transform(grid):
    R = len(grid)
    C = len(grid[0])
    
    min_r, max_r = R, -1
    min_c, max_c = C, -1
    
    for r in range(R):
        for c in range(C):
            if grid[r][c] != 0:
                if r < min_r: min_r = r
                if r > max_r: max_r = r
                if c < min_c: min_c = c
                if c > max_c: max_c = c
                 
    height = max_r - min_r + 1
    width = max_c - min_c + 1
    
    half_h = height // 2
    half_w = width // 2
    
    # Extract top-right quadrant of the bounding box
    subgrid = []
    for r in range(min_r, min_r + half_h):
        row = []
        for c in range(max_c - half_w + 1, max_c + 1):
            row.append(grid[r][c])
        subgrid.append(row)
        
    # Horizontal flip
    flipped = [row[::-1] for row in subgrid]
    
    # Transpose
    output = []
    for c in range(half_w):
        new_row = []
        for r in range(half_h):
            new_row.append(flipped[r][c])
        output.append(new_row)
        
    return output
