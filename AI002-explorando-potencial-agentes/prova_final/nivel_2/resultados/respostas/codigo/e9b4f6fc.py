def transform(grid):
    R = len(grid)
    C = len(grid[0])
    
    # Find all non-zero connected components using 4-connectivity
    visited = [[False] * C for _ in range(R)]
    components = []
    
    for r in range(R):
        for c in range(C):
            if grid[r][c] != 0 and not visited[r][c]:
                comp = []
                queue = [(r, c)]
                visited[r][c] = True
                while queue:
                    curr_r, curr_c = queue.pop(0)
                    comp.append((curr_r, curr_c))
                    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        nr, nc = curr_r + dr, curr_c + dc
                        if 0 <= nr < R and 0 <= nc < C and not visited[nr][nc] and grid[nr][nc] != 0:
                            visited[nr][nc] = True
                            queue.append((nr, nc))
                components.append(comp)
                
    # The template is the largest non-zero component
    largest_comp = max(components, key=len)
    
    # Bounding box of the template
    min_r = min(r for r, c in largest_comp)
    max_r = max(r for r, c in largest_comp)
    min_c = min(c for r, c in largest_comp)
    max_c = max(c for r, c in largest_comp)
    
    # Find mapping pairs [value, key] outside the template bounding box
    mapping = {}
    for r in range(R):
        for c in range(C - 1):
            in_bbox_1 = (min_r <= r <= max_r and min_c <= c <= max_c)
            in_bbox_2 = (min_r <= r <= max_r and min_c <= c + 1 <= max_c)
            
            if not in_bbox_1 and not in_bbox_2:
                if grid[r][c] != 0 and grid[r][c + 1] != 0:
                    val = grid[r][c]
                    key = grid[r][c + 1]
                    mapping[key] = val
                    
    # Construct output by extracting the template and applying color mappings
    output = []
    for r in range(min_r, max_r + 1):
        out_row = []
        for c in range(min_c, max_c + 1):
            val = grid[r][c]
            if val in mapping:
                out_row.append(mapping[val])
            else:
                out_row.append(val)
        output.append(out_row)
        
    return output
