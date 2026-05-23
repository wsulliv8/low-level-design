#include <algorithm>
#include <deque>
#include <unordered_map>
#include <vector>
#include <string>
#include <memory>
#include <atomic>
#include <mutex>

enum class VehicleType {
  Car,
  Motorcycle, 
  Truck
};

struct FloorConfig {
  size_t numMotorcyle {5};
  size_t numCar {10};
  size_t numTruck {5};
};

class Vehicle {
protected:
  std::string licensePlate;

public:
  Vehicle(std::string lp) : licensePlate(std::move(lp)) {}
  virtual ~Vehicle() = default;

  virtual VehicleType getType() const = 0;
  const std::string& getLicensePlate() const {return licensePlate; }
};

class Motorcyle : public Vehicle {
public:
  using Vehicle::Vehicle;

  VehicleType getType() const override { return VehicleType::Motorcycle; };
};

class Car : public Vehicle {
public:
  using Vehicle::Vehicle;

  VehicleType getType() const override { return VehicleType::Car; };
};

class Truck : public Vehicle {
public:
  using Vehicle::Vehicle;

  VehicleType getType() const override { return VehicleType::Truck; };
};

class ParkingSpot {
private:
  std::string currentLicensePlate;
  VehicleType type;
  size_t floorNumber;

  inline static std::atomic<size_t> global_id {0};
  size_t id;
public:
  ParkingSpot(VehicleType t, size_t fn) : type(t), id(global_id++), floorNumber(fn), currentLicensePlate("") {}

  size_t getId() const { return id; }
  VehicleType getType() const {return type;}
  size_t getFloorNumber() const { return floorNumber; }

  bool isEmpty() const { return currentLicensePlate == ""; }
  void assignVehicle(const std::string& lp) { currentLicensePlate = lp; };
  void clearVehicle() { currentLicensePlate = ""; };
};

class ParkingLevel {
private:
  size_t floorNumber;

  std::vector<std::unique_ptr<ParkingSpot>> allSpots;
  std::unordered_map<VehicleType, std::vector<ParkingSpot*>> freeSpots;

  std::mutex m;
public:
  ParkingLevel(size_t fn, const FloorConfig& fc) : floorNumber(fn) {

    for (const auto& [type, count] : {
      std::make_pair(VehicleType::Motorcycle, fc.numMotorcyle), 
      std::make_pair(VehicleType::Car, fc.numCar),
      std::make_pair(VehicleType::Truck, fc.numTruck)
    }) {
      freeSpots[type].reserve(count);
      for (size_t i = 0; i < count; ++i){
        auto spot = std::make_unique<ParkingSpot>(type, floorNumber);
        freeSpots[type].push_back(spot.get());
        allSpots.push_back(std::move(spot));
      }
    }
  }

  bool isFull(VehicleType type) const { return freeSpots.at(type).empty(); }
  ParkingSpot* findAndOccupySpot(const Vehicle& vehicle);
  void returnSpot(ParkingSpot* spot);
};

class ParkingLot {
private:
  FloorConfig floorConfig;

  std::vector<std::unique_ptr<ParkingLevel>> levels;
  std::unordered_map<std::string, ParkingSpot*> occupiedSpots;
  
  std::mutex glob_m;
public:
  ParkingLot(size_t numLevels, const FloorConfig& fc) : floorConfig{fc} {
    levels.reserve(numLevels);
    for (auto i = 0; i < numLevels; ++i) {
      levels.push_back(std::make_unique<ParkingLevel>(i, floorConfig));
    }
  };

  bool parkVehicle(const Vehicle& vehicle);
  void removeVehicle(const std::string& licensePlate);
};