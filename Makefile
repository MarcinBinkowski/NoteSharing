ENV ?= acc

TF_DIR    := infra/$(ENV)
ENV_FILE  := $(TF_DIR)/.env

PROJECT_ID := $(shell grep '^TF_VAR_project_id' $(ENV_FILE) 2>/dev/null | cut -d= -f2 | xargs)
REGION     := europe-west1
REGISTRY   := $(REGION)-docker.pkg.dev
IMAGE_BASE := $(REGISTRY)/$(PROJECT_ID)/notes/notes
IMAGE_TAG  := $(IMAGE_BASE):$(shell git rev-parse --short HEAD)

.PHONY: deploy build infra regen-client test lint fmt typecheck help

deploy: build infra

build:
	@test -f "$(ENV_FILE)" || (echo "Missing $(ENV_FILE)"; exit 1)
	gcloud auth configure-docker $(REGISTRY) --quiet
	docker build --platform linux/amd64 -t $(IMAGE_TAG) .
	docker push $(IMAGE_TAG)

infra:
	@test -f "$(ENV_FILE)" || (echo "Missing $(ENV_FILE)"; exit 1)
	set -a && . "$(CURDIR)/$(ENV_FILE)" && set +a && \
	  cd $(TF_DIR) && terraform init -input=false && \
	  terraform apply -var="container_image=$(IMAGE_TAG)"

regen-client:
	cd backend && uv run python -c "import json; from app.main import app; json.dump(app.openapi(), open('../frontend/openapi.json','w'), indent=2)"
	cd frontend && npx orval --config orval.config.ts

test:
	cd backend && uv run pytest tests/ -v

lint:
	cd backend && uv run ruff check .
	cd frontend && npx eslint .

fmt:
	cd backend && uv run ruff format .
	cd frontend && npx prettier --write .

typecheck:
	cd backend && uv run pyright
	cd frontend && npx tsc --noEmit -p tsconfig.app.json

help:
	@echo "Targets: deploy build infra regen-client test lint fmt typecheck"
