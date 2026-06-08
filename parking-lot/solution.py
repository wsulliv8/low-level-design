import threading
from enum import Enum
from typing import List, Optional, Dict


class VehicleType(Enum):
    CAR = 1
    TRUCK = 2
    BIKE = 3


class Vehicle:
    def __init__(self, license_plate: str, vehicle_type: VehicleType):
        self.license_plate = license_plate
        self.vehicle_type = vehicle_type


class Ticket:
    """Receipt object mapping a parked vehicle to its exact position."""

    def __init__(
        self, ticket_id: str, license_plate: str, floor_id: int, row: int, col: int
    ):
        self.id = ticket_id
        self.license_plate = license_plate
        self.floor_id = floor_id
        self.row = row
        self.col = col


class ParkingSpot:
    """A physical space in the lot that accepts a matching vehicle type."""

    def __init__(self, row: int, col: int, spot_type: VehicleType):
        self.row = row
        self.col = col
        self.spot_type = spot_type
        self.is_occupied: bool = False
        self.parked_vehicle: Optional[Vehicle] = None
        self._lock = threading.Lock()  # Atomic locking at the spot level

    def assign_vehicle(self, vehicle: Vehicle) -> bool:
        with self._lock:
            if self.is_occupied or self.spot_type != vehicle.vehicle_type:
                return False
            self.parked_vehicle = vehicle
            self.is_occupied = True
            return True

    def remove_vehicle(self) -> None:
        with self._lock:
            self.parked_vehicle = None
            self.is_occupied = False


class ParkingFloor:
    """Manages a 2D matrix of spots and monitors live floor capacities."""

    def __init__(self, floor_id: int, rows: int, cols: int):
        self.id = floor_id
        self.grid: List[List[ParkingSpot]] = []

        # In-memory thread-safe counters to avoid full grid scans for counts
        self.free_counts: Dict[VehicleType, int] = {vt: 0 for vt in VehicleType}
        self._floor_lock = threading.Lock()

        self._initialize_grid(rows, cols)

    def _initialize_grid(self, rows: int, cols: int):
        """Builds the 2D grid layout. (e.g., assigning rows for bikes vs trucks)"""
        for r in range(rows):
            row_spots = []
            for c in range(cols):
                # Simple rule: first row for trucks, middle for cars, rest for bikes
                if r == 0:
                    spot_type = VehicleType.TRUCK
                elif r < rows // 2:
                    spot_type = VehicleType.CAR
                else:
                    spot_type = VehicleType.BIKE

                row_spots.append(ParkingSpot(r, c, spot_type))
                self.free_counts[spot_type] += 1
            self.grid.append(row_spots)

    def update_count(self, spot_type: VehicleType, delta: int):
        """Thread-safe counter adjustments during park/unpark phases."""
        with self._floor_lock:
            self.free_counts[spot_type] += delta

    def get_free_spots_count(self, spot_type: VehicleType) -> int:
        with self._floor_lock:
            return self.free_counts[spot_type]


from abc import ABC, abstractmethod


class ParkingStrategy(ABC):
    """Abstract Strategy interface for hunting valid parking spaces."""

    @abstractmethod
    def find_spot(
        self, vehicle: Vehicle, floors: List[ParkingFloor]
    ) -> Optional[ParkingSpot]:
        pass


class NaturalOrderStrategy(ParkingStrategy):
    """Fills spots chronologically from lowest floor up, row by row."""

    def find_spot(
        self, vehicle: Vehicle, floors: List[ParkingFloor]
    ) -> Optional[ParkingSpot]:
        for floor in floors:
            # Short-circuit optimize: skip floor if counter shows no room for this type
            if floor.get_free_spots_count(vehicle.vehicle_type) == 0:
                continue

            for row in floor.grid:
                for spot in row:
                    if spot.spot_type == vehicle.vehicle_type and not spot.is_occupied:
                        return spot
        return None


class ParkingLot:
    """The main coordinator system managing inputs, outputs, and indexing."""

    def __init__(self, strategy: ParkingStrategy):
        self.floors: List[ParkingFloor] = []
        self.strategy = strategy

        # O(1) Search Index mapping license plates to active tracking tickets
        self.vehicle_registry: Dict[str, Ticket] = {}
        self._registry_lock = threading.Lock()
        self._ticket_counter = 0

    def add_floor(self, floor: ParkingFloor):
        self.floors.append(floor)

    def set_strategy(self, strategy: ParkingStrategy):
        self.strategy = strategy

    def park_vehicle(self, vehicle: Vehicle) -> Optional[Ticket]:
        # 1. Ask the strategy to find an available node spot
        spot = self.strategy.find_spot(vehicle, self.floors)
        if not spot:
            print(f"❌ Parking Denied: Lot full for {vehicle.vehicle_type.name}")
            return None

        # 2. Try to lock and acquire the target spot
        # (Find target floor instance to update counts later)
        target_floor = next(
            f for f in self.floors if spot in [s for r in f.grid for s in r]
        )

        if spot.assign_vehicle(vehicle):
            target_floor.update_count(vehicle.vehicle_type, -1)

            # 3. Mint registration ticket
            with self._registry_lock:
                self._ticket_counter += 1
                ticket = Ticket(
                    ticket_id=f"TKT-{self._ticket_counter}",
                    license_plate=vehicle.license_plate,
                    floor_id=target_floor.id,
                    row=spot.row,
                    col=spot.col,
                )
                self.vehicle_registry[vehicle.license_plate] = ticket

            print(
                f"🚗 Parked {vehicle.license_plate} at Floor {target_floor.id} -> Spot ({spot.row},{spot.col})"
            )
            return ticket

        return None

    def unpark_vehicle(self, license_plate: str) -> bool:
        with self._registry_lock:
            ticket = self.vehicle_registry.get(license_plate)
            if not ticket:
                print(
                    f"⚠️ Search Mismatch: Vehicle {license_plate} not found in tracking system."
                )
                return False
            del self.vehicle_registry[license_plate]

        # Fetch targets based on recorded coordinates
        floor = self.floors[ticket.floor_id]
        spot = floor.grid[ticket.row][ticket.col]

        spot.remove_vehicle()
        floor.update_count(spot.spot_type, 1)
        print(
            f"✅ Unparked {license_plate}. Space reclaimed at Floor {floor.id} -> Spot ({spot.row},{spot.col})"
        )
        return True

    def search_vehicle(self, license_plate: str) -> Optional[Ticket]:
        """Requirement: Search parked vehicles by vehicle number."""
        with self._registry_lock:
            # Achieved instantly in O(1) via hash table lookups
            return self.vehicle_registry.get(license_plate)
