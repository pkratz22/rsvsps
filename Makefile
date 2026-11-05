virtual: .venv/bin/pip

.venv/bin/pip:
	virtualenv -p /usr/bin/python3 .venv

install:
	.venv/bin/pip install -Ur requirements.txt

check:
	python3 -m unittest -q

coverage:
	coverage run --source=rsvsps -m unittest discover -q && coverage report -m

ci: coverage

update-requirements: install
	.venv/bin/pip freeze > requirements.txt
