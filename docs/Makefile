mmds = $(shell find ./ -type f -name '*.mmd')
mermaids = $(mmds:.mmd=.png)

all: doc

docs: doc

doc: $(mermaids)

$(mermaids): %.png: %.mmd
	mmdc -i $< -o $@ -b #f7f7f7
