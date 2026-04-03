// Package core 上下文工具函数
// 提供从 context 中提取用户等通用功能，支持 SSO Slave 模式
package core

import (
	"context"
)

// contextKey 定义上下文键类型，避免键冲突
type contextKey string

const (
	// ctxUserKey 用户对象在 context 中的键
	ctxUserKey contextKey = "gocms:user"
	// ctxUserIDKey 用户ID在 context 中的键
	ctxUserIDKey contextKey = "gocms:user_id"
	// ctxUsernameKey 用户名在 context 中的键
	ctxUsernameKey contextKey = "gocms:username"
)

// UserInfo 用户信息结构体（用于SSO上下文传递）
type UserInfo struct {
	ID       int64    `json:"id"`
	Username string   `json:"username"`
	Email    string   `json:"email,omitempty"`
	Roles    []string `json:"roles,omitempty"` // 多角色支持
	// SSO模式下的原始令牌信息
	SSOToken string `json:"-"`
}

// ---------------------------------------------------------------------------
// 用户上下文操作
// ---------------------------------------------------------------------------

// SetUserToCtx 将用户信息注入 context
// 由 SSO 中间件或认证中间件在请求开始时调用
func SetUserToCtx(ctx context.Context, user *UserInfo) context.Context {
	if user == nil {
		return ctx
	}
	ctx = context.WithValue(ctx, ctxUserKey, user)
	ctx = context.WithValue(ctx, ctxUserIDKey, user.ID)
	ctx = context.WithValue(ctx, ctxUsernameKey, user.Username)
	return ctx
}

// GetUserFromCtx 从 context 中提取用户信息
// Slave 模式下使用此函数替代数据库查询
func GetUserFromCtx(ctx context.Context) *UserInfo {
	if ctx == nil {
		return nil
	}
	if user, ok := ctx.Value(ctxUserKey).(*UserInfo); ok {
		return user
	}
	return nil
}

// GetUserIDFromCtx 从 context 中提取用户ID
func GetUserIDFromCtx(ctx context.Context) int64 {
	if ctx == nil {
		return 0
	}
	if id, ok := ctx.Value(ctxUserIDKey).(int64); ok {
		return id
	}
	return 0
}

// GetUsernameFromCtx 从 context 中提取用户名
func GetUsernameFromCtx(ctx context.Context) string {
	if ctx == nil {
		return ""
	}
	if username, ok := ctx.Value(ctxUsernameKey).(string); ok {
		return username
	}
	return ""
}