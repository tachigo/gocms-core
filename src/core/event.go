// Package core Event 总线实现
// 支持同步（Emit）和异步（EmitAsync）两种发布模式
// 模块间通过事件解耦通信，命名规范：{module}.{action}
package core

import (
	"strings"
	"sync"

	"github.com/gogf/gf/v2/os/glog"
)

// ---------------------------------------------------------------------------
// EventBus 接口
// ---------------------------------------------------------------------------

// EventHandler 事件处理函数
type EventHandler func(payload interface{})

// EventBus 事件总线接口
type EventBus interface {
	// Emit 同步发布事件，按注册顺序执行所有监听器
	// 每个 handler 用 recover 保护，单个 panic 不影响其他 handler
	Emit(event string, payload interface{})

	// EmitAsync 异步发布事件，在独立 goroutine 中执行
	EmitAsync(event string, payload interface{})

	// On 注册事件监听器
	// 支持精确匹配（如 "article.created"）和通配符（如 "article.*" 或 "*.*"）
	On(event string, handler EventHandler)

	// Off 移除指定事件的所有监听器
	Off(event string)
}

// ---------------------------------------------------------------------------
// 默认实现
// ---------------------------------------------------------------------------

// eventBus Event 总线默认实现（内存级，进程内通信）
type eventBus struct {
	mu       sync.RWMutex
	handlers map[string][]EventHandler // event name → handler list
	logger   *glog.Logger
}

// NewEventBus 创建事件总线实例
func NewEventBus(logger *glog.Logger) EventBus {
	return &eventBus{
		handlers: make(map[string][]EventHandler),
		logger:   logger,
	}
}

// Emit 同步发布事件
// 遍历所有匹配的 handler，每个都用 recover 保护
// 单个 handler panic 只写日志，不影响后续 handler 和发布者
func (eb *eventBus) Emit(event string, payload interface{}) {
	handlers := eb.matchHandlers(event)
	if len(handlers) == 0 {
		return
	}

	for _, h := range handlers {
		eb.safeCall(event, h, payload)
	}
}

// EmitAsync 异步发布事件
// 在独立 goroutine 中执行所有匹配的 handler
func (eb *eventBus) EmitAsync(event string, payload interface{}) {
	handlers := eb.matchHandlers(event)
	if len(handlers) == 0 {
		return
	}

	go func() {
		for _, h := range handlers {
			eb.safeCall(event, h, payload)
		}
	}()
}

// On 注册事件监听器
// 支持通配符模式：
//   - "article.created" — 精确匹配
//   - "article.*"       — 匹配 article 模块的所有事件
//   - "*.*"             — 匹配所有事件
func (eb *eventBus) On(event string, handler EventHandler) {
	eb.mu.Lock()
	defer eb.mu.Unlock()
	eb.handlers[event] = append(eb.handlers[event], handler)
}

// Off 移除指定事件的所有监听器
func (eb *eventBus) Off(event string) {
	eb.mu.Lock()
	defer eb.mu.Unlock()
	delete(eb.handlers, event)
}

// matchHandlers 查找所有匹配事件的 handler
// 匹配规则：精确匹配 → module.* 通配 → *.* 全局通配
func (eb *eventBus) matchHandlers(event string) []EventHandler {
	eb.mu.RLock()
	defer eb.mu.RUnlock()

	var matched []EventHandler

	// 1. 精确匹配
	if hs, ok := eb.handlers[event]; ok {
		matched = append(matched, hs...)
	}

	// 2. 模块级通配（article.* 匹配 article.created）
	parts := strings.SplitN(event, ".", 2)
	if len(parts) == 2 {
		wildcard := parts[0] + ".*"
		if hs, ok := eb.handlers[wildcard]; ok {
			matched = append(matched, hs...)
		}
	}

	// 3. 全局通配（*.* 匹配所有事件）
	if hs, ok := eb.handlers["*.*"]; ok {
		matched = append(matched, hs...)
	}

	return matched
}

// safeCall 安全调用 handler，用 recover 捕获 panic
func (eb *eventBus) safeCall(event string, handler EventHandler, payload interface{}) {
	defer func() {
		if r := recover(); r != nil {
			if eb.logger != nil {
				eb.logger.Errorf(nil, "[EventBus] handler panic on event '%s': %v", event, r)
			}
		}
	}()
	handler(payload)
}
