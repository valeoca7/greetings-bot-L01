PYTHON ?= python3

.PHONY: help run test test-unit check check-syntax check-template package

help:
	@echo "make check    run syntax, unit, and template checks"
	@echo "make package  create the tracked source archive"
	@echo "make run      start the local command line app"

run:
	PYTHONPATH=src $(PYTHON) -m greetings_bot

test: test-unit

test-unit:
	PYTHONPATH=src $(PYTHON) -m unittest discover -v

check: check-syntax test-unit check-template

check-syntax:
	$(PYTHON) -m compileall -q src tests

check-template:
	PYTHONPATH=src $(PYTHON) -m unittest -v tests.test_template

package:
	mkdir -p dist
	git archive --format=tar.gz --output=dist/greetings-bot-src.tar.gz HEAD
