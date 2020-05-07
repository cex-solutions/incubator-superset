AWS_REPOSITORY = 771646765151.dkr.ecr.eu-central-1.amazonaws.com
APP_NAME = superset
VERSION_FILE = VERSION
VERSION = $(shell cat ${VERSION_FILE})

version:
	@cat ${VERSION_FILE} | ( IFS=".-" ; read a b c d && \
      if [ "$(RELEASE_TYPE)" = "patch" ]; then echo "$$a.$$b.$$((c + 1))" > ${VERSION_FILE}; \
      elif [ "$(RELEASE_TYPE)" = "minor" ]; then echo "$$a.$$((b + 1)).0" > ${VERSION_FILE}; \
      elif [ "$(RELEASE_TYPE)" = "major" ]; then echo "$$((a + 1)).0.0" > ${VERSION_FILE}; fi)
	@git commit ${VERSION_FILE} -m "$$(cat ${VERSION_FILE})-${PROJECT}"
	@git tag "$$(cat ${VERSION_FILE})-${PROJECT}"
	@git push --tags origin master

build:
	@docker build --build-arg NPM_BUILD_CMD=build --target prod -t $(APP_NAME) .
	@docker tag $(APP_NAME):latest $(AWS_REPOSITORY)/$(APP_NAME):$(VERSION)-$(ENV)


publish: build
	@aws ecr get-login --no-include-email --region=eu-central-1 --profile=cex | sh
	@docker push $(AWS_REPOSITORY)/$(APP_NAME):$(VERSION)

release: version publish