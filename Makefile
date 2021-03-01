AWS_ACCOUNT_ID = 434494845257

ifneq ($(CI), true)
	ENVIRONMENT ?= dev
endif

# The commit hash of the current HEAD of the repo
HEAD_COMMIT_HASH  := $(shell git rev-parse HEAD)


# Work out what version we are building based on the nearest tag to the commit we are building.
# If there are no tags yet, default the version to 0.0.1
VERSION := $(shell git describe --tags $(HEAD_COMMIT_HASH) 2> /dev/null || echo v0.0.1)

STACK_NAME	:= prind-api

.PHONY: git-flow-init
.PHONY: test
.PHONY: version
.PHONY: build
.PHONY: deploy
.PHONY: release-finish
.PHONY: install-test-dependencies

git-flow-init:
ifeq ($(CI), true)
	# When a pipeline is executed, bitbucket only pulls down the specific
	# branch that is needed for the current pipeline execution. `git flow init`
	# tends to fail if the develop branch is not available, so we have to do 
	# some messing around to make sure it's here before we execute `git flow init`.
	git fetch origin "refs/heads/*:refs/remotes/origin/*
	git checkout -b develop origin/develop
	# Switch back to the original branch
	git checkout $(BITBUCKET_BRANCH)
endif
	# and finally, initialise git-flow with all defaults and v prefix for version tags
	git flow init -f -d
	git flow config set versiontagprefix v

install-test-dependencies:
	pip install -r requirements.txt
	pip install -r requirements-dev.txt

test:
	cd test/unit && \
	python3 -m unittest

version:
	@echo $(VERSION)

deploy:
	env \
	echo "Deploying to $(ENVIRONMENT)"
	sls deploy --stage $(ENVIRONMENT)

release-finish:
	# Set GIT_MERGE_AUTOEDIT=no to avoid invoking teh editor when merging
	# to master
	GIT_MERGE_AUTOEDIT=no git flow release finish -p -m "$(BITBUCKET_REPO_FULL_NAME) $(VERSION)"

