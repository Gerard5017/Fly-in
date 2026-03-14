import os
import re
from .utils import isnumber
from .metadata import Metadata_hub
from pydantic import ValidationError


class MapValidator():
    def __init__(self, map_file: str):
        self.nb_drones = 0
        self.start_hub = None
        self.end_hub = None
        self.hub = []
        self.connections = []

        if not map_file.endswith(".txt"):
            raise ValueError("the map must be a '.txt'")

        base_dir = os.path.dirname(os.path.abspath(__file__))
        map_path = os.path.join(base_dir, "..", "maps",  map_file)
        try:
            i = 0
            with open(map_path, "r") as file:
                content = file.read().split("\n")
                content = self.remove_comment(content)

                self.parse_nb_drones(content[i])
                i += 1
                
                while i < len(content) and (content[i].startswith("hub:") or
                    content[i].startswith("start_hub:") or
                    content[i].startswith("end_hub:")):
                    self.parse_hub(content[i])
                    i += 1

                while i < len(content) and content[i].startswith("connection:"):
                    self.parse_connection(content[i])
                    i += 1

        except (FileNotFoundError):
            raise FileNotFoundError(f"'{map_file}' not found")

        except (PermissionError):
            raise PermissionError(f"'{map_file}' can't be open")

        except (ValueError) as e:
            raise ValueError(e)

        except (ValidationError) as e:
            raise ValidationError(e)

    def remove_comment(self, content: list[str]) -> list[str]:
        copy =[]
        for line in content:
            if not (line.startswith("#") or line == ""):
                copy.append(line)
        return copy

    def parse_nb_drones(self, first_line: str):
        e = "first line of the map file must be \"nb_drones: 'value: int'\""

        if not first_line.startswith("nb_drones:"):
            raise ValueError(e)

        nb_drones = first_line.split(":")
        if len(nb_drones) != 2:
            raise ValueError(e)

        if nb_drones[1].strip().isdigit():
            self.nb_drones = int(nb_drones[1].strip())
        else:
            raise ValueError(e)

    def parse_hub(self, line_hub: str) -> None:
        e = "A hub must be declared like \"hub: 'name' 'x' 'y' '[metadata]'\""

        if line_hub.startswith("start_hub:") and self.start_hub is not None:
            raise ValueError("must have only one start_hub")

        if line_hub.startswith("end_hub:") and self.end_hub is not None:
            raise ValueError("must have only one end_hub")

        meta_match = re.search(r'\[([^\]]*)\]', line_hub)
        metadata_str = meta_match.group(1) if meta_match else ""
        data_part = line_hub.split("[")[0] if meta_match else line_hub

        parts = data_part.split()[1:]

        if len(parts) != 3:
            raise ValueError(e)

        name, x, y = parts

        for existing_hub in self.hub:
            if existing_hub["name"] == name:
                raise ValueError(f"hub '{name}' already exists")

            if existing_hub["x"] == int(x) and existing_hub["y"] == int(y):
                raise ValueError(f"a hub already exists at position ({x}, {y})")

        for special_hub in [self.start_hub, self.end_hub]:
            if special_hub is not None:
                if special_hub["name"] == name:
                    raise ValueError(f"hub '{name}' already exists")

                if special_hub["x"] == int(x) and special_hub["y"] == int(y):
                    raise ValueError(f"a hub already exists at position ({x}, {y})")

        for c in name:
            if not (c.isdigit() or c.isalpha() or c == "_"):
                raise ValueError("name must contain only letters, "
                                 "numbers or underscores")

        if not isnumber(x) or not isnumber(y):
            raise ValueError("x and y must be integers")

        color = "white"
        zone = "normal"
        max_drones = 1

        for metadata in metadata_str.split():
            d = metadata.split("=")
            if len(d) != 2:
                raise ValueError("metadata must be key=value")
            if d[0] == "max_drones":
                max_drones = int(d[1])
            elif d[0] == "zone":
                zone = d[1]
            elif d[0] == "color":
                color = d[1]

        hub = {
            "name": name,
            "x": int(x),
            "y": int(y),
            "metadata": Metadata_hub(zone=zone, color=color,
                                     max_drones=max_drones)
        }

        if line_hub.startswith("start_hub:"):
            self.start_hub = hub
        elif line_hub.startswith("end_hub:"):
            self.end_hub = hub
        else:
            self.hub.append(hub)

    def parse_connection(self, line) -> None:
        e = ("A connection must be declared like "
            "\"connection: 'zone1'-'zone2' '[metadata]'\"")
        
        meta_match = re.search(r'\[([^\]]*)\]', line)
        metadata_str = meta_match.group(1) if meta_match else ""
        data_part = line.split("[")[0] if meta_match else line

        parts = data_part.split(":")
        if len(parts) != 2:
            raise ValueError(e)

        zones = parts[1].strip().split("-")
        if len(zones) != 2:
            raise ValueError(e)

        zone1, zone2 = zones[0].strip(), zones[1].strip()

        all_hubs = self.hub + [h for h in [self.start_hub, self.end_hub] if h is not None]
        all_names = [h["name"] for h in all_hubs]

        if zone1 not in all_names:
            raise ValueError(f"zone '{zone1}' doesn't exist")
        if zone2 not in all_names:
            raise ValueError(f"zone '{zone2}' doesn't exist")

        for existing in self.connections:
            if ((existing[0] == zone1 and existing[1] == zone2) or
            (existing[0] == zone2 and existing[1] == zone1)):
                raise ValueError(f"connection '{zone1}-{zone2}' already exists")

        max_link_capacity = 1
        for metadata in metadata_str.split():
            d = metadata.split("=")
            if len(d) != 2:
                raise ValueError("metadata must be key=value")
            if d[0] == "max_link_capacity":
                if not d[1].isdigit() or int(d[1]) < 1:
                    raise ValueError("max_link_capacity must be a positive integer")
                max_link_capacity = int(d[1])
            else:
                raise ValueError(f"unknown metadata '{d[0]}' for connection")

        self.connections.append((zone1, zone2, max_link_capacity))
