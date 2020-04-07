NODE:=node --experimental-modules --no-warnings
DATASET:=data/jmb22

all: help

tag:
	@$(NODE) tagger/server.js $(DATASET)

help:
	@echo "Usage: make <target>"
