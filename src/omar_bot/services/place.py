import logging
import csv
from pathlib import Path
from datetime import datetime
from typing import List, Tuple
from omar_bot.config.settings import DEBUG, CANVAS_DIR, PLACE_COOLDOWN_MINUTES
from omar_bot.services.user_service import UserService


logger = logging.getLogger(__name__)


class PlaceService:
    """
    Handles the canvases used for painting with emoji.
    """
    def __init__(self, user_service: UserService):
        self.user_service = user_service
        self.canvases_dir = CANVAS_DIR
        self.canvases_dir.mkdir(parents=True, exist_ok=True)

    def _get_canvas_path(self, canvas_name: str) -> Path:
        """Get the file path for a canvas."""
        return self.canvases_dir / f"{canvas_name}.csv"

    def _load_canvas(self, canvas_name: str) -> List[List[int]]:
        """Load canvas data from CSV file."""
        canvas_path = self._get_canvas_path(canvas_name)
        if not canvas_path.exists():
            # Create a default 20x20 canvas if it doesn't exist
            return [[0 for _ in range(20)] for _ in range(20)]

        try:
            grid = []
            with open(canvas_path, 'r', newline='') as f:
                reader = csv.reader(f)
                for row in reader:
                    grid.append([int(cell) for cell in row if cell.strip()])
            return grid
        except Exception as e:
            logger.error(f"Error loading canvas {canvas_name}: {e}")
            # Return default canvas on error
            return [[0 for _ in range(20)] for _ in range(20)]

    def _save_canvas(self, canvas_name: str, grid: List[List[int]]) -> None:
        """Save canvas data to CSV file."""
        canvas_path = self._get_canvas_path(canvas_name)
        try:
            with open(canvas_path, 'w', newline='') as f:
                writer = csv.writer(f)
                for row in grid:
                    writer.writerow(row)
        except Exception as e:
            logger.error(f"Error saving canvas {canvas_name}: {e}")
            raise

    def _get_emoji_for_user(self, user_id: int) -> str:
        """Get the emoji for a user, or default if not found."""
        if user_id == 0:
            return "➕"  # Empty space

        user_data = self.user_service.get_user(user_id)
        if not user_data:
            return "❓"  # Unknown user

        return user_data.get('emoji', '❓')

    def can_place_tile(self, user_id: int, canvas_name: str, x: int, y: int) -> Tuple[bool, str]:
        """
        Check if a user can place a tile at the given position.
        Returns (can_place, error_message)
        """
        user_data = self.user_service.get_user(user_id)
        if not user_data:
            return False, "User not found. Please start the bot first."

        # Check cooldown
        last_place_time = user_data.get('last_place_time', 0)
        if not DEBUG and last_place_time:
            cooldown_seconds = PLACE_COOLDOWN_MINUTES * 60
            time_since_last = datetime.now().timestamp() - last_place_time
            if time_since_last < cooldown_seconds:
                remaining = cooldown_seconds - time_since_last
                mins = int(remaining // 60)
                secs = int(remaining % 60)
                return False, f"Cooldown active. Wait {mins}m {secs}s before placing another tile."

        # Load canvas
        grid = self._load_canvas(canvas_name)

        # Check bounds
        if y < 0 or y >= len(grid) or x < 0 or x >= len(grid[0]):
            return False, f"Position ({x}, {y}) is out of bounds. Canvas size: {len(grid[0])}x{len(grid)}."

        return True, ""

    def place_tile(self, user_id: int, canvas_name: str, x: int, y: int) -> Tuple[bool, str]:
        """Place or remove a tile at the specified position."""
        can_place, error = self.can_place_tile(user_id, canvas_name, x, y)
        if not can_place:
            return False, error

        grid = self._load_canvas(canvas_name)
        current_owner = grid[y][x]

        if current_owner == user_id:
            # Remove own tile
            grid[y][x] = 0
            self._save_canvas(canvas_name, grid)
            return True, "✅ Your tile has been removed!"
        else:
            # Place new tile
            grid[y][x] = user_id
            self._save_canvas(canvas_name, grid)

            # Award gem and increment tile count
            self.user_service.set(user_id, 'last_place_time', int(datetime.now().timestamp()))
            self.user_service.set(user_id, 'tiles_count', self.user_service.get(user_id, 'tiles_count', 0) + 1)
            self.user_service.set(user_id, 'gems', self.user_service.get(user_id, 'gems', 0) + 1)

            return True, "✅ Tile placed successfully!"

    def get_canvas_display(self, canvas_name: str) -> str:
        """Generate a compact text representation of the canvas with emojis and numeric coordinates."""
        grid = self._load_canvas(canvas_name)
        lines = []

        # Define number emoji mapping 0-9
        num_emojis = ["0️⃣", "1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣"]

        # Create header with column numbers (0️⃣1️⃣2️⃣...)
        header_nums = "".join(num_emojis[i % 10] for i in range(len(grid[0])))
        header = "⏹️" + header_nums
        lines.append(header)

        # Create rows with user emojis (no spaces between tiles)
        for y, row in enumerate(grid):
            # Row label with number emoji (0️⃣, 1️⃣, ...)
            row_label = num_emojis[y % 10]
            # Build row content without spaces
            row_content = ""
            for x, user_id in enumerate(row):
                emoji = self._get_emoji_for_user(user_id)
                row_content += emoji
            line = row_label + row_content
            lines.append(line)

        return "\n".join(lines)

    def reset_canvas(self, canvas_name: str) -> bool:
        """Reset a canvas to empty state."""
        try:
            grid = self._load_canvas(canvas_name)
            # Create empty grid of same dimensions
            empty_grid = [[0 for _ in range(len(grid[0]))] for _ in range(len(grid))]
            self._save_canvas(canvas_name, empty_grid)
            return True
        except Exception as e:
            logger.error(f"Error resetting canvas {canvas_name}: {e}")
            return False

    def delete_canvas(self, canvas_name: str) -> bool:
        """Delete a canvas file."""
        canvas_path = self._get_canvas_path(canvas_name)
        if canvas_path.exists():
            try:
                canvas_path.unlink()
                return True
            except Exception as e:
                logger.error(f"Error deleting canvas {canvas_name}: {e}")
                return False
        return False

    def set_user_canvas(self, user_id: int, canvas_name: str) -> bool:
        """Set the canvas for a user."""
        try:
            self.user_service.set(user_id, 'canvas', canvas_name)
            return True
        except Exception as e:
            logger.error(f"Error setting canvas for user {user_id}: {e}")
            return False
