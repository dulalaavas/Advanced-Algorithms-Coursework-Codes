import math

class City:
    """City record. `distance` is Euclidean distance from ORIGIN, used as the Min-Heap priority."""
    ORIGIN = (0.0, 0.0)

    def __init__(self, city_id, name, latitude, longitude, population):
        self.city_id = city_id
        self.name = name
        self.latitude = latitude
        self.longitude = longitude
        self.population = population
        self.distance = math.dist((latitude, longitude), City.ORIGIN)

    def __repr__(self):
        return f"City({self.city_id}, {self.name}, dist={self.distance:.2f})"
