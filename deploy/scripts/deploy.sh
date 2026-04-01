#!/bin/sh
# ============================================================
# GoCMS v2.0 一键部署脚本
#
# 功能:
#   1. 构建 Docker 镜像
#   2. 停止旧容器（如有）
#   3. 启动新容器
#   4. 健康检查
#   5. 失败时回滚
#
# 用法:
#   ./scripts/deploy.sh           # 使用 .env 文件
#   ./scripts/deploy.sh .env.prod # 使用指定 env 文件
# ============================================================

set -e

# ---------- 配置 ----------
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DEPLOY_DIR="$(dirname "$SCRIPT_DIR")"
ENV_FILE="${1:-$DEPLOY_DIR/.env}"
COMPOSE_FILE="$DEPLOY_DIR/docker-compose.yml"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# ---------- 前置检查 ----------
if [ ! -f "$ENV_FILE" ]; then
    log_error "环境文件不存在: $ENV_FILE"
    log_info "请复制 .env 模板并配置: cp $DEPLOY_DIR/.env $ENV_FILE"
    exit 1
fi

if [ ! -f "$COMPOSE_FILE" ]; then
    log_error "Compose 文件不存在: $COMPOSE_FILE"
    exit 1
fi

log_info "使用环境文件: $ENV_FILE"
cd "$DEPLOY_DIR"

# 加载环境变量（仅用于脚本内的值显示）
export $(grep -v '^#' "$ENV_FILE" | xargs)

log_info "开始部署 GoCMS v2.0..."
log_info "目标域名: ${DOMAIN:-pre-demo.gocms.tachigo.com}"
log_info "镜像版本: ${GOCMS_VERSION:-2.0.0}"

# ---------- 步骤 1: 构建镜像 ----------
log_info "[1/5] 构建 Docker 镜像..."
docker compose --env-file "$ENV_FILE" build --no-cache gocms

# ---------- 步骤 2: 备份当前运行状态 ----------
log_info "[2/5] 检查现有容器..."
OLD_CONTAINER=$(docker ps -q -f name=gocms-v2-app 2>/dev/null || true)
if [ -n "$OLD_CONTAINER" ]; then
    log_warn "发现运行中的旧容器，将平滑替换..."
fi

# ---------- 步骤 3: 启动新容器 ----------
log_info "[3/5] 启动新容器..."
docker compose --env-file "$ENV_FILE" up -d

# ---------- 步骤 4: 健康检查 ----------
log_info "[4/5] 等待健康检查..."
MAX_RETRIES=30
RETRY_COUNT=0
HEALTHY=false

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    sleep 2
    
    # 检查容器是否健康
    HEALTH_STATUS=$(docker inspect --format='{{.State.Health.Status}}' gocms-v2-app 2>/dev/null || echo "unknown")
    
    if [ "$HEALTH_STATUS" = "healthy" ]; then
        HEALTHY=true
        break
    fi
    
    # 检查容器是否还在运行
    CONTAINER_STATE=$(docker inspect --format='{{.State.Status}}' gocms-v2-app 2>/dev/null || echo "not found")
    if [ "$CONTAINER_STATE" = "exited" ] || [ "$CONTAINER_STATE" = "dead" ]; then
        log_error "容器异常退出！"
        break
    fi
    
    RETRY_COUNT=$((RETRY_COUNT + 1))
    echo -n "."
done

echo ""

if [ "$HEALTHY" = true ]; then
    log_info "[5/5] ✅ 部署成功！"
    log_info "应用状态:"
    docker compose --env-file "$ENV_FILE" ps
    
    # 测试健康端点
    HEALTH_RESPONSE=$(docker exec gocms-v2-app wget -qO- http://localhost:8080/health 2>/dev/null || echo "failed")
    log_info "健康检查响应: $HEALTH_RESPONSE"
    
    log_info ""
    log_info "访问地址:"
    log_info "  - HTTP:  http://${DOMAIN:-pre-demo.gocms.tachigo.com}"
    log_info "  - HTTPS: https://${DOMAIN:-pre-demo.gocms.tachigo.com}"
    
    # 清理旧镜像
    docker image prune -f > /dev/null 2>&1 || true
    
    exit 0
else
    log_error "[5/5] ❌ 健康检查失败！"
    
    # 显示容器日志
    log_error "容器日志（最后 50 行）:"
    docker logs --tail 50 gocms-v2-app 2>&1 || true
    
    # 回滚
    log_warn "执行回滚..."
    docker compose --env-file "$ENV_FILE" down
    
    if [ -n "$OLD_CONTAINER" ]; then
        log_warn "尝试恢复旧容器..."
        docker start "$OLD_CONTAINER" 2>/dev/null || true
    fi
    
    exit 1
fi
