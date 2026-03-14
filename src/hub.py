from dataclasses import dataclass
from .metadata import MetadataHub


@dataclass
class Hub:
    """Represents a zone/hub in the drone network."""

    name: str
    x: int
    y: int
    metadata: MetadataHub


@dataclass
class Connection:
    """Represents a bidirectional connection between two hubs."""

    zone1: Hub
    zone2: Hub
    max_link_capacity: int
