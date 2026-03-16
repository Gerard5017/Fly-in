from .map_validator import MapValidator
from .hub import Hub
from .metadata import Zone
import heapq


class Algorythme():
    """Pathfinding engine for the drone simulation.

    Computes one or several shortest paths through the map graph
    using Dijkstra's algorithm, with zone-based cost weights.

    Attributes:
        map: The validated map used as the graph source.
        all_hubs: Flat list of every hub including start and end.
    """

    def __init__(self, map: MapValidator) -> None:
        """Initialize the algorithm with a validated map.

        Args:
            map: A MapValidator instance containing hubs and connections.
        """
        self.map = map

        self.all_hubs: list[Hub] = self.map.hub[:]
        if self.map.start_hub is not None:
            self.all_hubs.append(self.map.start_hub)
        if self.map.end_hub is not None:
            self.all_hubs.append(self.map.end_hub)

    def yen_k_shortest(self, k: int) -> list[list[str]]:
        """Compute up to k distinct shortest paths from start to end.

        Finds the optimal path using Dijkstra, then forces a second path
        by excluding the first restricted node encountered, encouraging
        the algorithm to explore an alternative route. If fewer than k
        distinct paths are found, the list is padded by cycling through
        the discovered paths.

        Args:
            k: The number of paths to return.

        Returns:
            A list of k paths, each path being an ordered list of hub
            names from start to end. Paths may be repeated if fewer than
            k distinct routes exist.
        """
        def dijkstra_with_excluded(excluded_nodes: set[str]) -> list[str]:
            """Run Dijkstra's algorithm while skipping a set of nodes.

            Uses zone-based traversal costs: priority zones are slightly
            cheaper than normal, restricted zones are slightly more
            expensive, and blocked zones are impassable.

            Args:
                excluded_nodes: Hub names that must not appear in the path.

            Returns:
                An ordered list of hub names from start to end, or an
                empty list if no path exists.
            """
            if self.map.start_hub is None or self.map.end_hub is None:
                return []

            costs: dict[Zone, float] = {
                Zone.normal: 1.0,
                Zone.priority: 0.99,
                Zone.restricted: 1.1,
                Zone.blocked: float('inf')
            }
            tab: dict[str, float] = {
                h.name: float('inf') for h in self.all_hubs
            }
            tab[self.map.start_hub.name] = 0.0
            parents: dict[str, str | None] = {
                h.name: None for h in self.all_hubs
            }
            heap: list[tuple[float, str]] = [
                (0.0, self.map.start_hub.name)
            ]
            visited: set[str] = set()

            while heap:
                cost, name = heapq.heappop(heap)
                if name in visited:
                    continue
                visited.add(name)
                if name == self.map.end_hub.name:
                    break
                for c in self.map.connections:
                    if c.zone1.name == name:
                        n = c.zone2
                    elif c.zone2.name == name:
                        n = c.zone1
                    else:
                        continue
                    if n.metadata.zone == Zone.blocked:
                        continue
                    if n.name in excluded_nodes:
                        continue
                    new_cost = cost + costs[n.metadata.zone]
                    if new_cost < tab[n.name]:
                        tab[n.name] = new_cost
                        parents[n.name] = name
                        heapq.heappush(heap, (new_cost, n.name))

            if parents[self.map.end_hub.name] is None:
                return []
            path: list[str] = []
            node: str = self.map.end_hub.name
            while node != self.map.start_hub.name:
                path.append(node)
                parent = parents[node]
                if parent is None:
                    return []
                node = parent
            path.append(self.map.start_hub.name)
            return path[::-1]

        first = dijkstra_with_excluded(set())
        if not first:
            return []

        paths = [first]

        forced_excluded: set[str] = set()
        for node in first:
            hub = next((h for h in self.all_hubs if h.name == node), None)
            if hub and hub.metadata.zone == Zone.restricted:
                forced_excluded.add(node)
                break

        second = dijkstra_with_excluded(forced_excluded)
        if second and second != first:
            paths.append(second)

        nb = len(paths)
        while len(paths) < k:
            paths.append(paths[len(paths) % nb])
        return paths

    def find_best_paths(self, k: int) -> list[list[str]]:
        """Return the k best paths for drone assignment.

        Delegates to yen_k_shortest to produce a list of paths
        suitable for distribution across all drones.

        Args:
            k: The number of paths to return, typically equal to
               the total number of drones.

        Returns:
            A list of k paths, each an ordered list of hub names.
        """
        return self.yen_k_shortest(k)
