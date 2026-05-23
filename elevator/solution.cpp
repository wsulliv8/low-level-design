#include "solution.hpp"
#include <cmath>
#include <cstddef>
#include <cstdlib>
#include <limits>
#include <memory>
#include <mutex>

void Elevator::changeState(std::unique_ptr<ElevatorState> nextState) {
  state = std::move(nextState);
}

void MovingUpState::processMotion(Elevator &elevator) {
  if (elevator.upRequests.contains(elevator.level)) {
    elevator.upRequests.erase(elevator.level);
    return;
  }

  if (!elevator.upRequests.empty() &&
      *elevator.upRequests.rbegin() > elevator.level) {
    elevator.level++;
  } else {
    if (!elevator.downRequests.empty()) {
      elevator.changeState(std::make_unique<MovingDownState>());
    } else {
      elevator.changeState(std::make_unique<IdleState>());
    }
  }
}

void MovingDownState::processMotion(Elevator &elevator) {
  if (elevator.downRequests.contains(elevator.level)) {
    elevator.downRequests.erase(elevator.level);
    return;
  }

  if (!elevator.downRequests.empty() &&
      *elevator.downRequests.rbegin() < elevator.level) {
    elevator.level--;
  } else {
    if (!elevator.upRequests.empty()) {
      elevator.changeState(std::make_unique<MovingUpState>());
    } else {
      elevator.changeState(std::make_unique<IdleState>());
    }
  }
}

void IdleState::processMotion(Elevator &elevator) {
  if (!elevator.upRequests.empty()) {
    elevator.changeState(std::make_unique<MovingUpState>());
  } else {
    elevator.changeState(std::make_unique<MovingDownState>());
  }
}

void Elevator::run() {
  while (true) {
    std::unique_lock<std::mutex> lock(m);

    cv.wait(lock, [&] {
      return (!upRequests.empty() || !downRequests.empty()) && !isOverloaded();
    });

    state->processMotion(*this);
  }
}

void Elevator::addInternal(size_t requestedLevel) {
  std::scoped_lock<std::mutex> lock(m);
  if (requestedLevel == level)
    return;

  if (requestedLevel > level) {
    upRequests.insert(requestedLevel);
  } else {
    downRequests.insert(requestedLevel);
  }

  if (state->getState() == ElevatorDirection::Idle) {
    cv.notify_one();
  }
}

void ElevatorSystem::processExternal(const ExternalRequest &request) {
  std::scoped_lock<std::mutex> lock(m);

  int cost = std::numeric_limits<int>::max();
  size_t elevator_index = 0;

  for (size_t i = 0; i < elevators.size(); i++) {
    auto newCost = calculateCost(*elevators[i], request);
    if (newCost < cost) {
      elevator_index = i;
      cost = newCost;
    }
  }
  elevators[elevator_index]->addInternal(request.floor);
}

int ElevatorSystem::calculateCost(const Elevator &elevator,
                                  const ExternalRequest &request) {
  auto distance = std::abs(static_cast<int>(elevator.getLevel()) -
                           static_cast<int>(request.floor));

  if (elevator.getDirection() == ElevatorDirection::Idle)
    return distance;

  if (elevator.getDirection() == request.direction) {
    if (request.direction == ElevatorDirection::Up &&
        elevator.getLevel() <= request.floor) {
      return distance;
    } else if (request.direction == ElevatorDirection::Down &&
               elevator.getLevel() >= request.floor) {
      return distance;
    }
  }
  return distance + 1000;
}