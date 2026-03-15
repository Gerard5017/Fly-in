from .hub import Hub
from .metadata import Zone
from typing import Optional


class Drone():
    def __init__(self, drone_id: str, path: list[str], 
             all_hubs: list[Hub], start_turn: int = 0):
        self.drone_id = drone_id
        self.all_hubs = all_hubs
        self.path = self.convert_path(path)
        self.path_index = 0
        self.waiting = False
        self.finished = False
        self.start_turn = start_turn
        

    def convert_path(self, path: list[str]) -> list[Hub]:
        new = []
        for node in path:
            found = False
            for hub in self.all_hubs:
                if node == hub.name:
                    new.append(hub)
                    found = True
                    break
            if not found:
                print(f"HUB NOT FOUND: {node}")
        return new

    def go_on(self, current_turn: int) -> None:
        if self.is_finished():
            return
        if current_turn <= self.start_turn:
            return
        next_hub = self.path[self.path_index + 1]
        print(f"{self.drone_id} | turn={current_turn} | current={self.path[self.path_index].name} | next={next_hub.name} | waiting={self.waiting}")
        if next_hub.metadata.zone == Zone.restricted and not self.waiting:
            self.waiting = True
        else:
            self.path_index += 1
            self.waiting = False

    def go_back(self, current_turn: int) -> None:
        if self.path_index == 0:
            return
        if current_turn <= self.start_turn:
            return
        self.path_index -= 1
        current_hub = self.path[self.path_index]
        next_hub = self.path[self.path_index + 1]
        if next_hub.metadata.zone == Zone.restricted and not self.waiting:
            self.waiting = True
        elif current_hub.metadata.zone != Zone.restricted:
            self.waiting = False

    def current_zone(self):
        return self.path[self.path_index]

    def is_finished(self):
        return self.path_index == len(self.path) - 1
    
    def next_zone(self) -> Optional[Hub]:
        """R"""
        if self.is_finished():
            return None
        return self.path[self.path_index + 1]

    def next_connection(self, connections: list) -> Optional[object]:
        """R"""
        if self.is_finished():
            return None
        current = self.path[self.path_index]
        nxt = self.path[self.path_index + 1]
        for c in connections:
            if (c.zone1 == current and c.zone2 == nxt) or \
            (c.zone2 == current and c.zone1 == nxt):
                return c
        return None