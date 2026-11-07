from collections import Counter


def transform(grid):
    flat = [cell for row in grid for cell in row]
    counts = Counter(flat)
    most_common_color = counts.most_common(1)[0][0]

    output = []
    for row in grid:
        new_row = [
            cell if cell == most_common_color else 5 for cell in row
        ]
        output.append(new_row)
    return output
