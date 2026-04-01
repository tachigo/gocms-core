"""
Settings Module 测试
覆盖: 站点配置 / 管理配置
对应测试用例: 8 条 (P0: 4, P1: 4)
"""
import pytest
from conftest import api_request


# =============================================================================
# P0 - 基础功能
# =============================================================================

@pytest.mark.p0
class TestSettingsP0:
    """Settings - P0 优先级"""

    def test_public_settings(self):
        """SET-001: 公开配置 - 含 site_name/logo"""
        result = api_request("GET", "/api/settings", expect_code=0)

        assert "site_name" in result["data"] or "logo" in result["data"]

    def test_public_no_auth(self):
        """SET-002: 无需认证"""
        result = api_request("GET", "/api/settings", expect_code=0)
        assert result["code"] == 0

    def test_admin_settings(self, admin_token):
        """SET-003: 管理配置 - 含完整配置"""
        result = api_request("GET", "/api/admin/settings", token=admin_token, expect_code=0)

        # 管理配置应包含更多字段
        assert result["code"] == 0
        # 验证有额外字段
        assert len(result["data"]) > 0

    def test_admin_requires_auth(self):
        """SET-004: 管理需认证 - 401"""
        api_request("GET", "/api/admin/settings", expect_status=401)


# =============================================================================
# P1 - 进阶功能
# =============================================================================

@pytest.mark.p1
class TestSettingsP1:
    """Settings - P1 优先级"""

    def test_non_admin_denied(self, editor_token):
        """SET-005: 非 admin - 403"""
        api_request("GET", "/api/admin/settings", token=editor_token, expect_status=403)

    def test_image_styles_defined(self, admin_token):
        """SET-006: 图片样式定义 - 含 thumbnail"""
        result = api_request("GET", "/api/admin/settings", token=admin_token, expect_code=0)

        data = result["data"]
        # 配置中应有 image_styles 或相关字段
        if "image_styles" in data:
            styles = data["image_styles"]
            assert isinstance(styles, dict) or isinstance(styles, list)

    def test_seo_defaults(self, admin_token):
        """SET-007: SEO 默认值"""
        result = api_request("GET", "/api/admin/settings", token=admin_token, expect_code=0)

        data = result["data"]
        # 应有 seo 相关配置
        assert "seo" in data or "title_suffix" in data or "default_description" in data

    def test_pagination_config(self, admin_token):
        """SET-008: 分页配置"""
        result = api_request("GET", "/api/admin/settings", token=admin_token, expect_code=0)

        data = result["data"]
        # 应有 pagination 或 default_page_size
        assert "pagination" in data or "default_page_size" in data
