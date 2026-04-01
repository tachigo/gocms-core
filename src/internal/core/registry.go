// Package core Module 注册中心 & 依赖拓扑排序
// 管理所有 Module 的注册、依赖解析、按序初始化和优雅关闭
package core

import (
	"fmt"
	"strings"

	"github.com/gogf/gf/v2/os/gcmd"
	"github.com/gogf/gf/v2/os/glog"
)

// ---------------------------------------------------------------------------
// 全局注册表（供模块 init() 自注册使用）
// ---------------------------------------------------------------------------

var globalRegistry *Registry

// Register 全局注册函数，供模块在 init() 中调用
func Register(m Module) {
	if globalRegistry == nil {
		globalRegistry = NewRegistry(glog.New())
	}
	globalRegistry.Register(m)
}

// GetGlobalRegistry 获取全局注册表
func GetGlobalRegistry() *Registry {
	if globalRegistry == nil {
		globalRegistry = NewRegistry(glog.New())
	}
	return globalRegistry
}

// ---------------------------------------------------------------------------
// Registry 模块注册中心
// ---------------------------------------------------------------------------

// Registry 管理所有 Module 的生命周期
type Registry struct {
	modules  map[string]Module // name → module（注册表）
	ordered  []Module          // 按依赖拓扑排序后的初始化顺序
	logger   *glog.Logger
}

// NewRegistry 创建注册中心
func NewRegistry(logger *glog.Logger) *Registry {
	return &Registry{
		modules: make(map[string]Module),
		logger:  logger,
	}
}

// Register 注册一个 Module
// 重复注册同名 Module 会 panic（启动阶段及早暴露问题）
func (r *Registry) Register(m Module) {
	name := m.Name()
	if _, exists := r.modules[name]; exists {
		panic(fmt.Sprintf("[Registry] duplicate module: '%s'", name))
	}
	r.modules[name] = m
	r.logger.Infof(nil, "[Registry] registered module: %s (%s)", name, m.Description())
}

// InitAll 按依赖拓扑排序后逐个初始化所有 Module
// 步骤：
//  1. 解析依赖图 → 拓扑排序
//  2. 按排序结果逐个调用 Module.Init(app)
//  3. 任何 Module 初始化失败则终止启动
func (r *Registry) InitAll(app *App) error {
	// 1. 拓扑排序
	sorted, err := r.topologicalSort()
	if err != nil {
		return fmt.Errorf("[Registry] dependency resolution failed: %w", err)
	}
	r.ordered = sorted

	// 2. 按序初始化
	for _, m := range r.ordered {
		r.logger.Infof(nil, "[Registry] initializing module: %s", m.Name())
		if err := m.Init(app); err != nil {
			return fmt.Errorf("[Registry] module '%s' init failed: %w", m.Name(), err)
		}
		r.logger.Infof(nil, "[Registry] module '%s' initialized ✓", m.Name())
	}

	r.logger.Infof(nil, "[Registry] all %d modules initialized", len(r.ordered))
	return nil
}

// RegisterAllRoutes 为所有 Module 注册 API 路由
// 每个 Module 通过 RouterGroup 访问 Public 和 Admin 两个路由组
func (r *Registry) RegisterAllRoutes(rg *RouterGroup) {
	for _, m := range r.ordered {
		r.logger.Infof(nil, "[Registry] registering routes for module: %s", m.Name())
		m.RegisterRoutes(rg)
	}
}

// RegisterAllCommands 为所有实现了 CommandProvider 的 Module 注册 CLI 命令
func (r *Registry) RegisterAllCommands(root *gcmd.Command) {
	for _, m := range r.ordered {
		if cp, ok := m.(CommandProvider); ok {
			r.logger.Infof(nil, "[Registry] registering commands for module: %s", m.Name())
			cp.RegisterCommands(root)
		}
	}
}

// ShutdownAll 按初始化的逆序优雅关闭所有 Module
func (r *Registry) ShutdownAll() {
	for i := len(r.ordered) - 1; i >= 0; i-- {
		m := r.ordered[i]
		if s, ok := m.(Shutdownable); ok {
			r.logger.Infof(nil, "[Registry] shutting down module: %s", m.Name())
			if err := s.Shutdown(); err != nil {
				r.logger.Errorf(nil, "[Registry] module '%s' shutdown error: %v", m.Name(), err)
			}
		}
	}
}

// GetModule 按名称获取已注册的 Module
func (r *Registry) GetModule(name string) (Module, bool) {
	m, ok := r.modules[name]
	return m, ok
}

// Modules 返回所有已注册 Module（按初始化顺序）
func (r *Registry) Modules() []Module {
	return r.ordered
}

// AllSchemas 收集所有 Module 的 Schema 声明
// 供权限模块构建完整权限矩阵使用
func (r *Registry) AllSchemas() map[string]ModuleSchema {
	schemas := make(map[string]ModuleSchema, len(r.modules))
	for name, m := range r.modules {
		schemas[name] = m.Schema()
	}
	return schemas
}

// ---------------------------------------------------------------------------
// 拓扑排序（Kahn's Algorithm / BFS）
// ---------------------------------------------------------------------------

// topologicalSort 对所有 Module 按依赖关系进行拓扑排序
// 返回初始化顺序（依赖在前，被依赖在后）
// 检测：循环依赖 → 报错、缺失依赖 → 报错
func (r *Registry) topologicalSort() ([]Module, error) {
	// 构建入度表和邻接表
	inDegree := make(map[string]int)
	adjacency := make(map[string][]string) // dependency → dependents

	for name := range r.modules {
		inDegree[name] = 0
	}

	// 解析每个 Module 的依赖
	for name, m := range r.modules {
		deps := r.getDependencies(m)
		for _, dep := range deps {
			// 检查依赖是否已注册
			if _, exists := r.modules[dep]; !exists {
				return nil, fmt.Errorf("module '%s' depends on '%s' which is not registered", name, dep)
			}
			inDegree[name]++
			adjacency[dep] = append(adjacency[dep], name)
		}
	}

	// BFS：从入度为 0 的节点开始
	var queue []string
	for name, degree := range inDegree {
		if degree == 0 {
			queue = append(queue, name)
		}
	}

	var sorted []Module
	for len(queue) > 0 {
		// 取队首
		name := queue[0]
		queue = queue[1:]
		sorted = append(sorted, r.modules[name])

		// 更新邻接节点入度
		for _, dependent := range adjacency[name] {
			inDegree[dependent]--
			if inDegree[dependent] == 0 {
				queue = append(queue, dependent)
			}
		}
	}

	// 检测循环依赖：如果排序结果不包含所有模块，说明存在环
	if len(sorted) != len(r.modules) {
		var cycleModules []string
		for name, degree := range inDegree {
			if degree > 0 {
				cycleModules = append(cycleModules, name)
			}
		}
		return nil, fmt.Errorf("circular dependency detected among modules: [%s]",
			strings.Join(cycleModules, ", "))
	}

	return sorted, nil
}

// getDependencies 获取 Module 的依赖列表
// 如果 Module 实现了 DependencyAware 接口则返回声明的依赖，否则返回空
func (r *Registry) getDependencies(m Module) []string {
	if da, ok := m.(DependencyAware); ok {
		return da.Dependencies()
	}
	return nil
}
