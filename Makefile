# Raccourcis de développement. Surchargez MAMBA si nécessaire : make tests MAMBA=/chemin/mamba
MAMBA ?= mamba
ENV_NAME ?= cs-system

.PHONY: env tests docs

env:
	$(MAMBA) create -n $(ENV_NAME) -f environment.yml
	$(MAMBA) run -n $(ENV_NAME) python -m pip install -e .
	$(MAMBA) run -n $(ENV_NAME) playwright install chromium

tests:
	python -m pytest --cov -q -p no:cacheprovider

docs:
	mkdocs build --strict
