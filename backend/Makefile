.PHONY: test
test:
	DJANGO_SETTINGS_MODULE=backend.settings.test coverage run manage.py test

.PHONY: coverage
coverage:
	coverage report

.PHONY: exception_map
exception_map:
	# Fully rebuild the reference file, because upading the reference file
	# in-place occasionally leads to failed unit tests.
	rm substrapp/tasks/exceptions.json

	# Use python3.7 so that the exception map is compatible with the python
	# version used in Travis unit test builds.
	python3.7 substrapp/tasks/exception_handler.py
