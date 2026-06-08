import threading
import time
from enum import Enum
from typing import List, Set, Dict, Optional


class JobStatus(Enum):
    PENDING = 1
    RUNNING = 2
    COMPLETED = 3
    FAILED = 4


class Job:
    """Represents an executable unit of work demanding strict machine configurations."""

    def __init__(self, job_id: str, required_capabilities: Set[str], priority: int = 0):
        self.id = job_id
        self.required_capabilities = required_capabilities
        self.priority = priority  # Higher number means higher urgency
        self.status = JobStatus.PENDING
        self.assigned_machine_id: Optional[str] = None

    def execute(self) -> bool:
        """Simulates task logic running natively on a host node hardware."""
        print(f"⚙️ Running workload execution for Job {self.id}...")
        time.sleep(0.5)  # Simulate computing resources utilization
        return True

    # Reverse priority order for standard Python heapq (Min-Heap matches lower values,
    # so we invert comparisons to ensure high numbers exit the queue first)
    def __lt__(self, other: "Job") -> bool:
        return self.priority > other.priority


class WorkerMachine:
    """Represents an independent execution server node in the cluster."""

    def __init__(self, machine_id: str, capabilities: Set[str]):
        self.id = machine_id
        self.capabilities = capabilities
        self.active_jobs: Dict[str, Job] = {}
        self._lock = threading.Lock()

    def satisfies_requirements(self, required_capabilities: Set[str]) -> bool:
        """Requirement: Job may only run on a machine that has all required capabilities."""
        # Clean Pythonic set operations: checks if required capabilities are a subset of node traits
        return required_capabilities.issubset(self.capabilities)

    def run_job(self, job: Job) -> None:
        """Spawns an isolated hardware process thread executing the task."""
        with self._lock:
            self.active_jobs[job.id] = job
            job.status = JobStatus.RUNNING
            job.assigned_machine_id = self.id

        # In a massive distributed app, this runs via a thread pool or an async worker pipeline
        success = job.execute()

        with self._lock:
            del self.active_jobs[job.id]
            job.status = JobStatus.COMPLETED if success else JobStatus.FAILED
            print(f"✅ Job {job.id} terminated with status: {job.status.name}")


from abc import ABC, abstractmethod


class SchedulingStrategy(ABC):
    """Abstract Strategy interface for mapping matching workloads to hardware."""

    @abstractmethod
    def find_best_machine(
        self, job: Job, eligible_machines: List[WorkerMachine]
    ) -> Optional[WorkerMachine]:
        pass


class LeastLoadedStrategy(SchedulingStrategy):
    """
    Load-Balancing Strategy.
    Selects the qualified server currently executing the fewest active workloads.
    """

    def find_best_machine(
        self, job: Job, eligible_machines: List[WorkerMachine]
    ) -> Optional[WorkerMachine]:
        if not eligible_machines:
            return None
        # Finds the minimum node element keyed by its current workload length
        return min(eligible_machines, key=lambda machine: len(machine.active_jobs))


import queue


class JobScheduler:
    """The central orchestration master controlling resource matching loops."""

    def __init__(self, strategy: SchedulingStrategy):
        self.machines: List[WorkerMachine] = []
        self.strategy = strategy

        # Thread-safe heap broker storing incoming tasks prioritizing urgency indices
        self.job_queue: queue.PriorityQueue[Job] = queue.PriorityQueue()
        self._cluster_lock = threading.Lock()

        self.is_running = False

    def register_machine(self, machine: WorkerMachine):
        with self._cluster_lock:
            self.machines.append(machine)

    def submit_job(self, job: Job):
        """Asynchronous API entrypoint to ingest workloads smoothly."""
        print(f"📥 Received Job {job.id} [Priority: {job.priority}]")
        self.job_queue.put(job)

    def start_scheduler_loop(self):
        """Starts the central resource distribution clock cycle execution thread."""
        self.is_running = True
        threading.Thread(target=self._run_scheduling_cycle, daemon=True).start()

    def _run_scheduling_cycle(self):
        """Continuous internal background coordinator mapping tasks to machines."""
        while self.is_running:
            if self.job_queue.empty():
                time.sleep(0.1)  # Cool down step to prevent empty loop CPU burns
                continue

            # Fetch the highest priority job from our broker queue
            job = self.job_queue.get()

            with self._cluster_lock:
                # Filter down all machines to find those that fulfill the capabilities
                eligible_machines = [
                    m
                    for m in self.machines
                    if m.satisfies_requirements(job.required_capabilities)
                ]

            # Select the ideal target machine using our active scheduling algorithm strategy
            target_node = self.strategy.find_best_machine(job, eligible_machines)

            if target_node:
                # Hand off task asynchronously so it does not block the central scheduling loop
                threading.Thread(
                    target=target_node.run_job, args=(job,), daemon=True
                ).start()
            else:
                print(
                    f"⚠️ Scheduling Blocked: No node currently fulfills constraints for Job {job.id}. Re-queueing..."
                )
                self.job_queue.put(job)
                time.sleep(1)  # Delay buffer to allow machines to clear up or register
