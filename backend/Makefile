PYTHON = python

.PHONY: test
test:
	DJANGO_SETTINGS_MODULE=backend.settings.test coverage run manage.py test

.PHONY: coverage
coverage:
	coverage report

.PHONY: exception_map
exception_map:
	$(PYTHON) substrapp/tasks/exception_handler.py
