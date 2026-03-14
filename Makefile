SRC =	src/ fly_in.py

FLAGS = --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

install:
	@uv venv --python 3.10
	@uv add --dev flake8 mypy
	@uv add pydantic pygame
	@uv sync
	@clear

run:
	@clear
	@.venv/bin/python3 fly_in.py

debug:
	@clear
	@.venv/bin/python3 -m pdb fly_in.py

clean:
	@clear
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	find . -name "*.pyc" -delete

fclean: clean
	@clear
	rm -rf .venv
	rm -f uv.lock
	rm -f maze.txt

lint:
	@clear
	@status=0; \
	uv run flake8 $(SRC) || status=$$?; \
	uv run mypy $(SRC) $(FLAGS) || status=$$?; \
	exit $$status

lint-strict:
	@clear
	@status=0; \
	uv run flake8 $(SRC) || status=$$?; \
	uv run mypy $(SRC) $(FLAGS) --strict || status=$$?; \
	exit $$status

.PHONY: install run debug clean fclean lint lint-strict