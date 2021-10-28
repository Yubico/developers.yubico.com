MAKEFLAGS += -s
MAKEFLAGS += --no-builtin-rules
.SUFFIXES:

define USAGE
make build - build static website
make httpd - serve static website on http://localhost:8080
endef

all:
	$(info $(USAGE))

clean:
	@git clean -fXd
	@docker rmi -f yubico/developers/build
	@docker rmi -f yubico/developers/httpd

docker-build:
	@docker build \
		--build-arg uid=$(shell id -u) \
		--build-arg gid=$(shell id -g) \
		-t yubico/developers/build \
		-f Dockerfile.build .

build: docker-build
	@docker run --rm \
		-v $(shell pwd):/developers:z \
		-e NORELEASES=true \
		yubico/developers/build

build_noprojects: docker-build
	@docker run --rm \
		-v $(shell pwd):/developers:z \
		-e NORELEASES=true \
		-e NOPROJECTS=true \
		yubico/developers/build

docker-httpd:
	@docker build -t yubico/developers/httpd -f Dockerfile.httpd .

httpd: docker-httpd
	@docker run --rm \
		-v $(shell pwd)/htdocs/dist:/var/www/localhost/htdocs:z \
		-p 8080:8080 \
		yubico/developers/httpd

.PHONY: all clean docker-build build docker-httpd httpd
