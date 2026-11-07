def transform(grid):
    H = len(grid)
    W = len(grid[0])
    
    pixels = []
    for r in range(H):
        for c in range(W):
            if grid[r][c] != 0:
                pixels.append((r, c, grid[r][c]))
                
    if len(pixels) != 2:
        return grid
        
    p1, p2 = pixels[0], pixels[1]
    r1, c1, v1 = p1
    r2, c2, v2 = p2
    
    if (r1, c1) > (r2, c2):
        r1, c1, v1, r2, c2, v2 = r2, c2, v2, r1, c1, v1
        
    output = [[0] * W for _ in range(H)]
    
    if min(c1, c2) == 0:
        # Horizontal pattern (rows)
        dr = r2 - r1
        for r in range(H):
            if (r - r1) % dr == 0:
                k = (r - r1) // dr
                if k % 2 == 0:
                    output[r] = [v1] * W
                else:
                    output[r] = [v2] * W
    else:
        # Vertical pattern (columns)
        if c1 > c2:
            s1, cval1, s2, cval2 = c2, v2, c1, v1
        else:
            s1, cval1, s2, cval2 = c1, v1, c2, v2
            
        d = s2 - s1
        row_template = [0] * W
        k = 0
        while True:
            col = s1 + k * d
            if col >= W:
                break
            if k % 2 == 0:
                row_template[col] = cval1
            else:
                row_template[col] = cval2
            k += 1
            
        for r in range(H):
            output[r] = list(row_template)
            
    return output
