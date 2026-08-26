PYTHON ?= python3
EVENT ?= events/delivery_batch.json

.PHONY: help run test test-unit check check-runtime check-syntax check-template package replay-plan

help:
	@echo "make check    run syntax, unit, and template checks"
	@echo "make package  create the tracked source archive"
	@echo "make run      start the local command line app"
	@echo "make replay-plan EVENT=path  inspect a saved delivery batch"

run:
	PYTHONPATH=src $(PYTHON) -m greetings_bot

test: test-unit

test-unit:
	PYTHONPATH=src $(PYTHON) -m unittest discover -v

check: check-runtime check-syntax test-unit check-template

check-runtime:
	PYTHONPATH=src $(PYTHON) -m greetings_bot.runtime_compat

check-syntax:
	$(PYTHON) -m compileall -q src tests

check-template:
	PYTHONPATH=src $(PYTHON) -m unittest -v tests.test_template

replay-plan:
	PYTHONPATH=src $(PYTHON) -m greetings_bot.replay $(EVENT)

package:
	mkdir -p dist
	git archive --format=tar.gz --output=dist/greetings-bot-src.tar.gz HEAD
