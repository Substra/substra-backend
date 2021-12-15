# See Makefile in the backend/ folder

.PHONY: test
test:
	$(MAKE) -C backend test

.PHONY: db-test
db-test:
	$(MAKE) -C backend db-test

.PHONY: coverage
coverage:
	$(MAKE) -C backend coverage

docs: doc

doc:
	$(MAKE) -C docs

chart-doc:
	$(MAKE) -C charts doc
