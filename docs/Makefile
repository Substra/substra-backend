mmds = $(shell find ./ -type f -name '*.mmd')
mermaids = $(mmds:.mmd=.png)

all: doc

docs: doc

doc: $(mermaids) settings_doc

$(mermaids): %.png: %.mmd
	mmdc -i $< -o $@ -b #f7f7f7

.PHONY: settings_doc
settings_doc:
	python3 ../tools/build_settings_doc.py
