def transform(grid):
    # Find the 1-block (bounding box of color 1)
    r_indices = []
    c_indices = []
    for r in range(len(grid)):
        for c in range(len(grid[0])):
            if grid[r][c] == 1:
                r_indices.append(r)
                c_indices.append(c)

    r_min, r_max = min(r_indices), max(r_indices)
    c_min, c_max = min(c_indices), max(c_indices)

    # Get the 4 marker colors from the interior of the 1-block
    A = grid[r_min + 1][c_min + 1]
    B = grid[r_min + 1][c_min + 5]
    C = grid[r_min + 5][c_min + 1]
    D = grid[r_min + 5][c_min + 5]

    def get_shape(color):
        cells = []
        for r in range(len(grid)):
            for c in range(len(grid[0])):
                if grid[r][c] == color:
                    # Ignore cells that fall inside the 1-block
                    if not (r_min <= r <= r_max and c_min <= c <= c_max):
                        cells.append((r, c))
        if not cells:
            return [[0] * 3 for _ in range(3)]
        min_r = min(r for r, c in cells)
        min_c = min(c for r, c in cells)
        shape = []
        for r in range(min_r, min_r + 3):
            row = []
            for c in range(min_c, min_c + 3):
                row.append(grid[r][c])
            shape.append(row)
        return shape

    shape_A = get_shape(A)
    shape_B = get_shape(B)
    shape_C = get_shape(C)
    shape_D = get_shape(D)

    # Build the 7x7 output grid
    output = [[0] * 7 for _ in range(7)]

    # Place shape A at top-left
    for r in range(3):
        for c in range(3):
            output[r][c] = shape_A[r][c]

    # Place shape B at top-right
    for r in range(3):
        for c in range(3):
            output[r][c + 4] = shape_B[r][c]

    # Place shape C at bottom-left
    for r in range(3):
        for c in range(3):
            output[r + 4][c] = shape_C[r][c]

    # Place shape D at bottom-right
    for r in range(3):
        for c in range(3):
            output[r + 4][c + 4] = shape_D[r][c]

    return output
