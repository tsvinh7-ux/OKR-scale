# DMAG OKR - shortcuts for macOS / Linux
.PHONY: start logs stop test update reset

start:   ## start (first run installs everything with demo data)
	docker compose up -d
	@echo "First start takes 2-4 minutes: make logs. Then open http://localhost:8069 (admin / admin)"

logs:
	docker compose logs -f odoo

stop:
	docker compose down

test:    ## run every automated test on a throw-away database
	docker compose run --rm tests

update:  ## after git pull: update the modules of the database
	OKR_UPDATE=1 docker compose up -d --force-recreate odoo

reset:   ## delete the database and start again from scratch
	docker compose down -v
	docker compose up -d
