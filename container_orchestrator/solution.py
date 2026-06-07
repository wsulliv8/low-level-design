import threading
from abc import ABC, abstractmethod
from typing import List, Optional, Dict


class Container:
    """Represents an isolated application instance demanding specific resources."""

    def __init__(self, container_id: str, cpu_req: int, memory_req: int):
        self.id = container_id
        self.cpu_req = cpu_req
        self.memory_req = memory_req


class Machine:
    """Represents a host server machine (e.g., EC2 instance) managing its resources."""

    def __init__(self, machine_id: str, total_cpu: int, total_memory: int):
        self.id = machine_id
        self.total_cpu = total_cpu
        self.total_memory = total_memory

        # Track available headroom
        self.available_cpu = total_cpu
        self.available_memory = total_memory

        # Container Tracking
        self.containers: Dict[str, Container] = {}
        self._lock = (
            threading.Lock()
        )  # Protects machine state from concurrent mutations

    def can_fit(self, container: Container) -> bool:
        """Checks if the machine has enough remaining capacity."""
        with self._lock:
            return (
                self.available_cpu >= container.cpu_req
                and self.available_memory >= container.memory_req
            )

    def deploy_container(self, container: Container) -> bool:
        """Allocates resources and boots up the container securely."""
        with self._lock:
            if (
                self.available_cpu < container.cpu_req
                or self.available_memory < container.memory_req
            ):
                return False

            self.containers[container.id] = container
            self.available_cpu -= container.cpu_req
            self.available_memory -= container.memory_req
            return True

    def terminate_container(self, container_id: str) -> bool:
        """Stops the container and reclaims its resources safely."""
        with self._lock:
            if container_id not in self.containers:
                return False

            container = self.containers.pop(container_id)
            self.available_cpu += container.cpu_req
            self.available_memory += container.memory_req
            return True


class PlacementStrategy(ABC):
    """Abstract Strategy interface for selecting a target host machine."""

    @abstractmethod
    def select_machine(
        self, container: Container, machines: List[Machine]
    ) -> Optional[Machine]:
        pass


class BestFitStrategy(PlacementStrategy):
    """
    Resource Optimization Strategy.
    Finds the machine that will have the LEAST left-over CPU after placement.
    Packs containers densely to save infrastructure costs.
    """

    def select_machine(
        self, container: Container, machines: List[Machine]
    ) -> Optional[Machine]:
        best_machine = None
        min_remaining_cpu = float("inf")

        for machine in machines:
            if machine.can_fit(container):
                # How much CPU space is left over if we place it here?
                remaining_cpu = machine.available_cpu - container.cpu_req
                if remaining_cpu < min_remaining_cpu:
                    min_remaining_cpu = remaining_cpu
                    best_machine = machine

        return best_machine


class RoundRobinStrategy(PlacementStrategy):
    """
    High-Availability Strategy.
    Cycles through available valid machines evenly to balance the load across the cluster.
    """

    def __init__(self):
        self._current_index = 0

    def select_machine(
        self, container: Container, machines: List[Machine]
    ) -> Optional[Machine]:
        if not machines:
            return None

        num_machines = len(machines)
        # Attempt to scan all machines starting from where we last left off
        for _ in range(num_machines):
            candidate = machines[self._current_index]
            # Advance index tracking immediately
            self._current_index = (self._current_index + 1) % num_machines

            if candidate.can_fit(container):
                return candidate

        return None


class ContainerOrchestrator:
    """The central management system controlling cluster orchestration."""

    def __init__(self, strategy: PlacementStrategy):
        self.machines: List[Machine] = []
        self.strategy: PlacementStrategy = strategy
        self._global_lock = threading.Lock()  # Protects the cluster inventory topology

    def add_machine(self, machine: Machine):
        with self._global_lock:
            self.machines.append(machine)

    def set_strategy(self, strategy: PlacementStrategy):
        """Allows dynamically swapping algorithms on a live production cluster!"""
        with self._global_lock:
            self.strategy = strategy

    def schedule_container(self, container: Container) -> bool:
        """Determines placement using the active strategy and provisions the app."""
        with self._global_lock:
            target_machine = self.strategy.select_machine(container, self.machines)

        if not target_machine:
            print(
                f"❌ Allocation Failed: No machine can accommodate Container {container.id}"
            )
            return False

        success = target_machine.deploy_container(container)
        if success:
            print(
                f"🚀 Deployed Container {container.id} on Machine {target_machine.id}"
            )
        return success

    def stop_container(self, container_id: str) -> bool:
        """Locates and turns off a targeted container across the entire cluster."""
        with self._global_lock:
            for machine in self.machines:
                if machine.terminate_container(container_id):
                    print(
                        f"🛑 Stopped Container {container_id} on Machine {machine.id}"
                    )
                    return True
        print(f"⚠️ Container {container_id} not found anywhere in the cluster.")
        return False
