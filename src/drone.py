from .hub import Hub, Connection
from .metadata import Zone
from typing import Optional


class Drone():
    """Represents a single drone navigating through the map.

    A drone follows a pre-computed path of hubs, advancing one hub per
    turn subject to zone restrictions and capacity constraints enforced
    by the simulation.

    Attributes:
        drone_id: Unique identifier string for this drone.
        all_hubs: Full list of hubs available on the map.
        path: Ordered list of Hub objects the drone will traverse.
        path_index: Current position index within path.
        waiting: Whether the drone is waiting to enter a restricted zone.
        finished: Whether the drone has reached its final destination.
        start_turn: The turn number on which the drone becomes active.
    """

    def __init__(self, drone_id: str,
                 path: list[str],
                 all_hubs: list[Hub],
                 start_turn: int = 0) -> None:
        """Initialize a drone with its route and activation delay.

        Args:
            drone_id: A unique identifier for this drone (e.g. "D0").
            path: Ordered list of hub names from start to end.
            all_hubs: All hubs in the map, used to resolve names to objects.
            start_turn: Turn number before which the drone stays inactive.
        """
        self.drone_id = drone_id
        self.all_hubs = all_hubs
        self.path: list[Hub] = self.convert_path(path)
        self.path_index = 0
        self.waiting = False
        self.finished = False
        self.start_turn = start_turn

    def convert_path(self, path: list[str]) -> list[Hub]:
        """Convert a list of hub names into a list of Hub objects.

        Looks up each name in all_hubs. Prints a warning for any name
        that cannot be resolved.

        Args:
            path: Ordered list of hub name strings.

        Returns:
            Ordered list of Hub objects corresponding to the names.
        """
        new: list[Hub] = []
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

    def go_on(self, current_turn: int) -> Optional[str]:
        """Attempt to advance the drone by one hub.

        The drone will wait one extra turn before entering a restricted
        zone. If already waiting, it advances on the next call.

        Args:
            current_turn: The current simulation turn number.

        Returns:
            A string of the form "drone_id-hub_name" if the drone moved,
            or None if it is finished or not yet active.
        """
        if self.is_finished():
            return None
        if current_turn <= self.start_turn:
            return None
        next_hub = self.path[self.path_index + 1]
        if next_hub.metadata.zone == Zone.restricted and not self.waiting:
            self.waiting = True
        else:
            self.path_index += 1
            self.waiting = False
        return f"{self.drone_id}-{next_hub.name}"

    def go_back(self, current_turn: int) -> None:
        """Rewind the drone by one hub, used for turn undo.

        Args:
            current_turn: The current simulation turn number.
        """
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

    def current_zone(self) -> Hub:
        """Return the hub the drone currently occupies.

        Returns:
            The Hub at the drone's current path index.
        """
        return self.path[self.path_index]

    def is_finished(self) -> bool:
        """Check whether the drone has reached the end of its path.

        Returns:
            True if the drone is at the last hub in its path.
        """
        return self.path_index == len(self.path) - 1

    def next_zone(self) -> Optional[Hub]:
        """Return the next hub in the drone's path without advancing.

        Returns:
            The next Hub, or None if the drone has finished.
        """
        if self.is_finished():
            return None
        return self.path[self.path_index + 1]

    def next_connection(self, connections:
                        list[Connection]) -> Optional[Connection]:
        """Find the connection object linking the current and next hub.

        Args:
            connections: All connections defined in the map.

        Returns:
            The matching Connection, or None if the drone is finished
            or no matching connection exists.
        """
        if self.is_finished():
            return None
        current = self.path[self.path_index]
        nxt = self.path[self.path_index + 1]
        for c in connections:
            if ((c.zone1 == current and c.zone2 == nxt) or
               (c.zone2 == current and c.zone1 == nxt)):
                return c
        return None
