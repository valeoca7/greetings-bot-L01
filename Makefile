PYTHON ?= python3

.PHONY: run test

run:
	PYTHONPATH=src $(PYTHON) -m greetings_bot

test:
	PYTHONPATH=src $(PYTHON) -m unittest discover -v
