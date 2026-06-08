import threading
from enum import Enum
from typing import List, Dict, Set


class SeatStatus(Enum):
    AVAILABLE = 1
    BOOKED = 2


class Movie:
    def __init__(self, movie_id: str, title: str, language: str):
        self.id = movie_id
        self.title = title
        self.language = language


class Seat:
    """The atomic structural unit of inventory inside a cinema screen."""

    def __init__(self, seat_id: str):
        self.id = seat_id
        self.status = SeatStatus.AVAILABLE
        self._lock = (
            threading.Lock()
        )  # Fine-grained lock per seat to prevent double booking

    def reserve(self) -> bool:
        with self._lock:
            if self.status == SeatStatus.BOOKED:
                return False
            self.status = SeatStatus.BOOKED
            return True

    def cancel(self) -> None:
        with self._lock:
            self.status = SeatStatus.AVAILABLE


class Cinema:
    def __init__(self, cinema_id: str, name: str, city: str):
        self.id = cinema_id
        self.name = name
        self.city = city


from abc import ABC, abstractmethod


class Show:
    """Represents a specific time slot mapping a Movie to a Cinema."""

    def __init__(
        self,
        show_id: str,
        movie: Movie,
        cinema: Cinema,
        start_time: str,
        total_seats: int,
    ):
        self.id = show_id
        self.movie = movie
        self.cinema = cinema
        self.start_time = start_time
        # Generate physical inventory layout
        self.seats: Dict[str, Seat] = {
            f"Seat-{i}": Seat(f"Seat-{i}") for i in range(1, total_seats + 1)
        }


class CatalogObserver(ABC):
    """Abstract Observer interface."""

    @abstractmethod
    def update(self, show: Show) -> None:
        pass


class ShowCatalog:
    """The Subject (Observable): Manages mutations and notifies search caches."""

    def __init__(self):
        self._shows: Dict[str, Show] = {}
        self._observers: List[CatalogObserver] = []
        self._lock = threading.Lock()

    def register_observer(self, observer: CatalogObserver):
        self._observers.append(observer)

    def add_show(self, show: Show):
        with self._lock:
            self._shows[show.id] = show

        # Broadcast event to all listening search components
        self._notify_observers(show)

    def _notify_observers(self, show: Show):
        for observer in self._observers:
            observer.update(show)


# --- Concrete Observers (Read-Optimized Search Indices) ---


class CinemaSearchIndex(CatalogObserver):
    """Requirement: List all cinemas in a city which are displaying a particular movie."""

    def __init__(self):
        # Nested Index structure: { city: { movie_title: Set[Cinema] } }
        self._index: Dict[str, Dict[str, Set[Cinema]]] = {}
        self._lock = threading.Lock()

    def update(self, show: Show) -> None:
        """Invoked automatically via Observer broadcast."""
        city = show.cinema.city.lower()
        movie_title = show.movie.title.lower()

        with self._lock:
            if city not in self._index:
                self._index[city] = {}
            if movie_title not in self._index[city]:
                self._index[city][movie_title] = set()

            self._index[city][movie_title].add(show.cinema)

    def search_cinemas(self, city: str, movie_title: str) -> List[Cinema]:
        """Provides instant O(1) query speeds by bypassing full database sweeps."""
        return list(self._index.get(city.lower(), {}).get(movie_title.lower(), []))


class ShowSearchIndex(CatalogObserver):
    """Requirement: Fetch list of all shows in a cinema hall displaying a particular movie."""

    def __init__(self):
        # Nested Index structure: { cinema_id: { movie_title: List[Show] } }
        self._index: Dict[str, Dict[str, List[Show]]] = {}
        self._lock = threading.Lock()

    def update(self, show: Show) -> None:
        """Invoked automatically via Observer broadcast."""
        cinema_id = show.cinema.id
        movie_title = show.movie.title.lower()

        with self._lock:
            if cinema_id not in self._index:
                self._index[cinema_id] = {}
            if movie_title not in self._index[cinema_id]:
                self._index[cinema_id][movie_title] = []

            self._index[cinema_id][movie_title].append(show)

    def search_shows(self, cinema_id: str, movie_title: str) -> List[Show]:
        return self._index.get(cinema_id, {}).get(movie_title.lower(), [])


class BookingEngine:
    """Manages transactional user ticket lifecycle operations securely."""

    def __init__(self):
        self.bookings: Dict[str, List[Seat]] = {}
        self._lock = threading.Lock()
        self._booking_counter = 0

    def book_tickets(
        self, user_id: str, show: Show, seat_ids: List[str]
    ) -> Optional[str]:
        """Atomically locks and reserves a collection of seats for a customer."""
        target_seats = [show.seats[sid] for sid in seat_ids if sid in show.seats]

        # Guard against invalid inputs
        if len(target_seats) != len(seat_ids):
            return None

        # Step 1: Attempt to acquire locks sequentially
        reserved_seats = []
        for seat in target_seats:
            if seat.reserve():
                reserved_seats.append(seat)
            else:
                # ROLLBACK MECHANISM: If even 1 seat fails, free previous ones to prevent partial booking
                for r_seat in reserved_seats:
                    r_seat.cancel()
                print(f"❌ Transaction Terminated: Seat {seat.id} is already occupied.")
                return None

        # Step 2: Mint Booking ID upon full success
        with self._lock:
            self._booking_counter += 1
            booking_id = f"BKID-{self._booking_counter}"
            self.bookings[booking_id] = reserved_seats

        print(
            f"🎟️ Successfully booked {len(seat_ids)} seats under Booking Reference: {booking_id}"
        )
        return booking_id

    def cancel_booking(self, booking_id: str) -> bool:
        with self._lock:
            if booking_id not in self.bookings:
                print("⚠️ Action Aborted: Booking reference record not found.")
                return False
            seats_to_free = self.bookings.pop(booking_id)

        for seat in seats_to_free:
            seat.cancel()

        print(
            f"✅ Cancelled Booking {booking_id}. Seats returned to available inventory pools."
        )
        return True
