

load-files:
	python acquisition.py

storage:
	python storage.py

clean:
	black *.py
	black database/*.py
	black common/*.py


.PHONY: load-files clean storage