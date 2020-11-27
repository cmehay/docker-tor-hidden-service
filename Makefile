.EXPORT_ALL_VARIABLES:

TOR_VERSION = $(shell bash last_tor_version.sh)
TORSOCKS_VERSION = $(shell bash last_torsocks_version.sh)
CUR_COMMIT = $(shell git rev-parse --short HEAD)
CUR_TAG = v$(TOR_VERSION)-$(CUR_COMMIT)

test:
	tox

tag:
	git tag $(CUR_TAG)

release: test tag
	git push origin --tags

check:
	pre-commit run --all-files

build:
	- echo build with tor version $(TOR_VERSION) and torsocks version $(TORSOCKS_VERSION)
	docker-compose -f docker-compose.build.yml build

rebuild:
	- echo rebuild with tor version $(TOR_VERSION) and torsocks version $(TORSOCKS_VERSION)
	docker-compose -f docker-compose.build.yml build --no-cache

run: build
	docker-compose -f docker-compose.v1.yml up --force-recreate
run-v2: build
	docker-compose -f docker-compose.v2.yml up --force-recreate

run-v2-socket: build
	docker-compose -f docker-compose.v2.socket.yml up --force-recreate

run-v3: build
	docker-compose -f docker-compose.v3.yml up --force-recreate

shell-v3: build
	docker-compose -f docker-compose.v3.yml run tor--rm tor sh

run-v3-latest:
	docker-compose -f docker-compose.v3.latest.yml up --force-recreate

run-vanguards: build
	docker-compose -f docker-compose.vanguards.yml up --force-recreate

run-vanguards-network: build
	docker-compose -f docker-compose.vanguards-network.yml up --force-recreate
