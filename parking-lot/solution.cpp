#include "solution.hpp"
#include <mutex>

ParkingSpot* ParkingLevel::findAndOccupySpot(const Vehicle& vehicle) {
  std::lock_guard<std::mutex> lock(m);

  auto type = vehicle.getType();
  if (isFull(type)) return nullptr;

  auto spot = freeSpots[type].back();
  freeSpots[type].pop_back();

  spot->assignVehicle(vehicle.getLicensePlate());

  return spot;
}

void ParkingLevel::returnSpot(ParkingSpot* spot) {
  if (!spot) return;

  std::lock_guard<std::mutex> lock(m);

  spot->clearVehicle();
  freeSpots[spot->getType()].push_back(spot);
}

bool ParkingLot::parkVehicle(const Vehicle& vehicle) {
  {
    std::lock_guard<std::mutex> lock(glob_m);
    if (occupiedSpots.find(vehicle.getLicensePlate()) != occupiedSpots.end()){
      return false;
    }
  }

  for (auto& l : levels) {
    auto spot = l->findAndOccupySpot(vehicle);
    if (spot) {
      std::lock_guard<std::mutex> lock(glob_m);
      occupiedSpots[vehicle.getLicensePlate()] = spot;
      return true;
    }
  }
  return false;
}

void ParkingLot::removeVehicle(const std::string& licensePlate) {
  std::lock_guard<std::mutex> lock(glob_m);
  auto it = occupiedSpots.find(licensePlate);
  if (it == occupiedSpots.end()) return;

  auto spot = it -> second;
  levels[spot->getFloorNumber()]->returnSpot(spot);
  occupiedSpots.erase(it);
}

int main() {
  return 0;
}