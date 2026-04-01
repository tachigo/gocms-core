"""
SSO Bridge 集成测试
验证 999 号虚拟用户通过 SSO Headers 绕过本地登录
"""
import pytest
import requests

BASE_URL = "http://localhost:8080"


class TestSSOBridge:
    """SSO 桥接功能测试"""
    
    def test_sso_virtual_user_access(self):
        """TC-SSO-001: 999号虚拟用户通过SSO Headers访问管理接口"""
        url = f"{BASE_URL}/api/admin/sso-test"
        
        # 模拟 Nginx 注入的 SSO Headers
        headers = {
            "X-SSO-User-ID": "999",
            "X-SSO-User-Name": "virtual_sso_user",
            "X-SSO-User-Email": "sso@example.com",
            "X-SSO-User-Roles": "sso_manager",  # 应映射为本地 admin
            "X-SSO-Auth-Source": "test-idp"
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        
        # 验证 HTTP 200
        assert response.status_code == 200, f"期望 200, 实际 {response.status_code}: {response.text}"
        
        data = response.json()
        
        # 验证用户识别
        assert data.get("user_id") == 999, f"期望 user_id=999, 实际 {data.get('user_id')}"
        assert data.get("username") == "virtual_sso_user", f"用户名不匹配: {data.get('username')}"
        
        # 验证角色映射: sso_manager -> admin
        roles = data.get("roles", [])
        assert "admin" in roles, f"期望角色包含 admin, 实际: {roles}"
        
        # 验证能获取系统设置
        assert data.get("settings_access") is True, "应能访问系统设置"
        
        print(f"✅ SSO Bridge 测试通过: {data}")
    
    def test_sso_without_headers_should_fail(self):
        """TC-SSO-002: 无SSO Headers时应返回401"""
        url = f"{BASE_URL}/api/admin/sso-test"
        
        response = requests.get(url, timeout=10)
        
        # 应返回 401 未授权
        assert response.status_code == 401, f"期望 401, 实际 {response.status_code}"
        print("✅ 无SSO Headers时正确返回401")
    
    def test_sso_role_mapping(self):
        """TC-SSO-003: 验证SSO角色正确映射到本地角色"""
        url = f"{BASE_URL}/api/admin/sso-test"
        
        headers = {
            "X-SSO-User-ID": "999",
            "X-SSO-User-Name": "virtual_sso_user",
            "X-SSO-User-Email": "sso@example.com",
            "X-SSO-User-Roles": "sso_manager",
            "X-SSO-Auth-Source": "test-idp"
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        assert response.status_code == 200
        
        data = response.json()
        
        # 验证原始SSO角色和映射后的本地角色
        assert data.get("sso_roles") == "sso_manager", f"SSO角色记录错误: {data.get('sso_roles')}"
        assert "admin" in data.get("mapped_roles", []), f"映射角色错误: {data.get('mapped_roles')}"
        
        print(f"✅ 角色映射正确: sso_manager -> admin")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])