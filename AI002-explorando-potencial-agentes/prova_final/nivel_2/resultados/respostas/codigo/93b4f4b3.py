def transform(grid):
    bg = grid[0][0]
    
    # Find left_width by counting consecutive background color in row 0
    left_width = 0
    while left_width < len(grid[0]) and grid[0][left_width] == bg:
        left_width += 1
        
    # Find separator rows (rows where all left_width elements equal bg)
    separator_rows = []
    for r in range(len(grid)):
        if all(grid[r][c] == bg for c in range(left_width)):
            separator_rows.append(r)
            
    # Extract subgrids
    subgrids = []
    for i in range(len(separator_rows) - 1):
        start_r = separator_rows[i] + 1
        end_r = separator_rows[i+1]
        if start_r < end_r:
            subgrid_rows = grid[start_r:end_r]
            
            # Find associated color from the right side of this subgrid
            color = None
            for r in range(start_r, end_r):
                for c in range(left_width, len(grid[r])):
                    val = grid[r][c]
                    if val != 0 and val != bg:
                        color = val
                        break
                if color is not None:
                    break
            
            subgrids.append({
                'color': color,
                'rows': subgrid_rows
            })
            
    # Sort subgrids by associated color in ascending order
    subgrids.sort(key=lambda x: x['color'])
    
    # Build output grid
    sep_row = [bg] * left_width
    output = [sep_row]
    
    for sg in subgrids:
        for in_row in sg['rows']:
            right_part = in_row[left_width:]
            out_row = []
            for val in right_part:
                if val != 0:
                    out_row.append(val)
                else:
                    out_row.append(bg)
            while len(out_row) < left_width:
                out_row.append(bg)
            output.append(out_row[:left_width])
        output.append(sep_row)
        
    return output
