PYTHON = python

.PHONY: test
test:
	cd backend; DJANGO_SETTINGS_MODULE=backend.settings.test coverage run manage.py test

.PHONY: coverage
coverage:
	cd backend;coverage report

.PHONY: exception_map
exception_map:
	cd backend; $(PYTHON) substrapp/tasks/exception_handler.py
