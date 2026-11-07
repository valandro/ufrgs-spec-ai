def transform(grid):
    h = len(grid)
    w = len(grid[0])
    
    vert_flip = grid[::-1]
    horiz_flip = [row[::-1] for row in grid]
    
    is_symmetric = (grid == vert_flip) or (grid == horiz_flip)
    
    if h == w:
        transpose = [[grid[c][r] for c in range(h)] for r in range(w)]
        anti_transpose = [[grid[h-1-c][w-1-r] for c in range(h)] for r in range(w)]
        if grid == transpose or grid == anti_transpose:
            is_symmetric = True
            
    if is_symmetric:
        return [[1]]
    else:
        return [[7]]
