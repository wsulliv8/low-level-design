#include "solution.hpp"

ParkingSpot* ParkingLevel::findAndOccupySpot(VehicleType type) {
  if (isFull(type)) return nullptr;

  auto spot = freeSpots[type].back();
  freeSpots[type].pop_back();

  return spot;
}

void ParkingLevel::returnSpot()