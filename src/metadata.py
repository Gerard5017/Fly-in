from pydantic import BaseModel, Field
from enum import Enum


class Zone(Enum):
    """contain the Enumeration of zone"""
    normal = "normal"
    restricted = "restricted"
    priority = "priority"
    blocked = "blocked"


class Color(Enum):
    """contain the Enumeration of color"""
    red = "red"
    blue = "blue"
    yellow = "yellow"
    purple = "purple"
    green = "green"
    orange = "orange"
    white = "white"
    cyan = "cyan"
    brown = "brown"
    marron = "maroon"
    darkred = "darkred"
    rainbow = "rainbow"
    gold = "gold"
    crimson = "crimson"
    black = "black"
    violet = "violet"


class MetadataHub(BaseModel):
    """contain the metadata of an hub"""
    zone: Zone = Field(default=Zone.normal)
    color: Color = Field(default=Color.white)
    max_drones: int = Field(default=1, ge=1)
