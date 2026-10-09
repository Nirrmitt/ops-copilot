.PHONY: setup seed run-api run-ui test lint eval docker-up
setup:
	python -m pip install -e ".[dev]"
seed:
	python -m app.seed
run-api:
	uvicorn app.api:app --reload
run-ui:
	streamlit run ui/streamlit_app.py
test:
	pytest -q
lint:
	ruff check .
eval:
	python -m eval.run_eval
docker-up:
	docker compose up --build
