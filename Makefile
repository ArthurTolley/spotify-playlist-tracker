.PHONY: run logs stop down

run:
	@test -f .env || (echo "Missing .env — run: cp .env.example .env"; exit 1)
	docker compose up --build -d
	@echo "Spotify Playlist Tracker is running at http://127.0.0.1:8888"

logs:
	docker compose logs -f

stop:
	docker compose stop

down:
	docker compose down
