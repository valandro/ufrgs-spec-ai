def transform(grid):
    # Find all unique non-zero colors
    colors = set()
    for row in grid:
        for val in row:
            if val != 0:
                colors.add(val)
                
    # Calculate bounding box size for each color
    color_sizes = {}
    for color in colors:
        coords = []
        for r, row in enumerate(grid):
            for c, val in enumerate(row):
                if val == color:
                    coords.append((r, c))
        min_r = min(r for r, c in coords)
        max_r = max(r for r, c in coords)
        min_c = min(c for r, c in coords)
        max_c = max(c for r, c in coords)
        height = max_r - min_r + 1
        width = max_c - min_c + 1
        color_sizes[color] = max(height, width)
        
    # Sort colors by size in descending order
    sorted_colors = sorted(list(colors), key=lambda x: color_sizes[x], reverse=True)
    
    # N is the size of the largest color (outermost square)
    N = color_sizes[sorted_colors[0]]
    
    # Initialize N x N output grid with zeros
    out = [[0] * N for _ in range(N)]
    
    # Fill layers from outermost to innermost
    for i, color in enumerate(sorted_colors):
        s = N - 2 * i
        if s <= 0:
            break
        is_last = (i == len(sorted_colors) - 1)
        
        for r in range(i, i + s):
            for c in range(i, i + s):
                if is_last or r == i or r == i + s - 1 or c == i or c == i + s - 1:
                    out[r][c] = color
                    
    return out
