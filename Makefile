# See Makefile in the backend/ folder

.PHONY: test
test:
	$(MAKE) -C backend test

.PHONY: coverage
coverage:
	$(MAKE) -C backend coverage

.PHONY: exception_map
exception_map:
	$(MAKE) -C backend exception_map
