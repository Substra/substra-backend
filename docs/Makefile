mmds = $(shell find ./ -type f -name '*.mmd')
mermaids = $(mmds:.mmd=.svg)

all: doc

docs: doc

doc: $(mermaids) settings_doc

$(mermaids): %.svg: %.mmd
	npx -p @mermaid-js/mermaid-cli@latest mmdc -i $< -o $@ -b #f7f7f7

.PHONY: settings_doc
settings_doc:
	python3 ../tools/build_settings_doc.py
