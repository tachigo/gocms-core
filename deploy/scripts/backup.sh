#!/bin/sh
# ============================================================
# GoCMS v2.0 数据备份脚本
#
# 功能:
#   - 自动检测数据库类型（SQLite）
#   - 执行安全备份
#   - 压缩并清理过期备份
#
# 用法:
#   ./scripts/backup.sh                    # 备份到默认目录
#   ./scripts/backup.sh /path/to/backups   # 备份到指定目录
#
# Crontab 示例（每天凌晨 3:30）:
#   30 3 * * * /path/to/deploy/scripts/backup.sh >> /var/log/gocms-v2-backup.log 2>&1
# ============================================================

set -e

DEPLOY_DIR="$(cd "$(dirname "$0")/.." && pwd)"
BACKUP_DIR="${1:-$DEPLOY_DIR/backups}"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
RETAIN_DAYS=7

mkdir -p "$BACKUP_DIR"

cd "$DEPLOY_DIR"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] 开始 GoCMS v2.0 数据备份..."

# ---------- 备份 SQLite 数据库 ----------
BACKUP_FILE="$BACKUP_DIR/gocms-v2-${TIMESTAMP}.db"

# 使用 SQLite .backup 命令（在线安全备份，不影响读写）
if docker ps --format '{{.Names}}' | grep -q 'gocms-v2-app'; then
    log_info() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"; }
    
    log_info "检测到运行中的 gocms-v2-app 容器"
    log_info "执行 SQLite 在线备份..."
    
    docker exec gocms-v2-app sh -c \
        'sqlite3 /app/data/gocms.db ".backup /tmp/gocms-backup.db"' \
        && docker cp gocms-v2-app:/tmp/gocms-backup.db "$BACKUP_FILE" \
        && docker exec gocms-v2-app rm -f /tmp/gocms-backup.db
    
    # 压缩
    gzip "$BACKUP_FILE"
    BACKUP_FILE="${BACKUP_FILE}.gz"
    
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ SQLite 备份完成: $BACKUP_FILE ($(du -h "$BACKUP_FILE" | cut -f1))"
else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ⚠️ 容器未运行，尝试直接备份数据卷..."
    
    # 直接备份 Docker volume
    docker run --rm -v gocms-v2-data:/data alpine \
        tar czf - -C /data . > "$BACKUP_DIR/gocms-v2-${TIMESTAMP}-volume.tar.gz"
    
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ 数据卷备份完成: gocms-v2-${TIMESTAMP}-volume.tar.gz"
fi

# ---------- 上传目录备份（可选，取消注释启用）----------
# echo "[$(date '+%Y-%m-%d %H:%M:%S')] 备份上传目录..."
# UPLOADS_BACKUP="$BACKUP_DIR/gocms-v2-uploads-${TIMESTAMP}.tar.gz"
# docker run --rm -v gocms-v2-uploads:/data alpine \
#     tar czf - -C /data . > "$UPLOADS_BACKUP"
# echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ Uploads 备份完成: $UPLOADS_BACKUP"

# ---------- 清理过期备份 ----------
DELETED=$(find "$BACKUP_DIR" -name "gocms-v2-*" -mtime +"$RETAIN_DAYS" -delete -print 2>/dev/null | wc -l)
if [ "$DELETED" -gt 0 ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] 🗑️ 已清理 ${DELETED} 个过期备份（保留 ${RETAIN_DAYS} 天）"
fi

# ---------- 备份统计 ----------
BACKUP_COUNT=$(find "$BACKUP_DIR" -name "gocms-v2-*" -type f | wc -l)
BACKUP_SIZE=$(du -sh "$BACKUP_DIR" 2>/dev/null | cut -f1)

echo "[$(date '+%Y-%m-%d %H:%M:%S')] 📊 备份统计: ${BACKUP_COUNT} 个文件，总计 ${BACKUP_SIZE}"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ 备份流程完成"
