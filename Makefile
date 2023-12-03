.PHONY: build start pnl debug stop help


## 编译
build:
	echo 'biild'
	pip install -e .

## 启动
sync:
	echo 'start'
	python sync.py

pnl:
	echo "pnl"
	python pnl.py


stop:
	echo "stop"

debug:
	echo "debug"
## Show help
help:
	@echo ''
	@echo 'Usage:'
	@echo ' make target'
	@echo ''
	@echo 'Targets:'
	@awk '/^[a-zA-Z\-\_0-9]+:/ { \
	helpMessage = match(lastLine, /^## (.*)/); \
	if (helpMessage) { \
	helpCommand = substr($$1, 0, index($$1, ":")-1); \
	helpMessage = substr(lastLine, RSTART + 3, RLENGTH); \
	printf " %-20s %s\n", helpCommand, helpMessage; \
	} \
	} \
	{ lastLine = $$0 }' $(MAKEFILE_LIST)
