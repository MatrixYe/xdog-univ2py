.PHONY: build sync pnl debug stop help

#c=""
## 编译
build:
	echo 'biild'

## 启动同步器
sync:
	echo 'start'
	python sync.py

## 启动盈利统计任务
pnl:
	python pnl.py $(c)

## 停止
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
