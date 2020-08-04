

load-files:
	python acquisition.py

storage:
	python storage.py

clean:
	black *.py
	black database/*.py
	black common/*.py
	black database/test/*.py

test:
	pytest database

.PHONY: load-files clean storage