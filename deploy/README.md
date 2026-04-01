# GoCMS v2.0 部署文档

> 运维负责人：DevOps | 最后更新：2026-03-30

---

## 目录结构

```
deploy/
├── docker-compose.yml          # Docker Compose 主配置
├── .env                         # 环境变量模板
├── config/                      # 应用配置文件（从 src/config 同步）
│   └── config.yaml
├── nginx/
│   ├── gocms-v2.conf           # Nginx 反向代理配置
│   └── ssl/                    # SSL 证书目录
│       ├── gocms.pem
│       └── gocms.key
├── scripts/
│   ├── deploy.sh               # 一键部署脚本
│   └── backup.sh               # 数据备份脚本
├── backups/                     # 备份文件存放目录
└── README.md                    # 本文件
```

---

## 快速开始

### 1. 配置环境变量

```bash
cd /root/tachigo-openclaw/projects/gocms-v2/deploy

# 复制模板
cp .env .env.local

# 编辑配置
vim .env.local
```

**关键配置项：**

| 变量 | 说明 | 示例 |
|------|------|------|
| `GOCMS_JWT_SECRET` | JWT 签名密钥（必须修改！） | `your-random-secret-key` |
| `DOMAIN` | 部署域名 | `pre-demo.gocms.tachigo.com` |
| `HTTP_PORT` | HTTP 端口 | `80` |
| `HTTPS_PORT` | HTTPS 端口 | `443` |

### 2. 准备 SSL 证书

```bash
# 方式 1: 自签名证书（测试用）
mkdir -p nginx/ssl
cd nginx/ssl
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout gocms.key -out gocms.pem \
    -subj "/C=CN/ST=Beijing/L=Beijing/O=GoCMS/CN=pre-demo.gocms.tachigo.com"

# 方式 2: Let's Encrypt（生产用，见下方 SSL 章节）
```

### 3. 同步配置文件

```bash
# 从源码同步配置到部署目录
cp -r ../src/config/* ./config/

# 编辑生产配置
vim ./config/config.yaml
```

### 4. 一键部署

```bash
./scripts/deploy.sh .env.local
```

部署脚本会自动：
- ✅ 构建 Docker 镜像
- ✅ 启动容器
- ✅ 健康检查
- ✅ 失败自动回滚

### 5. 验证

```bash
# 查看服务状态
docker compose ps

# 测试健康端点
curl -s https://pre-demo.gocms.tachigo.com/health | jq .

# 查看日志
docker compose logs -f gocms
```

---

## 架构说明

```
                      ┌──────────────┐
    用户 ──HTTPS──▶   │    Nginx     │
                      │  :443 (SSL)  │
                      └──────┬───────┘
                             │
                ┌────────────┼────────────┐
                │            │            │
                ▼            ▼            ▼
           /uploads/    /api/* /admin   /*
           Nginx 直出    │              │
           (静态文件)     └──────┬───────┘
                               │
                        ┌──────▼───────┐
                        │  GoCMS v2.0  │
                        │    :8080     │
                        └──────┬───────┘
                               │
                        ┌──────▼───────┐
                        │    SQLite    │
                        │  data/       │
                        └──────────────┘
```

---

## SSL 证书（Let's Encrypt）

### 首次申请

```bash
# 1. 确保 HTTP 80 端口已开放

# 2. 申请证书
docker compose run --rm certbot certonly \
    --webroot -w /var/www/certbot \
    -d pre-demo.gocms.tachigo.com \
    --email your-email@example.com \
    --agree-tos --no-eff-email

# 3. 更新 Nginx 配置中的证书路径
#    编辑 nginx/gocms-v2.conf:
#    ssl_certificate     /etc/letsencrypt/live/pre-demo.gocms.tachigo.com/fullchain.pem;
#    ssl_certificate_key /etc/letsencrypt/live/pre-demo.gocms.tachigo.com/privkey.pem;

# 4. 重载 Nginx
docker compose exec nginx nginx -s reload
```

### 自动续期

Compose 中已内置 certbot 容器，每 12 小时自动检查续期。

额外保险：配置 crontab：

```bash
# 每天凌晨 3 点执行
0 3 * * * /root/tachigo-openclaw/projects/gocms-v2/deploy/scripts/ssl-renew.sh >> /var/log/gocms-v2-ssl.log 2>&1
```

---

## 数据备份

### 手动备份

```bash
./scripts/backup.sh                    # 备份到 deploy/backups/
./scripts/backup.sh /mnt/backup        # 备份到指定目录
```

### 自动备份（Crontab）

```bash
# 每天凌晨 3:30 执行
30 3 * * * /root/tachigo-openclaw/projects/gocms-v2/deploy/scripts/backup.sh >> /var/log/gocms-v2-backup.log 2>&1
```

### 备份策略

- **数据库**：使用 SQLite `.backup` 命令在线安全备份 → gzip 压缩
- **保留策略**：自动清理 7 天前的旧备份
- **文件位置**：`deploy/backups/gocms-v2-YYYYMMDD_HHMMSS.db.gz`

---

## 常用命令

```bash
# 查看服务状态
docker compose ps

# 查看日志（最后 100 行）
docker compose logs --tail=100 -f gocms

# 重启应用
docker compose restart gocms

# 重新构建（代码更新后）
./scripts/deploy.sh .env.local

# 进入容器调试
docker exec -it gocms-v2-app sh

# 停止所有服务
docker compose down

# 完全清理（包括数据卷！⚠️）
docker compose down -v
```

---

## 回滚方案

### 应用回滚

```bash
# 1. 停止当前版本
docker compose down

# 2. 切换到旧版本标签（修改 .env.local 中的 GOCMS_VERSION）
vim .env.local

# 3. 重新部署
./scripts/deploy.sh .env.local
```

### 数据库回滚

```bash
# 1. 停服
docker compose stop gocms

# 2. 恢复备份（示例：恢复到 20260330 的备份）
BACKUP_FILE="backups/gocms-v2-20260330_120000.db.gz"
gunzip -c "$BACKUP_FILE" | docker cp - gocms-v2-app:/app/data/gocms.db

# 3. 重启
docker compose start gocms
```

---

## 健康检查

| 端点 | 说明 | 用途 |
|------|------|------|
| `GET /health` | Go 应用原始端点 | Docker HEALTHCHECK |
| `GET /api/health` | Nginx 代理到 `/health` | 外部监控探针 |

响应示例：
```json
{
    "code": 0,
    "message": "ok",
    "data": {
        "name": "GoCMS",
        "version": "2.0.0"
    }
}
```

---

## 部署检查清单

部署前请确认：

- [ ] `.env.local` 中 `GOCMS_JWT_SECRET` 已修改为强密码
- [ ] SSL 证书已就位（`nginx/ssl/` 目录）
- [ ] `nginx/gocms-v2.conf` 中 `server_name` 已更新为实际域名
- [ ] DNS 已解析到服务器 IP
- [ ] 业务配置已同步到 `deploy/config/`
- [ ] Docker 镜像构建成功
- [ ] `GET /health` 响应正常
- [ ] 管理后台可登录 (`/admin`)
- [ ] 前台页面可访问 (`/`)
- [ ] 备份脚本已测试通过
- [ ] 回滚方案已确认

---

## 故障排查

### 容器无法启动

```bash
# 查看详细日志
docker compose logs gocms --no-color

# 检查配置文件
docker exec gocms-v2-app cat /app/config/config.yaml
```

### 数据库权限错误

```bash
# 修复数据目录权限
docker exec gocms-v2-app chmod 755 /app/data
```

### Nginx 502 错误

```bash
# 检查后端是否健康
docker exec gocms-v2-app wget -qO- http://localhost:8080/health

# 检查 Nginx 配置语法
docker compose exec nginx nginx -t
```

---

## 联系

如有问题，请联系：
- 总助（小秘）：项目统筹协调
- DevOps：部署技术支持
