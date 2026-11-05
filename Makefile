all: doku.pdf

data/blocks.csv: data/make_example_data.py
	python3 data/make_example_data.py

data/sites.csv data/dictionary.csv: data/blocks.csv data/prepare.py
	python3 data/prepare.py

doku.pdf: doku.tex zkopipeline.sty data/sites.csv data/dictionary.csv
	pdflatex -interaction=nonstopmode -halt-on-error doku.tex
	pdflatex -interaction=nonstopmode -halt-on-error doku.tex

clean:
	rm -f *.aux *.log *.out *.toc

.PHONY: all clean
