from .map_validator import MapValidator
from .hub import Hub, Connection
from .metadata import Zone
import heapq

class Algorythme():
    def __init__(self, map: MapValidator):
        self.map = map

        self.all_hubs: list[Hub] = self.map.hub[:]
        if self.map.start_hub is not None:
            self.all_hubs.append(self.map.start_hub)
        if self.map.end_hub is not None:
            self.all_hubs.append(self.map.end_hub)

    def dijkstra(self, excluded: set[str] = set()) -> list[str]:
        if excluded is None:
            excluded = set()
        costs = {
            Zone.normal: 1,
            Zone.priority: 0.99,
            Zone.restricted: 2,
            Zone.blocked: float('inf')
        }
        
        self.tab = {}
        for h in self.all_hubs:
            self.tab[h.name] = float('inf')
        self.tab[self.map.start_hub.name] = 0

        parents = {}
        for h in self.tab:
            parents[h] = None

        heap = []
        heapq.heappush(heap, (0, self.map.start_hub.name))
        visited = set()

        while heap:
            h = heapq.heappop(heap)
            if h[1] in visited:
                continue
            visited.add(h[1])
            if h[1] == self.map.end_hub.name:
                break

            for c in self.map.connections:
                if c.zone1.name == h[1]:
                    n = c.zone2
                elif c.zone2.name == h[1]:
                    n = c.zone1
                else:
                    continue
                if n.metadata.zone == Zone.blocked:
                    continue
                if n.name in excluded:
                    continue
                new_cost = h[0] + costs[n.metadata.zone]

                if new_cost < self.tab[n.name]:
                    self.tab[n.name] = new_cost
                    parents[n.name] = h[1]
                    heapq.heappush(heap, (new_cost, n.name))

        if parents[self.map.end_hub.name] is None:
            return []
        h_name = self.map.end_hub.name
        path = []
        while h_name != self.map.start_hub.name:
            path.append(h_name)
            h_name = parents[h_name]
        path.append(self.map.start_hub.name)
        path = path[::-1]
        return path

    def find_best_paths(self, k: int) -> list[list[str]]:
        paths = []
        excluded: set[str] = set()

        while len(paths) < k:
            path = self.dijkstra(excluded)
            if not path:
                break

            intermediates = set(path[1:-1])
            
            bottleneck_zones = {
                name for name in intermediates
                for h in self.all_hubs
                if h.name == name and h.metadata.max_drones > 1
            }
            strict_intermediates = intermediates - bottleneck_zones

            is_disjoint = all(
                strict_intermediates.isdisjoint(
                    set(p[1:-1]) - bottleneck_zones
                )
                for p in paths
            )

            if not is_disjoint:
                break

            paths.append(path)
            for zone in intermediates:
                hub = next((h for h in self.all_hubs if h.name == zone), None)
                if hub is not None and hub.metadata.max_drones == 1:
                    excluded.add(zone)

        if not paths:
            return []

        while len(paths) < k:
            paths.append(paths[0])

        return paths