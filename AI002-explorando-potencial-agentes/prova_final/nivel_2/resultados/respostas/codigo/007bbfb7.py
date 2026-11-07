def transform(grid):
    output = [[0] * 9 for _ in range(9)]
    for r in range(3):
        for c in range(3):
            if grid[r][c] != 0:
                for i in range(3):
                    for j in range(3):
                        output[3 * r + i][3 * c + j] = grid[i][j]
    return output
