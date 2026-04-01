# GoCMS v2.0 Dockerfile
# 多阶段构建：编译 → 最小运行时镜像

# === 编译阶段 ===
FROM golang:1.22-alpine AS builder
RUN apk add --no-cache git
WORKDIR /src
COPY go.mod go.sum ./
ENV GOPROXY=https://goproxy.cn,direct
RUN go mod download
COPY . .
RUN go build -ldflags "-s -w" -o /app/gocms .

# === 运行阶段 ===
FROM alpine:3.19
RUN apk add --no-cache ca-certificates tzdata
WORKDIR /app

# 从编译阶段复制二进制
COPY --from=builder /app/gocms .

# 复制配置文件
COPY config/ ./config/

# 数据目录
RUN mkdir -p data

EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=3s CMD wget -qO- http://localhost:8080/health || exit 1
ENTRYPOINT ["./gocms", "server"]
