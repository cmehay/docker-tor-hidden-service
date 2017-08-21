test:
	tox

check:
	pre-commit run --all-files

build:
	docker-compose build

run: build
	docker-compose up

build-v2:
	docker-compose -f docker-compose.v2.yml build

run-v2: build-v2
	docker-compose -f docker-compose.v2.yml up

build-v3:
	docker-compose -f docker-compose.v3.yml build

run-v3: build-v3
	docker-compose -f docker-compose.v3.yml up
