# GoCMS v2.0 自动化测试框架

> QA Engineer: 阿测 | 版本: v2.0-TC-1.0
> 覆盖 8 个 Module × 55 个 API 端点，330 条测试用例

## 快速开始

### 1. 安装依赖

```bash
cd tests
pip install -r requirements.txt
```

### 2. 配置测试环境

编辑 `conftest.py` 中的配置项：

```python
BASE_URL = "http://localhost:8000"  # GoCMS 服务地址
ADMIN_USERNAME = "admin"            # 管理员账号
ADMIN_PASSWORD = "admin123"         # 管理员密码
```

### 3. 运行测试

**全量测试：**
```bash
pytest tests/ -v
```

**指定 Module 测试：**
```bash
pytest tests/test_user.py -v
pytest tests/test_article.py -v
```

**按优先级运行：**
```bash
# 只运行 P0 用例
pytest tests/ -v -m "p0"

# 运行 P0 + P1
pytest tests/ -v -m "p0 or p1"
```

**生成报告：**
```bash
pytest tests/ -v --html=report.html --self-contained-html
```

## 测试文件说明

| 文件 | 对应 Module | 用例数 |
|------|------------|--------|
| `test_user.py` | user (登录/登出/Profile/用户管理) | 52 |
| `test_permission.py` | permission (角色/权限/RBAC) | 35 |
| `test_article.py` | article (文章 CRUD/发布/公开 API) | 62 |
| `test_page.py` | page (页面管理) | 35 |
| `test_menu.py` | menu (菜单管理) | 28 |
| `test_taxonomy.py` | taxonomy (分类/标签) | 32 |
| `test_media.py` | media (媒体上传/文件夹) | 30 |
| `test_settings.py` | settings (站点配置) | 8 |

## 测试优先级

- **P0**: 核心功能，阻塞性 Bug
- **P1**: 重要功能，一般缺陷
- **P2**: 边缘场景，优化建议

## Fixtures 说明

### 认证相关
- `admin_token` - 管理员登录 Token
- `editor_token` - 编辑角色 Token
- `author_token` - 作者角色 Token
- `auth_headers` - 带认证头的请求头

### 数据相关
- `created_user` - 创建并清理测试用户
- `created_article` - 创建并清理测试文章
- `created_page` - 创建并清理测试页面
- `uploaded_media` - 上传并清理测试媒体

## v1.0 教训融入

| Bug | 检查点 | 相关用例 |
|-----|--------|----------|
| BUG-002 | URL 不含 localhost | MED-R06 |
| BUG-004 | 空列表返回 [] 非 null | ART-L11, MED-F08 |
| BUG-008 | 公开 API 仅 published | ART-P01 |
| BUG-009 | admin scope=all 看全部 | ART-L06 |
| BUG-010 | slug pattern 校验 | ART-C10 |
| BUG-012 | 部分更新不覆盖 | ART-U01 |
| BUG-013 | slug 唯一排除自身 | ART-U03 |
| BUG-014 | author 不可查他人详情 | ART-D04 |
| BUG-015 | XSS sanitize | ART-C12 |
| BUG-016 | 前台 draft 不可见 | ART-P09 |
| BUG-017 | taxonomy 返回正确数组类型 | ART-C13 |
| BUG-018 | 删不存在返回 404 | ART-DEL03 |
| BUG-019 | 更新不存在返回 404 | TAX-U02 |
| BUG-020 | 媒体 URL 非空 | MED-U01 |

## CI/CD 集成

```yaml
# .github/workflows/test.yml
- name: Run Tests
  run: |
    cd tests
    pip install -r requirements.txt
    pytest tests/ -v --tb=short -q
```

## 注意事项

1. **SSL 验证已禁用** - 测试环境使用 `verify=False`
2. **测试数据隔离** - 每个测试用例自动清理创建的数据
3. **并发安全** - 使用 `pytest-xdist` 时可并行运行
4. **Token 失效** - 测试改密码后旧 Token 应失效
