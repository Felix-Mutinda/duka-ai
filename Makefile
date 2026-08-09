UV := uv

.PHONY: help sync lock lint fix format test coverage ci demo

help:
	@echo "sync     - install dependencies"
	@echo "lock     - update uv.lock"
	@echo "lint     - run ruff check"
	@echo "fix      - run ruff check with fixes"
	@echo "format   - run ruff format"
	@echo "test     - run pytest"
	@echo "coverage - run pytest with HTML coverage"
	@echo "ci       - lint, format check, tests"
	@echo "demo     - run demo app when wired"

sync:
	$(UV) sync --dev

lock:
	$(UV) lock

lint:
	$(UV) run ruff check .

fix:
	$(UV) run ruff check --fix .

format:
	$(UV) run ruff format .

eval:
	$(UV) run python -m eval.run_eval

test:
	$(UV) run pytest

coverage:
	$(UV) run pytest --cov=core --cov-report=html

ci:
	$(UV) run ruff check .
	$(UV) run ruff format --check .
	$(UV) run pytest

demo:
	@echo "Demo app is wired in Phase 7."

trace-demo:
	$(UV) run python -m observability.export_demo