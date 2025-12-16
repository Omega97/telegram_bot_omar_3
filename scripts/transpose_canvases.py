# scripts/transpose_canvases.py
"""
Transposes all canvas CSV files in data/PRIVATE/canvases/.
Each file is a comma-separated matrix of user IDs.
After transposing: new[y][x] = old[x][y]
"""
import csv
from pathlib import Path
from omar_bot.config.settings import CANVAS_DIR


def transpose_csv_file(file_path: Path) -> None:
    """Load, transpose, and overwrite a CSV canvas file."""
    # Read original grid
    grid = []
    with open(file_path, "r", newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:
            # Skip empty rows
            if not row or all(cell.strip() == "" for cell in row):
                continue
            # Convert to int (user IDs); treat empty cells as 0
            int_row = []
            for cell in row:
                cell = cell.strip()
                if cell == "":
                    int_row.append(0)
                else:
                    try:
                        int_row.append(int(cell))
                    except ValueError:
                        print(f"⚠️  Invalid cell in {file_path}: {cell!r}, treating as 0")
                        int_row.append(0)
            grid.append(int_row)

    if not grid or not grid[0]:
        print(f"🟡 Skipping empty canvas: {file_path.name}")
        return

    # Transpose: new_grid[i][j] = grid[j][i]
    rows = len(grid)
    cols = len(grid[0])

    # Ensure rectangular matrix
    for i, row in enumerate(grid):
        if len(row) != cols:
            print(f"⚠️  Padding row {i} in {file_path.name} to {cols} columns")
            row.extend([0] * (cols - len(row)))

    transposed = [[grid[y][x] for y in range(rows)] for x in range(cols)]

    # Write back to same file
    with open(file_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        for row in transposed:
            writer.writerow(row)

    print(f"✅ Transposed {file_path.name}: {rows}x{cols} → {cols}x{rows}")


def main():
    if not CANVAS_DIR.exists():
        print("❌ CANVAS_DIR does not exist:", CANVAS_DIR)
        return

    csv_files = list(CANVAS_DIR.glob("*.csv"))
    if not csv_files:
        print("ℹ️  No CSV files found in", CANVAS_DIR)
        return

    print(f"🔍 Found {len(csv_files)} canvas file(s) in {CANVAS_DIR}")
    for csv_file in sorted(csv_files):
        try:
            print(f'Transposing {csv_file}')
            transpose_csv_file(csv_file)
        except Exception as e:
            print(f"❌ Failed to transpose {csv_file.name}: {e}")

    print("✨ All canvases transposed!")


if __name__ == "__main__":
    main()
