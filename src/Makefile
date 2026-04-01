# GoCMS v2.0 Makefile

APP_NAME := gocms
VERSION  := 2.0.0
BUILD_DIR := build

.PHONY: all build run clean test tidy swagger

all: tidy build

# 下载依赖
tidy:
	go mod tidy

# 编译
build: tidy
	@mkdir -p $(BUILD_DIR)
	go build -ldflags "-s -w -X main.Version=$(VERSION)" -o $(BUILD_DIR)/$(APP_NAME) .

# 开发模式运行
run:
	go run . server

# 清理构建产物
clean:
	rm -rf $(BUILD_DIR) data/*.db

# 单元测试
test:
	go test ./... -v -cover

# Docker 构建
docker:
	docker build -t $(APP_NAME):$(VERSION) .

# 查看 OpenAPI 文档
swagger:
	@echo "Start server first, then visit: http://localhost:8080/swagger"
