.DEFAULT_GOAL := help

.PHONY: test
test: ## Launch the unit tests
	$(info ************  Launching tests ************)
	cd substrabac && \
	pip install -r requirements.txt && \
	DJANGO_SETTINGS_MODULE=substrabac.settings.test coverage run manage.py test && \
	coverage report && \
	coverage html

.PHONY: build
build: ## Build artifacts like docker images
	$(info ************  Building docker images ************)
	docker build -t substra/celerybeat -f docker/celerybeat/Dockerfile .
	docker build -t substra/celeryworker -f docker/celeryworker/Dockerfile .
	docker build -t substra/substrabac -f docker/substrabac/Dockerfile .

.PHONY: help
help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
