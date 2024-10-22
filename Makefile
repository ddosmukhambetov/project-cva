IMAGE_NAME = project_cva
ENV = --env-file .env

.PHONY: build
build:
	docker build -t $(IMAGE_NAME) .

.PHONY: exec
exec:
	docker run --rm -it $(IMAGE_NAME) /bin/bash

.PHONY: run-parse-data-py
run-parse-data-py:
	docker run --rm -it --volume $(CURDIR)/data:/project-cva/data $(ENV) $(IMAGE_NAME) python3 machine_learning/collect_data/parse_data.py

.PHONY: run-filter-data-py
run-filter-data-py:
	docker run --rm -it --volume $(CURDIR)/data:/project-cva/data $(ENV) $(IMAGE_NAME) python3 machine_learning/collect_data/filter_data.py

.PHONY: clean-images
clean-images:
	docker rmi $(IMAGE_NAME)

