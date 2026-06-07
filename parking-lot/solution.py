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
