#!/usr/bin/env python3
"""
Reads grid placements from src/pages/index.astro and HTML source order,
then generates ASCII layout diagrams for 4-col, 2-col, and 1-col views
and injects them into README.md between <!-- LAYOUT:START --> and <!-- LAYOUT:END -->.

Usage: python scripts/update-layout.py
"""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INDEX = ROOT / "src" / "pages" / "index.astro"
README = ROOT / "README.md"

# --- Cell labels (short names shown in diagrams) ---
LABELS = {
    "a": "STATUS",
    "b": "INPUT_STREAM",
    "c": "GH_STATS",
    "d": "CORRUPT_DATA",
    "e": "RECENT_COMMITS",
}

# --- Parse grid placements from index.astro ---

def parse_placements(src: str) -> dict:
    """Extract grid-column and grid-row for each cell from the 768px+ media query."""
    placements = {}
    # Find cell classes and their grid-column / grid-row inside the 768px block
    cell_blocks = re.findall(
        r'\.cell-([a-z])\s*\{([^}]*grid-(?:column|row)[^}]*)\}', src
    )
    for letter, block in cell_blocks:
        col = re.search(r'grid-column:\s*(\d+)\s*/\s*(\d+)', block)
        row = re.search(r'grid-row:\s*(\d+)\s*/\s*(\d+)', block)
        if col and row:
            placements[letter] = {
                "col": (int(col.group(1)), int(col.group(2))),
                "row": (int(row.group(1)), int(row.group(2))),
            }
    return placements


def parse_source_order(src: str) -> list:
    """Extract cell order from HTML source (section class='cell cell-X')."""
    return re.findall(r'class="cell\s+cell-([a-z])"', src)


# --- Grid renderer ---

def render_grid(grid: list[list[str]], col_width: int = 18) -> str:
    """
    Render a 2D grid (rows of cols, each cell is a letter or None)
    into a box-drawing ASCII diagram with merged spans.
    """
    rows = len(grid)
    cols = len(grid[0]) if grid else 0
    if not rows or not cols:
        return ""

    w = col_width  # inner width per column
    lines = []

    def same(r, c, r2, c2):
        """Check if two positions hold the same non-None cell."""
        if r < 0 or r >= rows or c < 0 or c >= cols:
            return False
        if r2 < 0 or r2 >= rows or c2 < 0 or c2 >= cols:
            return False
        return grid[r][c] is not None and grid[r][c] == grid[r2][c2]

    def cell(r, c):
        if 0 <= r < rows and 0 <= c < cols:
            return grid[r][c]
        return None

    for r in range(rows):
        # --- Top border of row ---
        top = ""
        for c in range(cols):
            # Corner character
            # Look at the 4 cells meeting at this corner: (r-1,c-1), (r-1,c), (r,c-1), (r,c)
            tl = cell(r - 1, c - 1)  # top-left
            tr = cell(r - 1, c)      # top-right
            bl = cell(r, c - 1)      # bottom-left
            br = cell(r, c)          # bottom-right

            # Are there actual borders at this corner?
            # Horizontal border = the cell changes vertically (top != bottom)
            # Vertical border = the cell changes horizontally (left != right)
            need_h = (tl != bl) or (tr != br)  # row transition on either side
            need_v = (tl != tr) or (bl != br)  # col transition on either side

            # But we need to know specifically which directions have lines
            line_up = tl != bl or tr != br      # horizontal line exists above/below
            line_down = tl != bl or tr != br
            line_left = tl != tr or bl != br    # vertical line exists left/right  
            line_right = tl != tr or bl != br

            # More precise: does a line segment extend in each direction?
            seg_up = (c == 0 and r > 0) or (r > 0 and tl != tr)
            seg_down = (c == 0 and r < rows) or (bl != br)
            seg_left = (r == 0 and c > 0) or (c > 0 and tl != bl)
            seg_right = (r == 0) or (tr != br)

            # Edge cases for grid boundaries
            if r == 0:
                seg_up = False
                seg_left = c > 0
                seg_right = True
                seg_down = True
            if c == 0:
                seg_left = False
                seg_up = r > 0
                seg_down = True

            at_top = r == 0
            at_left = c == 0
            at_right = False  # corners are at left side of columns
            at_bottom = False

            if at_top and at_left:
                ch = "┌"
            elif at_top and seg_down:
                ch = "┬"
            elif at_top:
                ch = "─"
            elif at_left and seg_right:
                ch = "├"
            elif at_left:
                ch = "│"
            else:
                # Interior corner — pick box char based on which segments extend
                n = (seg_up, seg_right, seg_down, seg_left)
                box = {
                    (True, True, True, True):   "┼",
                    (True, True, True, False):  "├",
                    (True, False, True, True):  "┤",
                    (True, True, False, True):  "┴",
                    (False, True, True, True):  "┬",
                    (True, True, False, False): "└",
                    (True, False, False, True):  "┘",
                    (False, True, False, True):  "─",
                    (False, False, True, True):  "┐",
                    (False, True, True, False):  "┌",
                    (True, False, True, False):  "│",
                    (True, False, False, False): "╵",
                    (False, True, False, False): "╶",
                    (False, False, True, False): "╷",
                    (False, False, False, True): "╴",
                    (False, False, False, False): " ",
                }
                ch = box.get(n, "┼")

            top += ch

            # Horizontal fill between this col and next
            if same(r - 1, c, r, c):
                top += " " * w
            else:
                top += "─" * w

        # Right edge corner
        tr_cell = cell(r - 1, cols - 1)
        br_cell = cell(r, cols - 1)
        if r == 0:
            top += "┐"
        elif tr_cell is not None and tr_cell == br_cell:
            top += "│"
        else:
            top += "┤"
        lines.append(top)

        # --- Content lines (2 lines per row) ---
        spans = []
        c = 0
        while c < cols:
            cur = grid[r][c]
            span = 1
            while c + span < cols and grid[r][c + span] == cur:
                span += 1
            spans.append((c, span, cur))
            c += span

        for line_idx in range(2):
            content = ""
            for start, span, cur in spans:
                inner_w = w * span + (span - 1)
                if cur is not None:
                    label = LABELS.get(cur, cur.upper())
                    letter = f"[{cur.upper()}]"
                    first_row = (r == 0 or grid[r - 1][start] != cur)
                    if first_row:
                        text = f"  {label}" if line_idx == 0 else f"  {letter}"
                    else:
                        text = ""
                    text = text[:inner_w].ljust(inner_w)
                else:
                    text = " " * inner_w
                content += "│" + text
            content += "│"
            lines.append(content)

    # --- Bottom border ---
    bottom = ""
    for c in range(cols):
        bl = cell(rows - 1, c - 1)
        br = cell(rows - 1, c)
        if c == 0:
            bottom += "└"
        elif bl != br:
            bottom += "┴"
        else:
            bottom += "─"
        bottom += "─" * w
    bottom += "┘"
    lines.append(bottom)

    return "\n".join(lines)


def build_4col(placements: dict) -> str:
    """Build 4-column desktop layout from parsed placements."""
    max_row = max(p["row"][1] for p in placements.values())
    max_col = max(p["col"][1] for p in placements.values())
    rows = max_row - 1
    cols = max_col - 1

    grid = [[None] * cols for _ in range(rows)]
    for letter, p in placements.items():
        for r in range(p["row"][0] - 1, p["row"][1] - 1):
            for c in range(p["col"][0] - 1, p["col"][1] - 1):
                grid[r][c] = letter

    return render_grid(grid, col_width=16)


def build_2col(source_order: list) -> str:
    """Build 2-column tablet layout. C spans 2 cols, others fill L-R."""
    grid = []
    queue = [c for c in source_order if c != "c"]
    for cell in source_order:
        if cell == "c":
            grid.append(["c", "c"])
        elif queue:
            row = [queue.pop(0)]
            if queue:
                row.append(queue.pop(0))
            else:
                row.append(row[0])  # span
            grid.append(row)
    return render_grid(grid, col_width=20)


def build_1col(source_order: list) -> str:
    """Build 1-column mobile layout (source order, single column)."""
    grid = [[c] for c in source_order]
    return render_grid(grid, col_width=40)


# --- README injection ---

def inject_layout(readme: str, layout_block: str) -> str:
    """Replace content between LAYOUT markers, or replace the old Layout section."""
    marker_start = "<!-- LAYOUT:START -->"
    marker_end = "<!-- LAYOUT:END -->"

    if marker_start in readme:
        pattern = re.escape(marker_start) + r".*?" + re.escape(marker_end)
        return re.sub(pattern, f"{marker_start}\n{layout_block}\n{marker_end}", readme, flags=re.DOTALL)
    else:
        # Replace existing Layout section (from ## Layout to next ---)
        pattern = r"## Layout\n.*?\n---"
        replacement = f"## Layout\n\n{marker_start}\n{layout_block}\n{marker_end}\n\n---"
        return re.sub(pattern, replacement, readme, flags=re.DOTALL)


def main():
    src = INDEX.read_text()
    placements = parse_placements(src)
    source_order = parse_source_order(src)

    print(f"Placements: {placements}")
    print(f"Source order: {source_order}")

    d4 = build_4col(placements)
    d2 = build_2col(source_order)
    d1 = build_1col(source_order)

    block = f"""**4 columns** (desktop, 768px+)

```
{d4}
```

**2 columns** (tablet, 580px+)

```
{d2}
```

**1 column** (mobile)

```
{d1}
```

Source order: {' → '.join(c.upper() for c in source_order)}"""

    readme = README.read_text()
    readme = inject_layout(readme, block)
    README.write_text(readme)
    print("README.md updated with layout diagrams.")


if __name__ == "__main__":
    main()
