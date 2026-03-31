.PHONY: help setup backend-install frontend-install backend-test backend-import frontend-build smoke

help:
	@echo "Targets:"
	@echo "  make setup          Install backend and frontend dependencies"
	@echo "  make backend-test   Run backend unit tests"
	@echo "  make frontend-build Run frontend production build"
	@echo "  make smoke          Run full smoke checks (setup + tests + build)"

setup: backend-install frontend-install

backend-install:
	@test -d backend/.venv || python3 -m venv backend/.venv
	@backend/.venv/bin/pip install -r backend/requirements.txt

frontend-install:
	@cd frontend && npm install

backend-test:
	@backend/.venv/bin/python -m unittest discover -s backend/tests

backend-import:
	@backend/.venv/bin/python -c "import backend.app.main as app; print(app.app.title)"

frontend-build:
	@cd frontend && npm run build

smoke: setup backend-test backend-import frontend-build
