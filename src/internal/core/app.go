// Package core App 容器
// 框架核心上下文，注入给每个 Module 的 Init() 方法
// 提供 DB / Cache / Events / Config / Logger 等基础能力
package core

import (
	
	"sync"

	"github.com/gogf/gf/v2/net/ghttp"
	"github.com/gogf/gf/v2/os/glog"
	"gorm.io/gorm"
)

// ---------------------------------------------------------------------------
// AppConfig 应用配置
// ---------------------------------------------------------------------------

// AppConfig 应用级配置（从 config.yaml 加载）
type AppConfig struct {
	// Server HTTP 服务配置
	Server ServerConfig `json:"server"`
	// Database 数据库配置
	Database DatabaseConfig `json:"database"`
	// Cache 缓存配置
	Cache CacheConfig `json:"cache"`
	// JWT 认证配置
	JWT JWTConfig `json:"jwt"`
	// User 用户模块配置
	User UserConfig `json:"user"`
	// Permission 权限模块配置
	Permission PermissionConfig `json:"permission"`
}

// ServerConfig HTTP 服务配置
type ServerConfig struct {
	Address string `json:"address"` // 监听地址，如 ":8080"
}

// DatabaseConfig 数据库配置
type DatabaseConfig struct {
	Driver string `json:"driver"` // sqlite / postgres
	DSN    string `json:"dsn"`    // 数据源，SQLite 为文件路径，PG 为连接串
}

// CacheConfig 缓存配置
type CacheConfig struct {
	Driver string `json:"driver"` // bigcache / redis
	TTL    int    `json:"ttl"`    // 默认过期时间（秒）
}

// JWTConfig JWT 认证配置
type JWTConfig struct {
	Secret string `json:"secret"` // 签名密钥
	Expire int    `json:"expire"` // Token 过期时间（小时）
	Issuer string `json:"issuer"` // 签发者
}

// UserConfig 用户模块配置
type UserConfig struct {
	// Mode 运行模式: master | slave
	// - master: 独立运行，拥有完整的用户管理功能
	// - slave:  作为SSO客户端运行，依赖上游SSO系统鉴权
	Mode string `json:"mode"`
}

// PermissionConfig 权限模块配置
type PermissionConfig struct {
	// RoleMapping SSO 角色到本地角色的映射表
	// key: SSO 角色名 (如 "sso_manager")
	// value: 本地角色名 (如 "admin")
	RoleMapping map[string]string `json:"role_mapping"`
}

// ---------------------------------------------------------------------------
// App 核心容器
// ---------------------------------------------------------------------------

// App 是 GoCMS 的核心容器，贯穿整个生命周期
// 每个 Module 在 Init(app) 时接收此实例，通过它访问所有框架能力
type App struct {
	// DB GORM 数据库连接
	DB *gorm.DB

	// Cache 缓存引擎
	Cache CacheEngine

	// Events 事件总线
	Events EventBus

	// Config 应用配置
	Config *AppConfig

	// Logger 日志实例
	Logger *glog.Logger

	// services 模块导出的服务注册表（模块间通过 GetService 访问）
	services map[string]interface{}
	mu       sync.RWMutex

	// authMiddlewares 认证中间件列表（由 user 模块注册）
	authMiddlewares []ghttp.HandlerFunc

	// adminMiddlewares 管理员鉴权中间件列表（由 permission 模块注册）
	adminMiddlewares []ghttp.HandlerFunc
}

// NewApp 创建 App 实例
func NewApp(db *gorm.DB, cache CacheEngine, events EventBus, cfg *AppConfig, logger *glog.Logger) *App {
	return &App{
		Config:   cfg,
		DB:       db,
		Cache:    cache,
		Events:   events,
		Logger:   logger,
		services: make(map[string]interface{}),
	}
}

// RegisterService 注册服务（供 Module 导出能力给其他 Module）
func (a *App) RegisterService(name string, svc interface{}) {
	a.mu.Lock()
	defer a.mu.Unlock()
	a.services[name] = svc
}

// GetService 获取服务（供 Module 消费其他 Module 的能力）
func (a *App) GetService(name string) (interface{}, bool) {
	a.mu.RLock()
	defer a.mu.RUnlock()
	svc, ok := a.services[name]
	return svc, ok
}

// ---------------------------------------------------------------------------
// 中间件管理
// ---------------------------------------------------------------------------

// AddAuthMiddleware 添加认证中间件（由 user 模块调用）
func (a *App) AddAuthMiddleware(mw ghttp.HandlerFunc) {
	a.authMiddlewares = append(a.authMiddlewares, mw)
}

// AddAdminMiddleware 添加管理员鉴权中间件（由 permission 模块调用）
func (a *App) AddAdminMiddleware(mw ghttp.HandlerFunc) {
	a.adminMiddlewares = append(a.adminMiddlewares, mw)
}

// GetAuthMiddlewares 获取所有认证中间件
func (a *App) GetAuthMiddlewares() []ghttp.HandlerFunc {
	return a.authMiddlewares
}

// GetAdminMiddlewares 获取所有管理员鉴权中间件
func (a *App) GetAdminMiddlewares() []ghttp.HandlerFunc {
	return a.adminMiddlewares
}

// SetupServer 配置 HTTP 服务器（应用所有中间件）
func (a *App) SetupServer(server *ghttp.Server) error {
	// 创建三层路由组
	// 1. Public: 无需认证
	// 2. Authenticated: 需要登录（JWT 认证）
	// 3. Admin: 需要管理员权限（JWT + RBAC）

	// 全局中间件：CORS、日志、恢复
	server.Use(ghttp.MiddlewareHandlerResponse)

	// 公开路由组
	publicGroup := server.Group("/")
	publicGroup.Middleware(func(r *ghttp.Request) {
		// 公开路由无需认证
		r.Middleware.Next()
	})

	// 认证路由组（需要 JWT）
	authGroup := server.Group("/api")
	for _, mw := range a.authMiddlewares {
		authGroup.Middleware(mw)
	}

	// 管理员路由组（需要 JWT + RBAC）
	adminGroup := server.Group("/api/admin")
	for _, mw := range a.authMiddlewares {
		adminGroup.Middleware(mw)
	}
	for _, mw := range a.adminMiddlewares {
		adminGroup.Middleware(mw)
	}

	// 存储路由组供后续使用
	// 这里我们使用 request context 来标记路由组
	// 实际应用中可能需要更复杂的路由注册机制

	return nil
}

// AuthMiddlewares 获取所有认证中间件（供 router.go 使用）
func (a *App) AuthMiddlewares() []ghttp.HandlerFunc {
	return a.authMiddlewares
}

// AdminMiddlewares 获取所有管理员鉴权中间件（供 router.go 使用）
func (a *App) AdminMiddlewares() []ghttp.HandlerFunc {
	return a.adminMiddlewares
}
