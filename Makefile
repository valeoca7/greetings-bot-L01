PYTHON ?= python3

.PHONY: run test test-unit check check-syntax check-template package

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
	$(PYTHON) -m tarfile -c dist/greetings-bot-src.tar.gz README.md setup.cfg setup.py template.yaml src
