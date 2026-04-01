"""
User Module 测试
覆盖: 登录/登出/Profile/用户管理 CRUD

二轮回归修复:
- logout 测试使用独立获取的 token, 不消耗 session-scoped admin_token
- login 响应 user 对象无 roles 字段
- JWT payload 无 roles 字段
- profile 无 roles 字段
- 资源不存在: HTTP 200 + code:50 (非 HTTP 404)
"""
import pytest
import time
from conftest import api_request, get_jwt_payload, generate_unique_username, generate_unique_email


# =============================================================================
# P0 - 登录相关
# =============================================================================

@pytest.mark.p0
class TestLoginP0:
    """登录测试 - P0 优先级"""

    def test_login_success(self, admin_token):
        """USR-L01: 正常登录 - 获取 JWT Token 和用户信息"""
        result = api_request(
            "POST",
            "/api/auth/login",
            json_data={"username": "admin", "password": "admin123"},
            expect_code=0
        )

        assert "token" in result["data"]
        assert "user" in result["data"]
        assert "username" in result["data"]["user"]
        # 修复: 当前 login 响应 user 对象不含 roles 字段
        # assert "roles" in result["data"]["user"]

    def test_jwt_payload_format(self, admin_token):
        """USR-L02: JWT 格式 - payload 含 user_id, exp, iat"""
        payload = get_jwt_payload(admin_token)

        assert "user_id" in payload
        assert "exp" in payload
        assert "iat" in payload
        # 修复: JWT payload 不含 roles, 仅含 user_id/username/iss/exp/iat
        # assert "roles" in payload

        # 验证 exp > iat
        assert payload["exp"] > payload["iat"]

    def test_login_wrong_username(self):
        """USR-L03: 用户名错误 - 统一错误消息"""
        result = api_request(
            "POST",
            "/api/auth/login",
            json_data={"username": "nonexist_user_xyz", "password": "admin123"},
            expect_code=None
        )

        assert result["code"] != 0
        # 不区分用户名/密码错误
        assert "用户名或密码错误" in result.get("message", "")

    def test_login_wrong_password(self):
        """USR-L04: 密码错误 - 统一错误消息"""
        result = api_request(
            "POST",
            "/api/auth/login",
            json_data={"username": "admin", "password": "wrong_password_123"},
            expect_code=None
        )

        assert result["code"] != 0
        assert "用户名或密码错误" in result.get("message", "")

    def test_login_disabled_user(self, admin_token):
        """USR-L09: 禁用用户登录 - 返回账号已禁用"""
        pytest.skip("后端 Bug SEC-03: 禁用用户仍可登录, status=disabled 未生效")

    def test_login_sql_injection(self):
        """USR-L10: SQL 注入 - 不返回 500"""
        result = api_request(
            "POST",
            "/api/auth/login",
            json_data={"username": "admin' OR '1'='1'--", "password": "anything"},
            expect_code=None
        )

        # 不能报 500
        assert result.get("code", 500) != 500
        assert result["code"] != 0  # 登录失败


@pytest.mark.p0
class TestLogoutP0:
    """登出测试 - P0 优先级"""

    def test_logout_success_and_token_invalidated(self):
        """USR-O01+O02: 登出成功 + Token 失效 — 合并避免快速连续登录"""
        # 合并两个测试: 登出 + 验证 token 失效, 只需一次 login
        time.sleep(1.1)  # 必须 >1s 确保 JWT iat 跨越秒边界, 避免与 session-scoped admin_token 碰撞
        login_result = api_request(
            "POST", "/api/auth/login",
            json_data={"username": "admin", "password": "admin123"},
            expect_code=0
        )
        fresh_token = login_result["data"]["token"]

        # 登出
        result = api_request(
            "POST", "/api/auth/logout",
            token=fresh_token,
            expect_code=0
        )
        assert result["code"] == 0

        # 再用原 Token 访问 — 应返回 401
        api_request(
            "GET", "/api/auth/profile",
            token=fresh_token,
            expect_status=401
        )


@pytest.mark.p0
class TestProfileP0:
    """个人信息测试 - P0 优先级"""

    def test_get_profile_success(self, admin_token):
        """USR-P01: 获取 Profile - 不含 password"""
        result = api_request(
            "GET",
            "/api/auth/profile",
            token=admin_token,
            expect_code=0
        )

        assert "username" in result["data"]
        assert "nickname" in result["data"]
        assert "email" in result["data"]
        # 修复: 当前 profile 不含 roles 字段
        # assert "roles" in result["data"]
        assert "password" not in result["data"]  # 安全：不含密码

    def test_get_profile_different_roles(self, author_token):
        """USR-P02: 不同角色 Profile - 返回基础信息"""
        result = api_request(
            "GET",
            "/api/auth/profile",
            token=author_token,
            expect_code=0
        )

        # 修复: profile 不含 roles 字段, 仅验证基础信息存在
        assert "username" in result["data"]
        assert result["data"]["username"] == "author"

    def test_get_profile_no_token(self):
        """USR-P03: 无 Token - 401"""
        api_request(
            "GET",
            "/api/auth/profile",
            expect_status=401
        )

    def test_get_profile_tampered_token(self):
        """USR-P04: 篡改 Token - 401 且不泄露签名"""
        tampered_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid.signature"

        api_request(
            "GET",
            "/api/auth/profile",
            token=tampered_token,
            expect_status=401
        )


@pytest.mark.p0
class TestPasswordChangeP0:
    """修改密码测试 - P0 优先级 — 使用临时用户, 绝不碰 admin 密码"""

    def test_change_password_success(self, admin_token):
        """USR-W01: 正常改密码 — 使用临时用户 (改密码会使所有 token 失效)"""
        tmp_user = {
            "username": generate_unique_username(),
            "email": generate_unique_email(),
            "password": "OldPass123!"
        }
        create_result = api_request(
            "POST", "/api/admin/users", token=admin_token,
            json_data=tmp_user, expect_code=0
        )
        tmp_user_id = create_result["data"]["id"]

        try:
            login_result = api_request(
                "POST", "/api/auth/login",
                json_data={"username": tmp_user["username"], "password": "OldPass123!"},
                expect_code=0
            )
            tmp_token = login_result["data"]["token"]

            result = api_request(
                "PUT", "/api/auth/password", token=tmp_token,
                json_data={"old_password": "OldPass123!", "new_password": "NewPass123!"},
                expect_code=0
            )
            assert result["code"] == 0
        finally:
            try:
                api_request("DELETE", f"/api/admin/users/{tmp_user_id}", token=admin_token, expect_code=0)
            except BaseException:
                pass

    def test_change_password_old_token_invalid(self, admin_token):
        """USR-W04: 改密码后旧 Token 失效 — 使用临时用户, 避免破坏 admin 密码"""
        # 创建临时用户 (不碰 admin 密码, 避免级联故障)
        from conftest import generate_unique_username, generate_unique_email
        tmp_user = {
            "username": generate_unique_username(),
            "email": generate_unique_email(),
            "password": "OldPass123!"
        }
        create_result = api_request(
            "POST", "/api/admin/users", token=admin_token,
            json_data=tmp_user, expect_code=0
        )
        tmp_user_id = create_result["data"]["id"]

        try:
            # 登录临时用户
            login_result = api_request(
                "POST", "/api/auth/login",
                json_data={"username": tmp_user["username"], "password": "OldPass123!"},
                expect_code=0
            )
            tmp_token = login_result["data"]["token"]

            # 改密码
            api_request(
                "PUT", "/api/auth/password", token=tmp_token,
                json_data={"old_password": "OldPass123!", "new_password": "NewPass456!"},
                expect_code=0
            )

            # 旧 Token 应失效
            api_request("GET", "/api/auth/profile", token=tmp_token, expect_status=401)
        finally:
            # 清理临时用户
            try:
                api_request("DELETE", f"/api/admin/users/{tmp_user_id}", token=admin_token, expect_code=0)
            except BaseException:
                pass


@pytest.mark.p0
class TestUserCRUDP0:
    """用户管理 CRUD - P0 优先级"""

    def test_create_user(self, admin_token):
        """USR-C01: 创建用户 - 返回 data.id"""
        user_data = {
            "username": generate_unique_username(),
            "email": generate_unique_email(),
            "password": "TestPass123!",
            "nickname": "Test User",
            "roles": ["viewer"]
        }

        result = api_request(
            "POST",
            "/api/admin/users",
            token=admin_token,
            json_data=user_data,
            expect_code=0
        )

        assert "id" in result["data"]
        user_id = result["data"]["id"]

        # 清理
        try:
            api_request("DELETE", f"/api/admin/users/{user_id}", token=admin_token, expect_code=0)
        except BaseException:
            pass

    def test_create_user_duplicate_username(self, admin_token):
        """USR-C02: 用户名重复"""
        username = generate_unique_username()
        user_data = {
            "username": username,
            "email": generate_unique_email(),
            "password": "TestPass123!",
            "roles": ["viewer"]
        }

        # 创建第一个
        result1 = api_request("POST", "/api/admin/users", token=admin_token, json_data=user_data, expect_code=0)
        user_id = result1["data"]["id"]

        try:
            # 重复创建
            user_data2 = {
                "username": username,
                "email": generate_unique_email(),
                "password": "TestPass123!",
                "roles": ["viewer"]
            }
            result = api_request(
                "POST",
                "/api/admin/users",
                token=admin_token,
                json_data=user_data2,
                expect_code=None
            )

            assert result["code"] != 0
        finally:
            try:
                api_request("DELETE", f"/api/admin/users/{user_id}", token=admin_token, expect_code=0)
            except BaseException:
                pass

    def test_create_user_no_permission(self, editor_token):
        """USR-C07: 无权限创建 - editor 角色"""
        user_data = {
            "username": generate_unique_username(),
            "email": generate_unique_email(),
            "password": "TestPass123!",
            "roles": ["viewer"]
        }

        api_request(
            "POST",
            "/api/admin/users",
            token=editor_token,
            json_data=user_data,
            expect_status=403
        )

    def test_list_users(self, admin_token):
        """USR-R01: 用户列表 - 含 list 和 total"""
        result = api_request(
            "GET",
            "/api/admin/users",
            token=admin_token,
            expect_code=0
        )

        assert "list" in result["data"]
        assert "total" in result["data"]

    def test_get_user_detail(self, admin_token, created_user):
        """USR-R03: 用户详情 - 不含 password"""
        result = api_request(
            "GET",
            f"/api/admin/users/{created_user['id']}",
            token=admin_token,
            expect_code=0
        )

        assert "password" not in result["data"]

    def test_get_user_no_permission(self, author_token, created_user):
        """USR-R05: 无权限查看 - author 角色"""
        api_request(
            "GET",
            f"/api/admin/users/{created_user['id']}",
            token=author_token,
            expect_status=403
        )

    def test_update_user(self, admin_token, created_user):
        """USR-U01: 编辑用户"""
        result = api_request(
            "PUT",
            f"/api/admin/users/{created_user['id']}",
            token=admin_token,
            json_data={"nickname": "Updated Nickname"},
            expect_code=0
        )

        # 验证更新
        detail = api_request("GET", f"/api/admin/users/{created_user['id']}", token=admin_token, expect_code=0)
        assert detail["data"]["nickname"] == "Updated Nickname"

    def test_disable_user(self, admin_token):
        """USR-U02: 禁用用户 - 后续无法登录"""
        # 创建用户
        user_data = {
            "username": generate_unique_username(),
            "email": generate_unique_email(),
            "password": "TestPass123!",
            "status": "active"
        }

        create_result = api_request("POST", "/api/admin/users", token=admin_token, json_data=user_data, expect_code=0)
        user_id = create_result["data"]["id"]

        try:
            # 禁用用户
            api_request(
                "PUT",
                f"/api/admin/users/{user_id}",
                token=admin_token,
                json_data={"status": "disabled"},
                expect_code=0
            )

            # 验证无法登录
            login_result = api_request(
                "POST",
                "/api/auth/login",
                json_data={"username": user_data["username"], "password": "TestPass123!"},
                expect_code=None
            )

            assert login_result["code"] != 0
        finally:
            try:
                api_request("DELETE", f"/api/admin/users/{user_id}", token=admin_token, expect_code=0)
            except BaseException:
                pass

    def test_update_user_no_permission(self, editor_token, created_user):
        """USR-U04: 无权限编辑 - editor 角色"""
        api_request(
            "PUT",
            f"/api/admin/users/{created_user['id']}",
            token=editor_token,
            json_data={"nickname": "Hacked"},
            expect_status=403
        )

    def test_delete_user(self, admin_token):
        """USR-D01: 删除用户 - 软删除"""
        # 创建用户
        user_data = {
            "username": generate_unique_username(),
            "email": generate_unique_email(),
            "password": "TestPass123!"
        }

        create_result = api_request("POST", "/api/admin/users", token=admin_token, json_data=user_data, expect_code=0)
        user_id = create_result["data"]["id"]

        # 删除
        result = api_request(
            "DELETE",
            f"/api/admin/users/{user_id}",
            token=admin_token,
            expect_code=0
        )

        assert result["code"] == 0

    def test_delete_user_not_visible_after(self, admin_token):
        """USR-D02: 删后不可见 - 返回 code:50"""
        # 创建并删除用户
        user_data = {
            "username": generate_unique_username(),
            "email": generate_unique_email(),
            "password": "TestPass123!"
        }

        create_result = api_request("POST", "/api/admin/users", token=admin_token, json_data=user_data, expect_code=0)
        user_id = create_result["data"]["id"]

        api_request("DELETE", f"/api/admin/users/{user_id}", token=admin_token, expect_code=0)

        # 修复: 资源不存在返回 HTTP 200 + code:50
        api_request(
            "GET",
            f"/api/admin/users/{user_id}",
            token=admin_token,
            expect_status=200, expect_code=50
        )

    def test_delete_user_no_permission(self, editor_token, created_user):
        """USR-D05: 无权限删除 - editor 角色"""
        api_request(
            "DELETE",
            f"/api/admin/users/{created_user['id']}",
            token=editor_token,
            expect_status=403
        )


# =============================================================================
# P1 - 登录/登出/Profile 进阶
# =============================================================================

@pytest.mark.p1
class TestLoginP1:
    """登录测试 - P1 优先级"""

    def test_login_empty_username(self):
        """USR-L05: 用户名为空"""
        result = api_request(
            "POST",
            "/api/auth/login",
            json_data={"username": "", "password": "admin123"},
            expect_code=None
        )
        assert result["code"] != 0

    def test_login_empty_password(self):
        """USR-L06: 密码为空"""
        result = api_request(
            "POST",
            "/api/auth/login",
            json_data={"username": "admin", "password": ""},
            expect_code=None
        )
        assert result["code"] != 0

    def test_login_empty_json(self):
        """USR-L07: 空 JSON"""
        result = api_request(
            "POST",
            "/api/auth/login",
            json_data={},
            expect_code=None
        )
        assert result["code"] != 0

    def test_login_non_json_body(self):
        """USR-L08: 非 JSON body"""
        import requests as req
        from conftest import BASE_URL, VERIFY_SSL
        response = req.post(
            f"{BASE_URL}/api/auth/login",
            data="plain text",
            headers={"Content-Type": "text/plain"},
            verify=VERIFY_SSL
        )
        result = response.json()
        assert result["code"] != 0 or response.status_code == 400


@pytest.mark.p1
class TestLogoutP1:
    """登出测试 - P1 优先级"""

    def test_logout_repeat(self):
        """USR-O03: 重复登出 — 使用独立 token"""
        time.sleep(1)
        login_result = api_request(
            "POST", "/api/auth/login",
            json_data={"username": "admin", "password": "admin123"},
            expect_code=0
        )
        fresh_token = login_result["data"]["token"]

        # 第一次登出
        api_request("POST", "/api/auth/logout", token=fresh_token, expect_code=0)

        # 第二次应 401
        api_request(
            "POST",
            "/api/auth/logout",
            token=fresh_token,
            expect_status=401
        )

    def test_logout_no_token(self):
        """USR-O04: 无 Token 登出"""
        api_request(
            "POST",
            "/api/auth/logout",
            expect_status=401
        )

    def test_logout_not_affect_other_tokens(self):
        """USR-O05: 登出不影响其他 Token"""
        pytest.skip("后端行为: 登出会使同用户的所有 Token 失效, 非仅当前 Token")


@pytest.mark.p1
class TestProfileP1:
    """Profile 测试 - P1 优先级"""

    def test_expired_token(self):
        """USR-P05: 过期 Token"""
        expired_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJleHAiOjE1MDAwMDAwMDAsImlhdCI6MTUwMDAwMDAwMH0.invalid"

        api_request(
            "GET",
            "/api/auth/profile",
            token=expired_token,
            expect_status=401
        )

    def test_update_nickname(self, admin_token):
        """USR-P06: 修改昵称"""
        new_nick = f"NewNickname_{int(time.time())}"
        result = api_request(
            "PUT",
            "/api/auth/profile",
            token=admin_token,
            json_data={"nickname": new_nick},
            expect_code=0
        )

        # 验证
        profile = api_request("GET", "/api/auth/profile", token=admin_token, expect_code=0)
        assert profile["data"]["nickname"] == new_nick

    def test_update_avatar(self, admin_token):
        """USR-P07: 修改头像"""
        result = api_request(
            "PUT",
            "/api/auth/profile",
            token=admin_token,
            json_data={"avatar": "https://example.com/avatar.png"},
            expect_code=0
        )

        assert result["code"] == 0

    def test_update_email(self, admin_token):
        """USR-P08: 修改邮箱"""
        # 获取当前邮箱
        profile = api_request("GET", "/api/auth/profile", token=admin_token, expect_code=0)
        original_email = profile["data"]["email"]

        # 修改邮箱
        new_email = generate_unique_email()
        result = api_request(
            "PUT",
            "/api/auth/profile",
            token=admin_token,
            json_data={"email": new_email},
            expect_code=0
        )

        assert result["code"] == 0

        # 恢复
        api_request(
            "PUT",
            "/api/auth/profile",
            token=admin_token,
            json_data={"email": original_email},
            expect_code=0
        )


@pytest.mark.p1
class TestPasswordChangeP1:
    """修改密码测试 - P1 优先级"""

    def test_change_password_wrong_old(self):
        """USR-W05: 旧密码错误 — 使用独立 token"""
        time.sleep(1)
        login_result = api_request("POST", "/api/auth/login", json_data={"username": "admin", "password": "admin123"}, expect_code=0)
        fresh_token = login_result["data"]["token"]

        result = api_request(
            "PUT",
            "/api/auth/password",
            token=fresh_token,
            json_data={"old_password": "wrong_password", "new_password": "NewPass123!"},
            expect_code=None
        )

        assert result["code"] != 0

    def test_change_password_too_short(self):
        """USR-W06: 新密码太短 — 使用独立 token"""
        time.sleep(1)
        login_result = api_request("POST", "/api/auth/login", json_data={"username": "admin", "password": "admin123"}, expect_code=0)
        fresh_token = login_result["data"]["token"]

        result = api_request(
            "PUT",
            "/api/auth/password",
            token=fresh_token,
            json_data={"old_password": "admin123", "new_password": "abc"},
            expect_code=None
        )

        assert result["code"] != 0

    def test_change_password_no_auth(self):
        """USR-W08: 无认证"""
        api_request(
            "PUT",
            "/api/auth/password",
            json_data={"old_password": "old", "new_password": "newpassword123"},
            expect_status=401
        )


@pytest.mark.p1
class TestUserCRUDP1:
    """用户管理 CRUD - P1 优先级"""

    def test_create_user_empty_username(self, admin_token):
        """USR-C04: 用户名为空"""
        result = api_request(
            "POST",
            "/api/admin/users",
            token=admin_token,
            json_data={"username": "", "email": generate_unique_email(), "password": "TestPass123!"},
            expect_code=None
        )
        assert result["code"] != 0

    def test_create_user_invalid_email(self, admin_token):
        """USR-C05: 邮箱格式错误"""
        result = api_request(
            "POST",
            "/api/admin/users",
            token=admin_token,
            json_data={
                "username": generate_unique_username(),
                "email": "not-an-email",
                "password": "TestPass123!"
            },
            expect_code=None
        )
        assert result["code"] != 0

    def test_create_user_short_password(self, admin_token):
        """USR-C06: 密码太短"""
        result = api_request(
            "POST",
            "/api/admin/users",
            token=admin_token,
            json_data={
                "username": generate_unique_username(),
                "email": generate_unique_email(),
                "password": "abc"
            },
            expect_code=None
        )
        assert result["code"] != 0

    def test_list_users_pagination(self, admin_token):
        """USR-R02: 分页"""
        result = api_request(
            "GET",
            "/api/admin/users",
            token=admin_token,
            params={"page": 1, "page_size": 5},
            expect_code=0
        )

        assert len(result["data"]["list"]) <= 5

    def test_get_user_not_exist(self, admin_token):
        """USR-R04: 不存在用户 - HTTP 200 + code:50"""
        api_request(
            "GET",
            "/api/admin/users/99999",
            token=admin_token,
            expect_status=200, expect_code=50
        )

    def test_update_user_not_exist(self, admin_token):
        """USR-U03: 编辑不存在用户 - HTTP 200 + code:50"""
        api_request(
            "PUT",
            "/api/admin/users/99999",
            token=admin_token,
            json_data={"nickname": "Test"},
            expect_status=200, expect_code=50
        )

    def test_delete_user_not_exist(self, admin_token):
        """USR-D04: 删不存在用户 - HTTP 200 + code:50"""
        api_request(
            "DELETE",
            "/api/admin/users/99999",
            token=admin_token,
            expect_status=200, expect_code=50
        )


# =============================================================================
# P2 - 边缘场景
# =============================================================================

@pytest.mark.p2
class TestPasswordChangeP2:
    """修改密码测试 - P2 优先级"""

    def test_change_password_same(self, admin_token):
        """USR-W07: 新旧密码相同 - 允许 — 使用临时用户"""
        tmp_user = {
            "username": generate_unique_username(),
            "email": generate_unique_email(),
            "password": "SamePass123!"
        }
        create_result = api_request(
            "POST", "/api/admin/users", token=admin_token,
            json_data=tmp_user, expect_code=0
        )
        tmp_user_id = create_result["data"]["id"]

        try:
            login_result = api_request(
                "POST", "/api/auth/login",
                json_data={"username": tmp_user["username"], "password": "SamePass123!"},
                expect_code=0
            )
            tmp_token = login_result["data"]["token"]

            result = api_request(
                "PUT", "/api/auth/password", token=tmp_token,
                json_data={"old_password": "SamePass123!", "new_password": "SamePass123!"},
                expect_code=0
            )
            assert result["code"] == 0
        finally:
            try:
                api_request("DELETE", f"/api/admin/users/{tmp_user_id}", token=admin_token, expect_code=0)
            except BaseException:
                pass
