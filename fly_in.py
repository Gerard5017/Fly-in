from src.map_validator import MapValidator
from src.visualizer import Visualiser
from sys import argv


if __name__ == "__main__":
    try:
        if len(argv) != 2 or not argv[1].endswith(".txt"):
            raise ValueError("must have a map argument wich is a .txt")
        map = MapValidator(argv[1])
        visual = Visualiser(map)
        visual.run()

    except Exception as e:
        print(f"ERROR: {e}")

    except KeyboardInterrupt:
        print("\nProgramme was kill")
