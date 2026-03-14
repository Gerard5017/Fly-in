from src.map_validator import MapValidator


if __name__ == "__main__":
    try:
        maps = MapValidator("easy/01_linear_path.txt")

    except Exception as e:
        print(f"ERROR: {e}")
