.EXPORT_ALL_VARIABLES:

TOR_VERSION = $(shell bash last_tor_version.sh)

test:
	tox

tag:
	git tag v$(TOR_VERSION) -f

release: test tag
	git push origin --tags

check:
	pre-commit run --all-files

build:
	- echo build with tor version $(TOR_VERSION)
	docker-compose -f docker-compose.build.yml build

rebuild:
	docker-compose -f docker-compose.build.yml build --no-cache

run: build
	docker-compose -f docker-compose-v1.yml up --force-recreate
run-v2: build
	docker-compose -f docker-compose.v2.yml up --force-recreate

run-v2-socket: build
	docker-compose -f docker-compose.v2.socket.yml up --force-recreate

run-v3: build
	docker-compose -f docker-compose.v3.yml up --force-recreate
