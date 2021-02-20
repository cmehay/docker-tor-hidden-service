.EXPORT_ALL_VARIABLES:

LAST_TOR_VERSION = $(shell bash last_tor_version.sh)
LAST_TORSOCKS_VERSION = $(shell bash last_torsocks_version.sh)
TOR_VERSION = $(shell cat current_tor_version)
TORSOCKS_VERSION = $(shell cat current_torsocks_version)
CUR_COMMIT = $(shell git rev-parse --short HEAD)
CUR_TAG = v$(TOR_VERSION)-$(CUR_COMMIT)

test:
	tox

tag:
	git tag $(CUR_TAG)

update_tor_version:
	echo $(LAST_TOR_VERSION) > current_tor_version
	echo $(LAST_TORSOCKS_VERSION) > current_torsocks_version

release: test tag
	git push origin --tags

check:
	pre-commit run --all-files

build:
	- echo build with tor version $(TOR_VERSION) and torsocks version $(TORSOCKS_VERSION)
	- echo 'Please run make update_tor_version to build the container with the last tor version'
	docker-compose -f docker-compose.build.yml build

rebuild:
	- echo rebuild with tor version $(TOR_VERSION) and torsocks version $(TORSOCKS_VERSION)
	- echo 'Please run make update_tor_version to build the container with the last tor version'
	docker-compose -f docker-compose.build.yml build --no-cache --pull

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
