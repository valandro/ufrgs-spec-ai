from collections import defaultdict

def transform(grid):
    R = len(grid)
    C = len(grid[0])
    
    blocks = []
    for r in range(R - 1):
        for c in range(C - 1):
            if (grid[r][c] == 8 and grid[r][c+1] == 8 and 
                grid[r+1][c] == 8 and grid[r+1][c+1] == 8):
                blocks.append((r, c))
                
    row_to_cols = defaultdict(list)
    for r, c in blocks:
        row_to_cols[r].append(c)
        
    output = []
    for r in sorted(row_to_cols.keys()):
        cols = sorted(row_to_cols[r])
        for i in range(0, len(cols), 2):
            if i + 1 < len(cols):
                c_left = cols[i]
                c_right = cols[i+1]
                output.append(grid[r][c_left + 2 : c_right])
                output.append(grid[r+1][c_left + 2 : c_right])
                
    return output
