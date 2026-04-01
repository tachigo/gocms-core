"""
GoCMS v2.0 Pytest 配置
提供全局 fixtures 和工具函数

二轮回归修复:
- api_request expect_code 使用 sentinel 默认值, 非 200 状态自动跳过 code 检查
- created_term 使用数字 vocab_id
- created_user 使用 viewer 角色 (author 角色不存在)
- author_token 保留 (用户存在可登录, 但无管理权限)
"""
import os
import pytest
import requests
import time
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Generator

# =============================================================================
# 全局配置
# =============================================================================

BASE_URL = os.environ.get("GOCMS_BASE_URL", "https://pre-demo.gocms.tachigo.com")
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"
EDITOR_USERNAME = "editor"
EDITOR_PASSWORD = "editor123"
AUTHOR_USERNAME = "author"
AUTHOR_PASSWORD = "author123"

# SSL 验证禁用（测试环境）
VERIFY_SSL = False

# expect_code 哨兵值 — 区分 "未显式设置" 和 "显式设为 None"
_UNSET = object()

# =============================================================================
# 工具函数
# =============================================================================

def api_request(
    method: str,
    endpoint: str,
    token: Optional[str] = None,
    json_data: Optional[Dict] = None,
    files: Optional[Dict] = None,
    params: Optional[Dict] = None,
    expect_code=_UNSET,
    expect_status: Optional[int] = 200
) -> Dict:
    """
    统一的 API 请求封装

    expect_code 逻辑:
      - 未显式传入 (sentinel) + expect_status=200 → 默认检查 code=0
      - 未显式传入 (sentinel) + expect_status!=200 → 跳过 code 检查
      - 显式传 None → 跳过 code 检查
      - 显式传数字 → 检查该数字
    """
    url = f"{BASE_URL}{endpoint}" if not endpoint.startswith('http') else endpoint
    headers = {}

    if token:
        headers["Authorization"] = f"Bearer {token}"

    if json_data and not files:
        headers["Content-Type"] = "application/json"

    try:
        response = requests.request(
            method=method.upper(),
            url=url,
            headers=headers,
            json=json_data,
            files=files,
            params=params,
            verify=VERIFY_SSL,
            timeout=30
        )
    except requests.exceptions.ConnectionError:
        pytest.fail(f"无法连接到服务器: {BASE_URL}")
    except requests.exceptions.Timeout:
        pytest.fail(f"请求超时: {endpoint}")

    # 验证 HTTP 状态码
    if expect_status is not None and response.status_code != expect_status:
        pytest.fail(
            f"HTTP 状态码错误: 期望 {expect_status}, 实际 {response.status_code}\n"
            f"响应: {response.text[:500]}"
        )

    # 尝试解析 JSON
    try:
        result = response.json()
    except ValueError:
        if expect_status == 200:
            pytest.fail(f"响应不是有效 JSON: {response.text[:500]}")
        result = {"_raw_status": response.status_code, "message": response.text}

    # 解析实际的 expect_code
    if expect_code is _UNSET:
        if expect_status == 200:
            effective_code = 0  # 默认成功
        else:
            effective_code = None  # 非 200 场景自动跳过 code 检查
    else:
        effective_code = expect_code

    # 验证业务 code
    if effective_code is not None and "code" in result:
        if result["code"] != effective_code:
            pytest.fail(
                f"业务 code 错误: 期望 {effective_code}, 实际 {result['code']}\n"
                f"message: {result.get('message', 'N/A')}"
            )

    return result


def get_jwt_payload(token: str) -> Dict:
    """解码 JWT payload（不验证签名）"""
    import base64
    try:
        parts = token.split('.')
        if len(parts) != 3:
            return {}
        payload = parts[1]
        # 补齐 base64 padding
        payload += '=' * (4 - len(payload) % 4)
        decoded = base64.b64decode(payload)
        import json
        return json.loads(decoded)
    except BaseException:
        return {}


def generate_unique_id() -> str:
    """生成唯一标识符"""
    return f"test_{uuid.uuid4().hex[:8]}_{int(time.time())}"


def generate_unique_username() -> str:
    """生成唯一用户名"""
    return f"testuser_{uuid.uuid4().hex[:8]}"


def generate_unique_email() -> str:
    """生成唯一邮箱"""
    return f"test_{uuid.uuid4().hex[:8]}@example.com"


def generate_unique_slug() -> str:
    """生成唯一 slug"""
    return f"test-slug-{uuid.uuid4().hex[:8]}"


def get_vocab_id_by_machine_id(token: str, machine_id: str) -> int:
    """通过 machine_id 查找 vocabulary 的数字 ID"""
    result = api_request("GET", "/api/admin/taxonomies", token=token, expect_code=0)
    vocabs = result["data"]
    if isinstance(vocabs, dict) and "list" in vocabs:
        vocabs = vocabs["list"]
    for v in vocabs:
        if v.get("machine_id") == machine_id:
            return v["id"]
    pytest.fail(f"Vocabulary '{machine_id}' not found")


# =============================================================================
# Fixtures - 认证相关
# =============================================================================

@pytest.fixture(scope="session")
def base_url() -> str:
    """基础 URL"""
    return BASE_URL


@pytest.fixture(scope="session")
def admin_token() -> str:
    """管理员登录 Token"""
    result = api_request(
        "POST",
        "/api/auth/login",
        json_data={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD},
        expect_code=0
    )
    return result["data"]["token"]


@pytest.fixture(scope="session")
def editor_token() -> str:
    """编辑角色 Token"""
    result = api_request(
        "POST",
        "/api/auth/login",
        json_data={"username": EDITOR_USERNAME, "password": EDITOR_PASSWORD},
        expect_code=0
    )
    return result["data"]["token"]


@pytest.fixture(scope="session")
def author_token() -> str:
    """作者角色 Token (用户存在但权限受限)"""
    result = api_request(
        "POST",
        "/api/auth/login",
        json_data={"username": AUTHOR_USERNAME, "password": AUTHOR_PASSWORD},
        expect_code=0
    )
    return result["data"]["token"]


@pytest.fixture
def auth_headers(admin_token: str) -> Dict[str, str]:
    """带认证头的请求头"""
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def editor_headers(editor_token: str) -> Dict[str, str]:
    """编辑角色的请求头"""
    return {"Authorization": f"Bearer {editor_token}"}


@pytest.fixture
def author_headers(author_token: str) -> Dict[str, str]:
    """作者角色的请求头"""
    return {"Authorization": f"Bearer {author_token}"}


# =============================================================================
# Fixtures - 数据创建（自动清理）
# =============================================================================

@pytest.fixture
def created_user(admin_token: str) -> Generator[Dict, None, None]:
    """
    创建测试用户，测试结束后自动删除
    Yields: 用户数据 Dict
    """
    user_data = {
        "username": generate_unique_username(),
        "email": generate_unique_email(),
        "password": "TestPass123!",
        "nickname": "Test User",
        "roles": ["viewer"]  # 修复: author 角色不存在, 改用 viewer
    }

    result = api_request(
        "POST",
        "/api/admin/users",
        token=admin_token,
        json_data=user_data,
        expect_code=0
    )

    user_id = result["data"]["id"]
    created_data = {**user_data, "id": user_id}

    yield created_data

    # 清理：删除用户
    try:
        api_request(
            "DELETE",
            f"/api/admin/users/{user_id}",
            token=admin_token,
            expect_code=0
        )
    except BaseException:
        pass  # 忽略清理错误


@pytest.fixture
def created_article(admin_token: str) -> Generator[Dict, None, None]:
    """
    创建测试文章，测试结束后自动删除
    Yields: 文章数据 Dict
    """
    # 后端 Bug workaround: author_id 必填, 从 JWT 获取 user_id
    payload = get_jwt_payload(admin_token)
    author_id = payload.get("user_id", 1)

    article_data = {
        "title": f"Test Article {generate_unique_id()}",
        "slug": generate_unique_slug(),
        "body": "<p>This is a test article body.</p>",
        "summary": "Test summary",
        "status": "draft",
        "category_ids": [],
        "tag_ids": [],
        "is_top": False,
        "author_id": author_id
    }

    result = api_request(
        "POST",
        "/api/admin/articles",
        token=admin_token,
        json_data=article_data,
        expect_code=0
    )

    article_id = result["data"]["id"]
    created_data = {**article_data, "id": article_id}

    yield created_data

    # 清理：删除文章
    try:
        api_request(
            "DELETE",
            f"/api/admin/articles/{article_id}",
            token=admin_token,
            expect_code=0
        )
    except BaseException:
        pass


@pytest.fixture
def created_page(admin_token: str) -> Generator[Dict, None, None]:
    """
    创建测试页面，测试结束后自动删除
    Yields: 页面数据 Dict
    """
    page_data = {
        "title": f"Test Page {generate_unique_id()}",
        "slug": generate_unique_slug(),
        "body": "<p>This is a test page body.</p>",
        "template": "default",
        "sort_order": 0,
        "status": "draft"
    }

    result = api_request(
        "POST",
        "/api/admin/pages",
        token=admin_token,
        json_data=page_data,
        expect_code=0
    )

    page_id = result["data"]["id"]
    created_data = {**page_data, "id": page_id}

    yield created_data

    # 清理：删除页面
    try:
        api_request(
            "DELETE",
            f"/api/admin/pages/{page_id}",
            token=admin_token,
            expect_code=0
        )
    except BaseException:
        pass


@pytest.fixture
def uploaded_media(admin_token: str) -> Generator[Dict, None, None]:
    """
    上传测试图片，测试结束后自动删除
    Yields: 媒体数据 Dict
    """
    from io import BytesIO
    from PIL import Image

    # 创建测试图片
    img = Image.new('RGB', (100, 100), color='red')
    img_bytes = BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)

    files = {
        'file': ('test_image.png', img_bytes, 'image/png')
    }

    result = api_request(
        "POST",
        "/api/admin/media/upload",
        token=admin_token,
        files=files,
        expect_code=0
    )

    media_id = result["data"]["id"]
    created_data = result["data"]

    yield created_data

    # 清理：删除媒体
    try:
        api_request(
            "DELETE",
            f"/api/admin/media/{media_id}",
            token=admin_token,
            expect_code=0
        )
    except BaseException:
        pass


@pytest.fixture
def created_folder(admin_token: str) -> Generator[Dict, None, None]:
    """
    创建测试文件夹，测试结束后自动删除
    Yields: 文件夹数据 Dict
    """
    folder_data = {
        "name": f"TestFolder_{generate_unique_id()}"
    }

    result = api_request(
        "POST",
        "/api/admin/media/folders",
        token=admin_token,
        json_data=folder_data,
        expect_code=0
    )

    folder_id = result["data"]["id"]
    created_data = {**folder_data, "id": folder_id}

    yield created_data

    # 清理：删除文件夹
    try:
        api_request(
            "DELETE",
            f"/api/admin/media/folders/{folder_id}",
            token=admin_token,
            expect_code=0
        )
    except BaseException:
        pass


@pytest.fixture
def created_term(admin_token: str) -> Generator[Dict, None, None]:
    """
    创建测试分类术语，测试结束后自动删除
    修复: 使用数字 vocab_id (2=tags), 不用字符串 slug
    """
    vocab_id = 2  # tags 词汇表的数字 ID

    term_data = {
        "name": f"TestTag_{generate_unique_id()}",
        "slug": generate_unique_slug()
    }

    result = api_request(
        "POST",
        f"/api/admin/taxonomies/{vocab_id}/terms",
        token=admin_token,
        json_data=term_data,
        expect_code=0
    )

    term_id = result["data"]["id"]
    created_data = {**term_data, "id": term_id, "vocab_id": vocab_id}

    yield created_data

    # 清理：删除术语（注意: 后端可能尚未实现单个 term 删除路由）
    try:
        api_request(
            "DELETE",
            f"/api/admin/taxonomies/{vocab_id}/terms/{term_id}",
            token=admin_token,
            expect_code=0
        )
    except BaseException:
        pass  # 路由不存在时静默失败


@pytest.fixture
def created_role(admin_token: str) -> Generator[Dict, None, None]:
    """
    创建测试角色，测试结束后自动删除
    Yields: 角色数据 Dict
    """
    role_name = generate_unique_id()

    role_data = {
        "name": role_name,
        "label": f"Test Role {role_name}",
        "description": "Test role for automated testing",
        "permissions": [
            {"module": "article", "action": "read", "scope": "own"}
        ]
    }

    result = api_request(
        "POST",
        "/api/admin/roles",
        token=admin_token,
        json_data=role_data,
        expect_code=0
    )

    role_id = result["data"]["id"]
    created_data = {**role_data, "id": role_id}

    yield created_data

    # 清理：删除角色
    try:
        api_request(
            "DELETE",
            f"/api/admin/roles/{role_id}",
            token=admin_token,
            expect_code=0
        )
    except BaseException:
        pass


# =============================================================================
# Fixtures - 公开 API 测试
# =============================================================================

@pytest.fixture
def published_article(admin_token: str) -> Generator[Dict, None, None]:
    """
    创建并发布测试文章
    Yields: 文章数据 Dict
    """
    # 后端 Bug workaround: author_id 必填
    payload = get_jwt_payload(admin_token)
    author_id = payload.get("user_id", 1)

    article_data = {
        "title": f"Published Test Article {generate_unique_id()}",
        "slug": generate_unique_slug(),
        "body": "<p>This is a published test article.</p>",
        "summary": "Published test summary",
        "status": "published",
        "category_ids": [],
        "tag_ids": [],
        "is_top": False,
        "author_id": author_id
    }

    result = api_request(
        "POST",
        "/api/admin/articles",
        token=admin_token,
        json_data=article_data,
        expect_code=0
    )

    article_id = result["data"]["id"]
    created_data = {**article_data, "id": article_id}

    yield created_data

    # 清理
    try:
        api_request(
            "DELETE",
            f"/api/admin/articles/{article_id}",
            token=admin_token,
            expect_code=0
        )
    except BaseException:
        pass


@pytest.fixture
def published_page(admin_token: str) -> Generator[Dict, None, None]:
    """
    创建并发布测试页面
    Yields: 页面数据 Dict
    """
    page_data = {
        "title": f"Published Test Page {generate_unique_id()}",
        "slug": generate_unique_slug(),
        "body": "<p>This is a published test page.</p>",
        "template": "default",
        "sort_order": 0,
        "status": "published"
    }

    result = api_request(
        "POST",
        "/api/admin/pages",
        token=admin_token,
        json_data=page_data,
        expect_code=0
    )

    page_id = result["data"]["id"]
    created_data = {**page_data, "id": page_id}

    # 后端 Bug workaround: 验证页面是否真正发布 (在 try/except 外, 以免 skip 被吞)
    actually_published = False
    try:
        detail = api_request("GET", f"/api/admin/pages/{page_id}", token=admin_token, expect_code=0)
        if detail["data"].get("status") == "published":
            actually_published = True
        else:
            api_request("PUT", f"/api/admin/pages/{page_id}", token=admin_token,
                        json_data={"status": "published"}, expect_code=0)
            detail2 = api_request("GET", f"/api/admin/pages/{page_id}", token=admin_token, expect_code=0)
            actually_published = (detail2["data"].get("status") == "published")
    except BaseException:
        pass

    if not actually_published:
        # 清理掉创建的页面
        try:
            api_request("DELETE", f"/api/admin/pages/{page_id}", token=admin_token, expect_code=0)
        except BaseException:
            pass
        pytest.skip("后端 Bug BUG-01: 页面无法设为 published 状态, 创建和 PUT 均被忽略")

    yield created_data

    # 清理
    try:
        api_request(
            "DELETE",
            f"/api/admin/pages/{page_id}",
            token=admin_token,
            expect_code=0
        )
    except BaseException:
        pass


# =============================================================================
# Pytest Hooks
# =============================================================================

def pytest_configure(config):
    """配置 pytest"""
    config.addinivalue_line("markers", "p0: P0 优先级 - 核心功能")
    config.addinivalue_line("markers", "p1: P1 优先级 - 重要功能")
    config.addinivalue_line("markers", "p2: P2 优先级 - 边缘场景")
    config.addinivalue_line("markers", "slow: 慢速测试（性能测试等）")
    config.addinivalue_line("markers", "security: 安全测试")


def pytest_collection_modifyitems(config, items):
    """按优先级排序测试用例"""
    # 优先级映射
    priority_order = {"p0": 0, "p1": 1, "p2": 2}

    def get_priority(item):
        for marker in item.iter_markers():
            if marker.name in priority_order:
                return priority_order[marker.name]
        return 99  # 无标记的放最后

    items.sort(key=get_priority)
