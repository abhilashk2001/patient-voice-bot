# Simple entry points. `make setup` then `make demo` runs with no paid accounts.
.PHONY: setup test demo list

# 1) One-command setup: virtualenv + dependencies.
setup:
	python3 -m venv .venv
	./.venv/bin/pip install -q -r requirements.txt
	@echo "Setup complete. Run 'make demo' (no accounts needed) or 'make test'."

# 2) Prove the code works: 139 unit tests.
test:
	./.venv/bin/python -m pytest -q

# 2) See it work without any paid accounts: render a scenario's prompt + scaffold,
#    no real call, no spend. (Uses .env.example placeholders.)
demo:
	@[ -f .env ] || cp .env.example .env
	PYTHONPATH=src ./.venv/bin/python src/main.py --scenario call_09 --dry-run

# List the 10 scenarios (no setup needed).
list:
	PYTHONPATH=src ./.venv/bin/python src/main.py --list
