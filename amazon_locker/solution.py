"""

class Locker:
    - compartments: Compartment[]
    - accessTokenMapping: Map<string, AccessToken>

    + Locker(compartments)
    + depositPackage(size) -> string | error
    + pickup(tokenCode) -> void | error
    + openExpiredCompartments() -> void

class AccessToken:
    - code: string
    - expiration: timestamp
    - compartment: Compartment

    + AccessToken(code, expiration, compartment)
    + isExpired() -> boolean
    + getCompartment() -> Compartment
    + getCode() -> string

class Compartment:
    - size: Size
    - occupied: boolean

    + Compartment(size)
    + getSize() -> Size
    + isOccupied() -> boolean
    + markOccupied() -> void
    + markFree() -> void
    + open() -> void

enum Size:
    SMALL
    MEDIUM
    LARGE

"""

from datetime import datetime, timedelta
from typing import Optional
import random
from enum import Enum


class Size(Enum):
    SMALL = "SMALL"
    MEDIUM = "MEDIUM"
    LARGE = "LARGE"


class Compartment:
    def __init__(self, size):
        self.size = size
        self.occupied = False

    def get_size(self):
        return self.size

    def is_occupied(self) -> bool:
        return self.occupied

    def mark_occupied(self) -> None:
        self.occupied = True

    def mark_free(self) -> None:
        self.occupied = False

    def open(self) -> None:
        pass


class AccessToken:
    def __init__(self, code: str, expiration: datetime, compartment):
        self.code = code
        self.expiration = expiration
        self.compartment = compartment

    def is_expired(self) -> bool:
        return datetime.now() >= self.expiration

    def get_compartment(self):
        return self.compartment

    def get_code(self) -> str:
        return self.code


class Locker:
    def __init__(self, compartments: list["Compartment"]):
        self.compartments = compartments
        self.access_token_mapping: dict[str, "AccessToken"] = {}

    def deposit_package(self, size: "Size") -> str:
        compartment = self._get_available_compartment(size)
        if compartment is None:
            raise Exception(f"No available compartment of size {size}")

        compartment.open()
        compartment.mark_occupied()
        access_token = self._generate_access_token(compartment)
        self.access_token_mapping[access_token.get_code()] = access_token

        return access_token.get_code()

    def pickup(self, token_code: str) -> None:
        if not token_code:
            raise Exception("Invalid access token code")

        access_token = self.access_token_mapping.get(token_code)
        if access_token is None:
            raise Exception("Invalid access token code")

        if access_token.is_expired():
            raise Exception("Access token has expired")

        compartment = access_token.get_compartment()
        compartment.open()
        self._clear_deposit(access_token)

    def open_expired_compartments(self) -> None:
        for access_token in self.access_token_mapping.values():
            if access_token.is_expired():
                compartment = access_token.get_compartment()
                compartment.open()

    def _get_available_compartment(self, size: "Size") -> Optional["Compartment"]:
        for c in self.compartments:
            if c.get_size() == size and not c.is_occupied():
                return c
        return None

    def _generate_access_token(self, compartment: "Compartment") -> "AccessToken":
        code = f"{random.randint(0, 999999):06d}"
        expiration = datetime.now() + timedelta(days=7)
        return AccessToken(code, expiration, compartment)

    def _clear_deposit(self, access_token: "AccessToken") -> None:
        compartment = access_token.get_compartment()
        compartment.mark_free()
        self.access_token_mapping.pop(access_token.get_code(), None)
