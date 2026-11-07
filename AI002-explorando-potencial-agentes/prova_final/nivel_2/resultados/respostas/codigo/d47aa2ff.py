def transform(grid):
    mid = grid[0].index(5)
    output = []
    for r in range(len(grid)):
        out_row = []
        for c in range(mid):
            v_l = grid[r][c]
            v_r = grid[r][mid + 1 + c]
            if v_l == v_r:
                out_row.append(v_l)
            elif v_l != 0 and v_r == 0:
                out_row.append(2)
            elif v_l == 0 and v_r != 0:
                out_row.append(1)
            else:
                out_row.append(v_l)
        output.append(out_row)
    return output
