.PHONY: venv requirements server

clean: clean-venv clean-venv-lint clean-caches

clean-venv:
	rm -rf venv

clean-venv-lint:
	rm -rf venv-lint

clean-caches:
	rm -rf .mypy_cache
	rm -rf __pycache__

venv:
	test -d venv || virtualenv-3.6 venv

venv-lint:
	test -d venv-lint || virtualenv-3.6 venv-lint

requirements: venv
	( \
		source venv/bin/activate; \
		pip install -r requirements.txt; \
	)

requirements-lint: venv-lint
	( \
		source venv-lint/bin/activate; \
		pip install -r requirements.txt; \
		pip install -r requirements-lint.txt; \
	)

server: venv requirements
	( \
		source venv/bin/activate; \
		export FLASK_APP=lawfight; \
		export FLASK_DEBUG=1; \
		flask run; \
	)

server-prod: venv requirements
	( \
		source venv/bin/activate; \
		export PORT=5000; \
		python lawfight.py; \
	)

lint: venv-lint requirements-lint
	( \
		source venv-lint/bin/activate; \
		pylint **.py; \
		mypy --ignore-missing-imports **.py; \
	)