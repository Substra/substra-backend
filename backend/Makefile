ORCHESTRATOR_ROOT?=../../orchestrator
UNAME_S := $(shell uname -s)

ifeq ($(UNAME_S),Linux)
	SED_BINARY = sed
endif
ifeq ($(UNAME_S),Darwin)
	SED_BINARY = gsed
endif

.PHONY: db-test
db-test:
	docker run --name postgres --rm \
		-e POSTGRES_DB=substra \
		-e POSTGRES_USER=postgres \
		-e POSTGRES_PASSWORD=postgres \
		-p 5432:5432 -d postgres:11

.PHONY: test
test:
	DJANGO_SETTINGS_MODULE=backend.settings.test coverage run manage.py test

.PHONY: coverage
coverage: test
	coverage report

orchestrator-grpc:
	python -m grpc_tools.protoc -I ${ORCHESTRATOR_ROOT}/lib/asset/ --python_out=./orchestrator --grpc_python_out=./orchestrator ${ORCHESTRATOR_ROOT}/lib/asset/*.proto

	${SED_BINARY} -i -E 's/^import.*_pb2/from . \0/' ./orchestrator/*_pb2*.py
