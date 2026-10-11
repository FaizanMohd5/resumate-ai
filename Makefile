.PHONY: dev tunnel

dev:
	docker compose up --build

tunnel:
	ngrok http 8000
