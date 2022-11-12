PYTHON ?= python3

.PHONY: run test check-template

run:
	PYTHONPATH=src $(PYTHON) -m greetings_bot

test:
	PYTHONPATH=src $(PYTHON) -m unittest discover -v

check-template:
	PYTHONPATH=src $(PYTHON) -m unittest -v tests.test_template
