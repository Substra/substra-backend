ORCHESTRATOR_ROOT?=../../orchestrator
UNAME_S := $(shell uname -s)

ifeq ($(UNAME_S),Linux)
	SED_BINARY = sed
endif
ifeq ($(UNAME_S),Darwin)
	SED_BINARY = gsed
endif

.PHONY: test
test:
	DJANGO_SETTINGS_MODULE=backend.settings.test coverage run manage.py test

.PHONY: coverage
coverage: test
	coverage report

.PHONY: exception_map
exception_map:
	# Fully rebuild the reference file, because upading the reference file
	# in-place occasionally leads to failed unit tests.
	rm substrapp/tasks/exceptions.json

	# Use python3.7 so that the exception map is compatible with the python
	# version used in Travis unit test builds.
	python3.7 substrapp/compute_tasks/exception_handler.py

orchestrator-grpc:
	python -m grpc_tools.protoc -I ${ORCHESTRATOR_ROOT}/lib/asset/ --python_out=./orchestrator --grpc_python_out=./orchestrator ${ORCHESTRATOR_ROOT}/lib/asset/*.proto

	${SED_BINARY} -i -E 's/^import.*_pb2/from . \0/' ./orchestrator/*_pb2*.py
