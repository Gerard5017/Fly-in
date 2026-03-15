from .hub import Hub, Connection
from .drone import Drone
from .algorythme import Algorythme
from .map_validator import MapValidator


class Simulation():
    def __init__(self, all_hubs: list[Hub], map: MapValidator):
        self.drones: list[Drone] = []
        self.map = map
        self.algo = Algorythme(self.map)
        self.all_hubs = all_hubs
        self.turn = 0
        self.history: list[list[tuple[int, bool]]] = []

    def _bottleneck(self, path: list[str]) -> int:
        caps = [
            h.metadata.max_drones
            for name in path[1:-1]
            for h in self.all_hubs
            if h.name == name
        ]
        return min(caps) if caps else 1

    def create_drone(self) -> None:
        paths = self.algo.find_best_paths(self.map.nb_drones)
        bottlenecks = [self._bottleneck(p) for p in paths]
        total_capacity = sum(bottlenecks)
        
        counts: dict[tuple, int] = {}
        for i in range(self.map.nb_drones):
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
        if on:
            if self.is_finished():
                return
            self.history.append([(d.path_index, d.waiting) for d in self.drones])
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
        return [d for d in self.drones if not d.is_finished() and self.turn > d.start_turn]

    def _occupancy(self) -> dict[str, int]:
        occ: dict[str, int] = {}
        for d in self.drones:
            n = d.current_zone().name
            occ[n] = occ.get(n, 0) + 1
        return occ

    def _conn_key(self, c: Connection) -> str:
        return f"{min(c.zone1.name, c.zone2.name)}-{max(c.zone1.name, c.zone2.name)}"

    def _is_special(self, name: str) -> bool:
        return name in (
            self.map.start_hub.name if self.map.start_hub else "",
            self.map.end_hub.name if self.map.end_hub else ""
        )

    def _resolve(self, wants: list[tuple], occ: dict[str, int], leaving: dict[str, int]) -> set[int]:
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
        active = self._active()
        occ = self._occupancy()
        print([(d.drone_id, d.path[d.path_index+1].name) for d in active])
        wants = [(d, d.path[d.path_index + 1],
                  d.next_connection(self.map.connections)) for d in active]
        leaving: dict[str, int] = {}
        for d, _, __ in wants:
            n = d.current_zone().name
            leaving[n] = leaving.get(n, 0) + 1
        allowed = self._resolve(wants, occ, leaving)
        for i, (d, _, __) in enumerate(wants):
            if i in allowed:
                d.go_on(self.turn)

    def is_finished(self) -> bool:
        return all(d.is_finished() for d in self.drones)