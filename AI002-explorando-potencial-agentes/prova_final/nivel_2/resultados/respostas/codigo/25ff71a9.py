def transform(grid):
    rows = len(grid)
    cols = len(grid[0])
    new_grid = [[0] * cols for _ in range(rows)]
    for r in range(1, rows):
        new_grid[r] = list(grid[r-1])
    return new_grid
