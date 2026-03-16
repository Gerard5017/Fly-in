from .hub import Hub, Connection
from .drone import Drone
from .algorythme import Algorythme
from .map_validator import MapValidator


class Simulation():
    """Manages the turn-by-turn execution of the drone simulation.

    Handles drone creation, movement resolution, capacity enforcement,
    and undo support via a history stack.

    Attributes:
        drones: All drones participating in the simulation.
        map: The validated map providing graph structure.
        algo: Pathfinding engine used to compute drone routes.
        all_hubs: Flat list of all hubs including start and end.
        turn: Current turn counter.
        history: Stack of snapshots used for undo (go_back).
    """

    def __init__(self, all_hubs: list[Hub], map: MapValidator) -> None:
        """Initialize the simulation.

        Args:
            all_hubs: All hubs in the map, including start and end.
            map: A validated MapValidator instance.
        """
        self.drones: list[Drone] = []
        self.map = map
        self.algo = Algorythme(self.map)
        self.all_hubs = all_hubs
        self.turn = 0
        self.history: list[list[tuple[int, bool]]] = []

    def _bottleneck(self, path: list[str]) -> int:
        """Return the minimum hub capacity along an intermediate path.

        Excludes the start and end hubs since they have no drone limit.

        Args:
            path: Ordered list of hub names.

        Returns:
            The smallest max_drones value among intermediate hubs,
            or 1 if no intermediate hubs exist.
        """
        caps = [
            h.metadata.max_drones
            for name in path[1:-1]
            for h in self.all_hubs
            if h.name == name
        ]
        return min(caps) if caps else 1

    def create_drone(self) -> None:
        """Instantiate all drones and assign them paths with staggered delays.

        Distributes drones across the available paths proportionally to
        each path's bottleneck capacity. Drones assigned to the same path
        are delayed to prevent immediate pile-ups at bottleneck nodes.
        """
        paths = self.algo.find_best_paths(self.map.nb_drones)
        bottlenecks = [self._bottleneck(p) for p in paths]

        counts: dict[tuple[str, ...], int] = {}
        for i in range(1, self.map.nb_drones + 1):
            best = min(
                range(len(paths)),
                key=lambda j: counts.get(tuple(paths[j]), 0) / bottlenecks[j]
            )
            path = paths[best]
            key = tuple(path)
            counts[key] = counts.get(key, 0) + 1
            delay = (counts[key] - 1) // bottlenecks[best]
            d = Drone("D" + str(i), path, self.all_hubs, delay)
            self.drones.append(d)

    def exec_turn(self, on: bool) -> None:
        """Advance or rewind the simulation by one turn.

        Args:
            on: If True, advance one turn forward. If False, undo the
                last turn using the history stack.
        """
        if on:
            if self.is_finished():
                return
            self.history.append([(d.path_index, d.waiting)
                                 for d in self.drones])
            self.turn += 1
            self._apply_moves()
        else:
            if self.turn == 0 or not self.history:
                return
            snapshot = self.history.pop()
            self.turn -= 1
            for i, d in enumerate(self.drones):
                d.path_index, d.waiting = snapshot[i]

    def _active(self) -> list[Drone]:
        """Return all drones that are active and not yet finished.

        Returns:
            List of drones whose start_turn has passed and that have
            not yet reached their destination.
        """
        actives = []
        for d in self.drones:
            if not d.is_finished() and self.turn > d.start_turn:
                actives.append(d)
        return actives

    def _occupancy(self) -> dict[str, int]:
        """Count how many drones currently occupy each hub.

        Returns:
            A mapping of hub name to the number of drones present.
        """
        occ: dict[str, int] = {}
        for d in self.drones:
            n = d.current_zone().name
            occ[n] = occ.get(n, 0) + 1
        return occ

    def _conn_key(self, c: Connection) -> str:
        """Generate a canonical key string for a connection.

        Uses alphabetical ordering of hub names so the key is the same
        regardless of traversal direction.

        Args:
            c: The connection to key.

        Returns:
            A string of the form "hub_a-hub_b" with names in sorted order.
        """
        mn = min(c.zone1.name, c.zone2.name)
        mx = max(c.zone1.name, c.zone2.name)
        return f"{mn}-{mx}"

    def _is_special(self, name: str) -> bool:
        """Check whether a hub name is the start or end hub.

        Special hubs are exempt from capacity checks.

        Args:
            name: The hub name to test.

        Returns:
            True if the hub is the start or end hub.
        """
        return name in (
            self.map.start_hub.name if self.map.start_hub else "",
            self.map.end_hub.name if self.map.end_hub else ""
        )

    def _resolve(self, wants: list[tuple[Drone, Hub, Connection | None]],
                 occ: dict[str, int],
                 leaving: dict[str, int]) -> set[int]:
        """Determine which drones are allowed to move this turn.

        Enforces both connection link capacity and destination hub
        capacity. Drones are processed in order; earlier drones take
        priority when a resource is contested.

        Args:
            wants: List of (drone, next_hub, connection) tuples for all
                   active drones that wish to move.
            occ: Current occupancy count per hub name.
            leaving: Number of drones leaving each hub this turn.

        Returns:
            Set of indices into wants for drones that may move.
        """
        conn_usage: dict[str, int] = {}
        incoming: dict[str, int] = {}
        allowed: set[int] = set()

        for i, (d, nxt, conn) in enumerate(wants):
            if conn is not None:
                key = self._conn_key(conn)
                conn_usage[key] = conn_usage.get(key, 0) + 1
                if conn_usage[key] > conn.max_link_capacity:
                    conn_usage[key] -= 1
                    continue

            if not self._is_special(nxt.name):
                free = (nxt.metadata.max_drones - (occ.get(nxt.name, 0) -
                                                   leaving.get(nxt.name, 0) +
                                                   incoming.get(nxt.name, 0)))
                if free <= 0:
                    if conn is not None:
                        conn_usage[self._conn_key(conn)] -= 1
                    continue

            incoming[nxt.name] = incoming.get(nxt.name, 0) + 1
            allowed.add(i)

        return allowed

    def _apply_moves(self) -> None:
        """Compute and apply all drone movements for the current turn.

        Builds the list of desired moves, resolves conflicts via
        _resolve, then calls go_on for each permitted drone.
        """
        active = self._active()
        occ = self._occupancy()
        wants: list[tuple[Drone, Hub, Connection | None]] = [
            (d, d.path[d.path_index + 1],
             d.next_connection(self.map.connections))
            for d in active
        ]
        leaving: dict[str, int] = {}
        for d, _, __ in wants:
            n = d.current_zone().name
            leaving[n] = leaving.get(n, 0) + 1
        allowed = self._resolve(wants, occ, leaving)
        for i, (d, _, __) in enumerate(wants):
            if i in allowed:
                print(d.go_on(self.turn), end=" ")
        print()

    def is_finished(self) -> bool:
        """Check whether all drones have reached their destination.

        Returns:
            True if every drone has finished its path.
        """
        return all(d.is_finished() for d in self.drones)
