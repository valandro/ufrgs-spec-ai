from collections import defaultdict


def transform(grid):
    H = len(grid)
    W_grid = len(grid[0])

    candidates = []

    # Search for subgrids of height 3 and width 3 or 4
    for h in [3]:
        for w in [3, 4]:
            for r in range(H - h + 1):
                for c in range(W_grid - w + 1):
                    subgrid = [row[c : c + w] for row in grid[r : r + h]]
                    # Check if subgrid is not entirely zeros
                    if any(cell != 0 for row in subgrid for cell in row):
                        sub_tuple = tuple(tuple(row) for row in subgrid)
                        candidates.append((sub_tuple, r, c, subgrid))

    groups = defaultdict(list)
    for sub_tuple, r, c, subgrid in candidates:
        groups[sub_tuple].append((r, c, subgrid))

    # Look for groups with duplicates (appear > 1 time)
    duplicate_groups = [g for g in groups.values() if len(g) > 1]

    if duplicate_groups:
        all_dups = []
        for g in duplicate_groups:
            all_dups.extend(g)
        all_dups.sort(key=lambda x: x[0])  # sort by row index r
        return all_dups[0][2]
    else:
        if candidates:
            return candidates[0][3]
        return []
