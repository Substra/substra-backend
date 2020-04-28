PYTHON = python

.PHONY: test
test:
	DJANGO_SETTINGS_MODULE=backend.settings.test coverage run manage.py test

.PHONY: coverage
coverage:
	coverage report

.PHONY: exception_map
exception_map:
	rm substrapp/tasks/exceptions.json
	$(PYTHON) substrapp/tasks/exception_handler.py
