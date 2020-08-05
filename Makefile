

load-files:
	python acquisition.py

storage:
	python storage.py

query:
	python query.py

check:
	flake8

clean:
	black *.py
	black database/*.py
	black common/*.py
	black database/test/*.py

test:
	pytest -n 5 database

.PHONY: load-files clean storage