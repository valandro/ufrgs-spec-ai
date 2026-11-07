def transform(grid):
    R = len(grid)
    C = len(grid[0])
    
    # 1. Find all color 6 pixels
    magenta_pixels = set()
    for r in range(R):
        for c in range(C):
            if grid[r][c] == 6:
                magenta_pixels.add((r, c))
                
    # 2. Group magenta pixels into connected components (8-connectivity)
    visited = set()
    components = []
    
    for pr, pc in magenta_pixels:
        if (pr, pc) not in visited:
            comp = []
            queue = [(pr, pc)]
            visited.add((pr, pc))
            while queue:
                r, c = queue.pop(0)
                comp.append((r, c))
                for dr, dc in [(-1,0), (1,0), (0,-1), (0,1), (-1,-1), (-1,1), (1,-1), (1,1)]:
                    nr, nc = r + dr, c + dc
                    if (nr, nc) in magenta_pixels and (nr, nc) not in visited:
                        visited.add((nr, nc))
                        queue.append((nr, nc))
            components.append(comp)
            
    # 3. Find markers (non-zero, non-6 pixels)
    markers = []
    for r in range(R):
        for c in range(C):
            val = grid[r][c]
            if val != 0 and val != 6:
                markers.append((r, c, val))
                
    # 4. Associate each marker with the nearest magenta component
    pairs = []
    for mr, mc, val in markers:
        best_comp = None
        min_dist = float('inf')
        for comp in components:
            d = min(abs(mr - cr) + abs(mc - cc) for cr, cc in comp)
            if d < min_dist:
                min_dist = d
                best_comp = comp
        pairs.append((mc, val, best_comp))
        
    # 5. Sort pairs by marker column (left to right)
    pairs.sort(key=lambda x: x[0])
    
    output_blocks = []
    for mc, val, comp in pairs:
        # Find bounding box of comp
        min_r = min(r for r, c in comp)
        min_c = min(c for r, c in comp)
        
        # Extract 4x4 block
        block = []
        for dr in range(4):
            row = []
            for dc in range(4):
                tr = min_r + dr
                tc = min_c + dc
                if 0 <= tr < R and 0 <= tc < C:
                    if grid[tr][tc] == 6:
                        row.append(val)
                    else:
                        row.append(0)
                else:
                    row.append(0)
            block.append(row)
        output_blocks.append(block)
        
    # 6. Concatenate blocks horizontally
    out_R = 4
    out_C = 4 * len(output_blocks)
    output_grid = [[0] * out_C for _ in range(out_R)]
    
    for b_idx, block in enumerate(output_blocks):
        for r in range(4):
            for c in range(4):
                output_grid[r][b_idx * 4 + c] = block[r][c]
                
    return output_grid
