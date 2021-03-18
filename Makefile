# See Makefile in the backend/ folder

.PHONY: test
test:
	$(MAKE) -C backend test

.PHONY: coverage
coverage:
	$(MAKE) -C backend coverage
