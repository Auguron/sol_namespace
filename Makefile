.PHONY:  stage install doc

demo:
	python examples/deleting_names.py

stage:
	pip install -e .

install:
	pip install .

doc:
	pdoc --force --html --output-dir=doc sol_namespace
