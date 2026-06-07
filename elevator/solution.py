"""
class ElevatorController:
    - elevators: List<Elevator>

    + ElevatorController()
    + requestElevator(floor, type) -> boolean
    + step() -> void

class Elevator:
    - currentFloor: int
    - direction: Direction        // UP, DOWN, IDLE
    - requests: Set<Request>

    + Elevator()
    + addRequest(request) -> boolean
    + step() -> void
    + getCurrentFloor() -> int
    + getDirection() -> Direction

class Request:
    - floor: int
    - type: RequestType

    + Request(floor, type)
    + getFloor() -> int
    + getType() -> RequestType

enum Direction:
    UP
    DOWN
    IDLE

enum RequestType:
    PICKUP_UP
    PICKUP_DOWN
    DESTINATION

"""

from enum import Enum


class RequestType(Enum):
    PICKUP_UP = 1
    PICKUP_DOWN = 2
    DESTINATION = 3


class Request:
    def __init__(self, floor: int, type: RequestType):
        self.floor = floor
        self.type = type

    def get_floor(self) -> int:
        return self.floor

    def get_type(self) -> RequestType:
        return self.type

    def __eq__(self, other):
        if not isinstance(other, Request):
            return False
        return self.floor == other.floor and self.type == other.type

    def __hash__(self):
        return hash((self.floor, self.type))


class Direction(Enum):
    UP = 1
    DOWN = 2
    IDLE = 3


class Elevator:
    def __init__(self):
        self.current_floor = 0
        self.direction = Direction.IDLE
        self.requests = set()

    def add_request(self, request):
        if request.get_floor() < 0 or request.get_floor() > 9:
            return False
        if request.get_floor() == self.current_floor:
            return True
        if request in self.requests:
            return False
        self.requests.add(request)
        return True

    def step(self):
        if not self.requests:
            self.direction = Direction.IDLE
            return

        if self.direction == Direction.IDLE:
            # Find nearest request to establish initial direction (deterministic)
            nearest = None
            min_distance = float("inf")

            for req in self.requests:
                distance = abs(req.get_floor() - self.current_floor)
                if distance < min_distance or (
                    distance == min_distance
                    and (nearest is None or req.get_floor() < nearest.get_floor())
                ):
                    min_distance = distance
                    nearest = req

            self.direction = (
                Direction.UP
                if nearest.get_floor() > self.current_floor
                else Direction.DOWN
            )

        pickup_type = (
            RequestType.PICKUP_UP
            if self.direction == Direction.UP
            else RequestType.PICKUP_DOWN
        )
        pickup_request = Request(self.current_floor, pickup_type)
        destination_request = Request(self.current_floor, RequestType.DESTINATION)

        if pickup_request in self.requests or destination_request in self.requests:
            self.requests.discard(pickup_request)
            self.requests.discard(destination_request)
            if not self.requests:
                self.direction = Direction.IDLE
            return

        if not self.has_requests_ahead(self.direction):
            self.direction = (
                Direction.DOWN if self.direction == Direction.UP else Direction.UP
            )
            return

        if self.direction == Direction.UP:
            self.current_floor += 1
        elif self.direction == Direction.DOWN:
            self.current_floor -= 1

    def has_requests_ahead(self, dir):
        for request in self.requests:
            if dir == Direction.UP and request.get_floor() > self.current_floor:
                return True
            if dir == Direction.DOWN and request.get_floor() < self.current_floor:
                return True
        return False

    def has_requests_at_or_beyond(self, floor, dir):
        for request in self.requests:
            if dir == Direction.UP and request.get_floor() >= floor:
                if request.get_type() in (
                    RequestType.PICKUP_UP,
                    RequestType.DESTINATION,
                ):
                    return True
            if dir == Direction.DOWN and request.get_floor() <= floor:
                if request.get_type() in (
                    RequestType.PICKUP_DOWN,
                    RequestType.DESTINATION,
                ):
                    return True
        return False

    def get_current_floor(self):
        return self.current_floor

    def get_direction(self):
        return self.direction


class ElevatorController:
    def __init__(self):
        self.elevators = [Elevator(), Elevator(), Elevator()]

    def request_elevator(self, floor, type):
        if floor < 0 or floor > 9:
            return False
        if type == RequestType.DESTINATION:
            return False

        request = Request(floor, type)
        best = self.select_best_elevator(request)
        if best is None:
            return False

        return best.add_request(request)

    def step(self):
        for elevator in self.elevators:
            elevator.step()

    def select_best_elevator(self, request):
        best = self.find_committed_to_floor(request)
        if best is not None:
            return best

        best = self.find_nearest_idle(request.get_floor())
        if best is not None:
            return best

        return self.find_nearest(request.get_floor())

    def find_committed_to_floor(self, request):
        floor = request.get_floor()
        direction = (
            Direction.UP
            if request.get_type() == RequestType.PICKUP_UP
            else Direction.DOWN
        )

        nearest = None
        min_distance = float("inf")

        for e in self.elevators:
            if e.get_direction() != direction:
                continue

            if (direction == Direction.UP and e.get_current_floor() > floor) or (
                direction == Direction.DOWN and e.get_current_floor() < floor
            ):
                continue

            if not e.has_requests_at_or_beyond(floor, direction):
                continue

            distance = abs(e.get_current_floor() - floor)
            if distance < min_distance:
                min_distance = distance
                nearest = e

        return nearest

    def find_nearest_idle(self, floor):
        nearest = None
        min_distance = float("inf")

        for e in self.elevators:
            if e.get_direction() != Direction.IDLE:
                continue

            distance = abs(e.get_current_floor() - floor)
            if distance < min_distance:
                min_distance = distance
                nearest = e

        return nearest

    def find_nearest(self, floor):
        nearest = self.elevators[0]
        min_distance = abs(self.elevators[0].get_current_floor() - floor)

        for e in self.elevators:
            distance = abs(e.get_current_floor() - floor)
            if distance < min_distance:
                min_distance = distance
                nearest = e

        return nearest
