#include <condition_variable>
#include <cstddef>
#include <deque>
#include <functional>
#include <memory>
#include <mutex>
#include <set>
#include <vector>

struct ElevatorConfig {
  size_t numElevators{4};
  size_t maxFloor{10};
  float maxCapacity{1000.0f};
};

enum class ElevatorDirection { Idle, Down, Up };

enum class RequestSource { Internal, External };

class Elevator;

class ElevatorState {
public:
  virtual ~ElevatorState() = default;

  virtual ElevatorDirection getState() const = 0;
  virtual void processMotion(Elevator &elevator) = 0;
};

class MovingUpState : public ElevatorState {
public:
  ElevatorDirection getState() const override { return ElevatorDirection::Up; }
  void processMotion(Elevator &elevator) override;
};

class MovingDownState : public ElevatorState {
public:
  ElevatorDirection getState() const override {
    return ElevatorDirection::Down;
  }
  void processMotion(Elevator &elevator) override;
};

class IdleState : public ElevatorState {
public:
  ElevatorDirection getState() const override {
    return ElevatorDirection::Idle;
  }
  void processMotion(Elevator &elevator) override;
};

class Elevator {
private:
  size_t level;
  const float maxCapacity;
  float currentWeight;

  std::set<size_t> upRequests;
  std::set<size_t, std::greater<size_t>> downRequests;

  std::unique_ptr<ElevatorState> state;

  std::mutex m;
  std::condition_variable cv; // for waiting while idle
public:
  Elevator(const float maxCapacity)
      : level(0), maxCapacity(maxCapacity), currentWeight(0) {
    state = std::make_unique<IdleState>();
  };

  size_t getLevel() const { return level; }
  bool isOverloaded() const { return currentWeight > maxCapacity; }
  ElevatorDirection getDirection() const { return state->getState(); }

  void changeState(std::unique_ptr<ElevatorState>);
  void run();
  void addInternal(size_t floor);

  friend class IdleState;
  friend class MovingUpState;
  friend class MovingDownState;
};

struct ExternalRequest {
  size_t floor{1};
  ElevatorDirection direction{ElevatorDirection::Up};
};

class ElevatorSystem {
private:
  ElevatorConfig config;

  std::vector<std::unique_ptr<Elevator>> elevators;
  std::deque<ExternalRequest> requests;

  std::mutex m;

public:
  ElevatorSystem(const ElevatorConfig &c) : config(c) {
    elevators.reserve(config.numElevators);
    for (size_t i = 0; i < config.numElevators; ++i) {
      elevators.emplace_back(std::make_unique<Elevator>(config.maxCapacity));
    }
  }

  void processExternal(const ExternalRequest &request);

private:
  int calculateCost(const Elevator &elevator, const ExternalRequest &request);
};