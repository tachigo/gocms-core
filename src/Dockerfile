# GoCMS v2.0 Dockerfile (Runtime Only)
# 本镜像不包含编译环境，需预先运行 build_linux.sh 生成二进制文件

FROM alpine:3.19

# 安装基础运行环境
RUN apk add --no-cache ca-certificates tzdata
WORKDIR /app

# 设置时区
ENV TZ=Asia/Shanghai

# 物理复制宿主机已编译好的二进制文件
# 注意：构建上下文必须包含 gocms 二进制文件
COPY gocms .

# 复制配置文件
COPY config/ ./config/

# 数据存储目录
RUN mkdir -p data

EXPOSE 8080

# 健康检查：由 Nginx 或 Docker 守护进程调用
HEALTHCHECK --interval=30s --timeout=3s CMD wget -qO- http://localhost:8080/health || exit 1

# 启动服务端
ENTRYPOINT ["./gocms", "server"]
