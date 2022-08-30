### Development

SRC_DIRS := backend metrics-exporter fixtures

.PHONY: install
install:  ## Install Python development dependencies
	pip install -r backend/dev-requirements.txt

.PHONY: db
db:  ## Set up test database
	docker run --name postgres --rm \
		-e POSTGRES_DB=substra \
		-e POSTGRES_USER=postgres \
		-e POSTGRES_PASSWORD=postgres \
		-p 5432:5432 -d postgres:latest

.PHONY: test
test:  ## Run tests
	cd backend && pytest --cov-report=

.PHONY: coverage
coverage: test  ## Report test coverage
	cd backend && coverage report

.PHONY: format
format:  ## Format code
	black $(SRC_DIRS)
	isort $(SRC_DIRS)

.PHONY: lint
lint:  ## Perform a static analysis of the code
	flake8 $(SRC_DIRS)
	bandit --ini=.bandit
	mypy backend/substrapp/tasks/ 

.PHONY: shell
shell:	## Start a Python shell for the Django project
	python backend/manage.py shell

.PHONY: migrations
migrations: ## Create missing Django migrations, if any. See also: check-migrations.
	python backend/manage.py makemigrations --settings backend.settings.test

.PHONY: check-migrations
check-migrations: ## Check whether there are missing Django migrations
	python backend/manage.py makemigrations --dry-run --check --no-input --settings backend.settings.test

.PHONY: quickstart
quickstart:  ## Quickstart for local dev
	cd backend && DJANGO_SETTINGS_MODULE=backend.settings.localdev ISOLATED=1 sh dev-startup.sh

.PHONY: fixtures
fixtures:
	python backend/manage.py generate_fixtures --settings backend.settings.localdev

### gRPC

ORCHESTRATOR_ROOT?=../orchestrator
UNAME_S := $(shell uname -s)
GRPC_CLIENT_DIR := ./backend/orchestrator

ifeq ($(UNAME_S),Linux)
	SED_BINARY = sed
endif
ifeq ($(UNAME_S),Darwin)
	SED_BINARY = gsed
endif

.PHONY: orchestrator-grpc
orchestrator-grpc:	## Generate Python gRPC client files (ORCHESTRATOR_ROOT variable may override the default orchestrator path)
	python -m grpc_tools.protoc -I ${ORCHESTRATOR_ROOT}/lib/asset/ \
		--python_out=$(GRPC_CLIENT_DIR) \
		--grpc_python_out=$(GRPC_CLIENT_DIR) \
		--mypy_out=$(GRPC_CLIENT_DIR) \
		--mypy_grpc_out=$(GRPC_CLIENT_DIR) \
		${ORCHESTRATOR_ROOT}/lib/asset/*.proto
	${SED_BINARY} -i -E 's/^import.*_pb2/from . \0/' $(GRPC_CLIENT_DIR)/*_pb2*.py

### Documentation

.PHONY: docs
docs:  ## Generate documentation
	$(MAKE) -C docs

.PHONY: docs-charts
docs-charts:  ## Generate Helm chart documentation
	$(MAKE) -C charts doc

### Makefile

.PHONY: help
help:  ## Display this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

.DEFAULT_GOAL := help
