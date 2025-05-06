.SILENT:

run:
	uv run ./main.py

lint:
	uvx ruff check

update:
	uv sync -U
	uv pip compile pyproject.toml > requirements.txt
