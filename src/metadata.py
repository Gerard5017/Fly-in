from pydantic import BaseModel, Field
from enum import Enum


class Zone(Enum):
    normal = "normal"
    restricted = "restricted"
    priority = "priority"
    blocked = "blocked"


class Color(Enum):
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


class Metadata_hub(BaseModel):
    zone: Zone = Field(default=Zone.normal)
    color: Color = Field(default=Color.white)
    max_drones: int = Field(default=1, ge=1)
