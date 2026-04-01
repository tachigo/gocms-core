// Package core GoCMS v2.0 框架核心
// 定义 Module 规范接口，所有内置和第三方 Module 必须实现该接口
package core

import (
	"github.com/gogf/gf/v2/os/gcmd"
)

// ---------------------------------------------------------------------------
// 必须实现的核心接口
// ---------------------------------------------------------------------------

// Module 是 GoCMS 的基本构建单元。
// 每个功能模块（文章、用户、权限等）都必须实现此接口。
// 框架通过该接口统一管理模块的注册、初始化、路由挂载和元信息声明。
type Module interface {
	// Name 返回模块唯一标识符，如 "article"、"user"、"permission"
	// 用于依赖声明、事件命名空间、权限前缀等
	Name() string

	// Description 返回模块的人类可读描述，如 "文章管理"、"用户认证与管理"
	Description() string

	// Init 模块初始化入口，框架按依赖顺序调用
	// 职责：数据库迁移（AutoMigrate）、种子数据、注册事件监听
	Init(app *App) error

	// RegisterRoutes 注册模块的 API 路由
	// rg 包含 Public（/api/）和 Admin（/api/admin/）两个路由组
	// 模块自行决定在哪个组下注册路由
	// 推荐使用 GoFrame Bind 模式：rg.Admin.Bind(controller)
	RegisterRoutes(rg *RouterGroup)

	// Schema 返回模块的元信息声明
	// 包含：模块类型、字段定义、权限声明、关联关系
	// 供权限系统、健康检查、后台 UI 自动渲染使用
	Schema() ModuleSchema
}

// ---------------------------------------------------------------------------
// 可选接口（Module 按需实现，框架通过类型断言检测）
// ---------------------------------------------------------------------------

// DependencyAware 声明模块依赖关系（可选）
// 框架在初始化前解析依赖图，按拓扑排序决定 Init 调用顺序
// 未实现此接口的模块视为无依赖
type DependencyAware interface {
	// Dependencies 返回依赖的模块名列表
	// 例如 article 依赖 ["user", "media", "taxonomy"]
	Dependencies() []string
}

// CommandProvider 注册 CLI 子命令（可选）
// 模块可注册自己的命令行工具，如 seed、migrate、export 等
type CommandProvider interface {
	// RegisterCommands 向根命令注册子命令
	RegisterCommands(root *gcmd.Command)
}

// Shutdownable 优雅关闭钩子（可选）
// 框架收到 shutdown 信号时，按初始化的逆序调用
type Shutdownable interface {
	// Shutdown 执行清理逻辑（关闭连接、刷新缓冲区等）
	Shutdown() error
}
