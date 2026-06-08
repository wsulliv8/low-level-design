import re
from typing import Dict, Set, List


class Cell:
    """A single node inside the spreadsheet matrix capable of reactive evaluation."""

    def __init__(self, coordinate: str):
        self.coordinate = coordinate
        self.raw_value: str = (
            "0"  # Can be a raw number string ("10") or formula ("=SUM(A1,B2)")
        )
        self.calculated_value: float = 0.0

        # Dependency Graph Connections
        self.inputs: Set[str] = set()  # Cells that THIS cell reads from
        self.dependents: Set[str] = set()  # Cells that rely on THIS cell's value


class Spreadsheet:
    """The matrix coordinator managing cell state transformations and evaluations."""

    def __init__(self):
        self.matrix: Dict[str, Cell] = {}

    def _get_or_create_cell(self, coord: str) -> Cell:
        coord = coord.upper()
        if coord not in self.matrix:
            self.matrix[coord] = Cell(coord)
        return self.matrix[coord]

    def set_value(self, coord: str, value: str) -> None:
        """Sets raw value or formula to a target coordinate, updating dependencies."""
        coord = coord.upper()
        cell = self._get_or_create_cell(coord)

        # 1. Sever old input bonds before rewriting the cell's equation
        for input_coord in cell.inputs:
            if input_coord in self.matrix:
                self.matrix[input_coord].dependents.discard(coord)
        cell.inputs.clear()

        # 2. Parse new raw value or extract formula targets
        cell.raw_value = value
        if value.startswith("="):
            # Use Regex to isolate cell coordinate strings (e.g., extracts ['A1', 'B2'] from "=SUM(A1,B2)")
            extracted_inputs = re.findall(r"[A-Z]+\d+", value.upper())

            # Formally register the newly discovered graph dependency connections
            for input_coord in extracted_inputs:
                cell.inputs.add(input_coord)
                self._get_or_create_cell(input_coord).dependents.add(coord)

        # 3. Check for illegal circular reference loops before rendering final calculations
        if self._has_circular_dependency(coord):
            # Rollback to safe defaults to prevent system crashes
            self.set_value(coord, "0")
            raise ValueError(
                f"⚠️ Circular Dependency detected at cell allocation payload: {coord}"
            )

        # 4. Success: Re-evaluate this cell and all downward downstream paths
        self._evaluate_cell_cascade(coord)

    def get_value(self, coord: str) -> float:
        """Retrieves the calculated scalar representation of a cell."""
        coord = coord.upper()
        if coord in self.matrix:
            return self.matrix[coord].calculated_value
        return 0.0

    def _has_circular_dependency(self, start_coord: str) -> bool:
        """Uses Depth-First Search (DFS) with node coloring to trap graph cycles."""
        visited = set()
        rec_stack = set()

        def dfs(curr: str) -> bool:
            visited.add(curr)
            rec_stack.add(curr)

            cell = self.matrix.get(curr)
            if cell:
                for neighbor in cell.inputs:
                    if neighbor not in visited:
                        if dfs(neighbor):
                            return True
                    elif neighbor in rec_stack:
                        return True  # Cycle trapped!

            rec_stack.remove(curr)
            return False

        return dfs(start_coord)

    def _evaluate_cell_cascade(self, start_coord: str) -> None:
        """Generates a Topological Sort to calculate dependencies in strict linear order."""
        order = []
        visited = set()

        # Build the proper topological compute path down the graph hierarchy
        def topological_sort_dfs(curr: str):
            visited.add(curr)
            cell = self.matrix.get(curr)
            if cell:
                for dep in cell.dependents:
                    if dep not in visited:
                        topological_sort_dfs(dep)
            order.append(curr)

        topological_sort_dfs(start_coord)
        order.reverse()  # Resolves execution line from parent nodes down to leaves

        # Execute calculations sequentially down our validated sorted trail
        for coord in order:
            self._compute_single_cell_value(self.matrix[coord])

    def _compute_single_cell_value(self, cell: Cell) -> None:
        """Parses raw text data or reduces a target SUM array list to a float scalar."""
        if not cell.raw_value.startswith("="):
            try:
                cell.calculated_value = float(cell.raw_value)
            except ValueError:
                cell.calculated_value = 0.0  # Safe fallback for illegal text items
            return

        # Handle Formula Computations (e.g., "=SUM(A1,B2)")
        if cell.raw_value.upper().startswith("=SUM"):
            total = 0.0
            for input_coord in cell.inputs:
                total += self.get_value(input_coord)
            cell.calculated_value = total
