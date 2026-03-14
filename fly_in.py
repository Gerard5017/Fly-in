from src.map_validator import MapValidator
from src.visualizer import Visualiser


if __name__ == "__main__":
    try:
        # map = MapValidator("easy/01_linear_path.txt")
        map = MapValidator("hard/01_maze_nightmare.txt")
        # map = MapValidator("challenger/01_the_impossible_dream.txt")
        visual = Visualiser(map)
        visual.run()

    except Exception as e:
        print(f"ERROR: {e}")
