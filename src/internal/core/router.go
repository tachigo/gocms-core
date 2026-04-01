// Package core 路由统一挂载 & 基础中间件
// 创建 HTTP Server，配置公开/管理两个路由组
// OpenAPI / Swagger 自动生成由 GoFrame 内置支持
package core

import (
	"net/http"
	"time"

	"github.com/gogf/gf/v2/frame/g"
	"github.com/gogf/gf/v2/net/ghttp"
)

// ---------------------------------------------------------------------------
// RouterGroup — 双路由组容器
// ---------------------------------------------------------------------------

// RouterGroup 包含三层路由组，传给每个 Module 的 RegisterRoutes
// Module 自行决定在哪个组下注册路由：
//   - Public:        /api/ 前缀，无需认证（如 login、公开内容查询）
//   - Authenticated: /api/ 前缀，需 JWT 认证但不需 RBAC（如 profile、logout）
//   - Admin:         /api/admin/ 前缀，需 JWT + RBAC（管理后台 API）
type RouterGroup struct {
	Public        *ghttp.RouterGroup
	Authenticated *ghttp.RouterGroup
	Admin         *ghttp.RouterGroup
}

// ---------------------------------------------------------------------------
// Server 配置与启动
// ---------------------------------------------------------------------------

// SetupServer 创建并配置 HTTP Server
// 职责：
//  1. 设置服务地址和 OpenAPI 端点
//  2. 配置全局中间件管道（CORS → Recovery → Logger → 统一响应）
//  3. 注册健康检查端点
//  4. 创建公开/管理两个路由组
//  5. 调用 Registry 为所有 Module 注册路由
func SetupServer(registry *Registry, app *App) *ghttp.Server {
	s := g.Server()

	// --- 服务基础配置 ---
	s.SetAddr(app.Config.Server.Address)

	// --- OpenAPI / Swagger ---
	s.SetOpenApiPath("/api.json")
	s.SetSwaggerPath("/swagger")

	// --- 全局中间件管道 ---
	// 执行顺序：CORS → Recovery → RequestLog → HandlerResponse
	s.Use(
		MiddlewareCORS,
		MiddlewareRecovery,
		MiddlewareRequestLog,
		ghttp.MiddlewareHandlerResponse, // GoFrame 统一响应格式（Bind 模式自动包装）
	)

	// --- 健康检查 ---
	s.BindHandler("GET:/health", func(r *ghttp.Request) {
		modules := make([]string, 0, len(registry.Modules()))
		for _, m := range registry.Modules() {
			modules = append(modules, m.Name())
		}
		r.Response.WriteJson(g.Map{
			"status":  "ok",
			"version": "2.0.0",
			"modules": modules,
		})
	})

	// --- API 路由组 ---
	// 公开 API：/api/ 前缀，无需认证
	publicGroup := s.Group("/api")

	// 需认证 API：/api/ 前缀，JWT 认证但不需要 RBAC（如 profile、logout）
	authenticatedGroup := s.Group("/api")
	for _, mw := range app.AuthMiddlewares() {
		authenticatedGroup.Middleware(mw)
	}

	// 管理 API：/api/admin/ 前缀，JWT + RBAC
	adminGroup := s.Group("/api/admin")
	// 先加 JWT 认证中间件
	for _, mw := range app.AuthMiddlewares() {
		adminGroup.Middleware(mw)
	}
	// 再加 RBAC 权限中间件
	for _, mw := range app.AdminMiddlewares() {
		adminGroup.Middleware(mw)
	}

	// --- 为所有 Module 注册路由 ---
	rg := &RouterGroup{
		Public:        publicGroup,
		Authenticated: authenticatedGroup,
		Admin:         adminGroup,
	}
	registry.RegisterAllRoutes(rg)

	// --- API 404 兜底（返回 JSON 而非 HTML） ---
	s.BindHandler("ALL:/api/*", func(r *ghttp.Request) {
		r.Response.Status = http.StatusNotFound
		r.Response.WriteJsonExit(g.Map{
			"code":    404,
			"message": "接口不存在",
		})
	})

	return s
}

// ---------------------------------------------------------------------------
// 基础中间件
// ---------------------------------------------------------------------------

// MiddlewareCORS 跨域资源共享中间件
// 允许所有来源访问（开发阶段），生产环境建议通过配置限制
func MiddlewareCORS(r *ghttp.Request) {
	r.Response.CORSDefault()
	r.Middleware.Next()
}

// MiddlewareRecovery panic 恢复中间件
// 捕获 handler 中的 panic，返回 500 JSON 响应，避免服务崩溃
func MiddlewareRecovery(r *ghttp.Request) {
	defer func() {
		if err := recover(); err != nil {
			g.Log().Errorf(r.Context(), "[Recovery] panic: %+v", err)
			r.Response.Status = http.StatusInternalServerError
			r.Response.WriteJsonExit(g.Map{
				"code":    500,
				"message": "Internal Server Error",
			})
		}
	}()
	r.Middleware.Next()
}

// MiddlewareRequestLog 请求日志中间件
// 记录每个请求的方法、路径、状态码和耗时
func MiddlewareRequestLog(r *ghttp.Request) {
	start := time.Now()
	r.Middleware.Next()

	// 请求完成后记录日志
	elapsed := time.Since(start).Milliseconds()
	g.Log().Infof(r.Context(), "[HTTP] %s %s → %d (%dms)",
		r.Method,
		r.URL.Path,
		r.Response.Status,
		elapsed,
	)
}
