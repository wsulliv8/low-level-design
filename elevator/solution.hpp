/*
struct config
- numElevators
- capacity
- maxFloor

enum direction
  up, down, idle 

enum requestSource
  Internal, external

class Elevator
- set upRequests
- set downRequests (sorted decreasing)
- mutex
- level
- capacity
- numPeople
- Elevator State state
- changeState (using move)
- step()
- addInternal()
- friend classes with ElevatorStates so they can access requests

class ElevatorSystem 
- vector Elevator 
- q requests
- mutex
- processExternal()
  - calculateCost()

class virtual ElevatorState 
  Movingup, down, idle
- processMotion
- getState
*/
#include <cstddef>
#include <memory>
#include <set>
#include <mutex>

struct ElevatorConfig {
  size_t numElevators {4};
  size_t maxFloor {10};
  float maxCapacity {1000.0f};
};

enum class ElevatorDirection {
  Idle,
  Down,
  Up
};

enum class RequestSource {
  Internal,
  External
};

class Elevator;

class ElevatorState {
public:
  virtual ~ElevatorState() = default;
  
  virtual ElevatorDirection getState() const = 0;
  virtual void processMotion(Elevator& elevator) = 0;
};

class MovingUpState : ElevatorState {
  public:
    ElevatorDirection getState() const override {return ElevatorDirection::Up;}
    void processMotion(Elevator& elevator) override;
};

class MovingDownState : ElevatorState {
  public:
    ElevatorDirection getState() const override {return ElevatorDirection::Down;}
    void processMotion(Elevator& elevator) override;
};

class IdleState : ElevatorState {
  public:
    ElevatorDirection getState() const override {return ElevatorDirection::Idle;}
    void processMotion(Elevator& elevator) override;
};
/* 
class Elevator
- set upRequests
- set downRequests (sorted decreasing)
- mutex
- level
- capacity
- numPeople
- Elevator State state
- changeState (using move)
- step()
- addInternal()
- friend classes with ElevatorStates so they can access requests
 */

class Elevator {
public:
  size_t level;
  size_t maxCapacity;
  size_t currentWeight;

  std::set<size_t> upRequests;
  std::set<size_t> downRequests;

  std::unique_ptr<ElevatorState> state;

  std::mutex m;
private:
  Elevator(const ElevatorConfig& config) :
    level(0), maxCapacity(config.maxCapacity), currentWeight(0), 
};