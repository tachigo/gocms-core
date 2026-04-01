// Package core 缓存引擎接口与实现
// 默认提供 bigcache 本地缓存，接口预留 Redis 等外部缓存扩展
package core

import (
	"context"
	"time"

	"github.com/allegro/bigcache/v3"
)

// ---------------------------------------------------------------------------
// CacheEngine 接口
// ---------------------------------------------------------------------------

// CacheEngine 缓存引擎统一接口
// Module 通过 App.Cache 访问，无需关心底层实现
type CacheEngine interface {
	// Get 获取缓存值，key 不存在时返回 ErrCacheMiss
	Get(key string) ([]byte, error)

	// Set 设置缓存值（ttl=0 表示使用默认过期时间）
	Set(key string, value []byte, ttl time.Duration) error

	// Delete 删除缓存
	Delete(key string) error

	// Clear 清空所有缓存
	Clear() error
}

// ErrCacheMiss 缓存未命中错误（调用方通过 errors.Is 判断）
var ErrCacheMiss = bigcache.ErrEntryNotFound

// ---------------------------------------------------------------------------
// BigCache 实现
// ---------------------------------------------------------------------------

// bigCacheEngine 基于 allegro/bigcache 的本地缓存实现
// 特点：零 GC 压力、并发安全、纯内存
type bigCacheEngine struct {
	cache *bigcache.BigCache
}

// NewBigCacheEngine 创建 bigcache 缓存引擎
// defaultTTL: 默认过期时间（建议 10~30 分钟）
func NewBigCacheEngine(defaultTTL time.Duration) (CacheEngine, error) {
	cfg := bigcache.DefaultConfig(defaultTTL)
	cfg.CleanWindow = 5 * time.Minute  // 清理间隔
	cfg.MaxEntriesInWindow = 1000 * 10  // 预估 10 分钟内的条目数
	cfg.MaxEntrySize = 500              // 单条最大 500 字节（预估）
	cfg.HardMaxCacheSize = 256          // 最大 256MB

	cache, err := bigcache.New(context.Background(), cfg)
	if err != nil {
		return nil, err
	}

	return &bigCacheEngine{cache: cache}, nil
}

// Get 获取缓存值
func (e *bigCacheEngine) Get(key string) ([]byte, error) {
	return e.cache.Get(key)
}

// Set 设置缓存值
// 注意：bigcache 不支持单条 TTL，所有条目共享全局过期时间
// ttl 参数保留接口兼容性，实际使用全局 TTL
func (e *bigCacheEngine) Set(key string, value []byte, _ time.Duration) error {
	return e.cache.Set(key, value)
}

// Delete 删除缓存
func (e *bigCacheEngine) Delete(key string) error {
	return e.cache.Delete(key)
}

// Clear 清空所有缓存
func (e *bigCacheEngine) Clear() error {
	return e.cache.Reset()
}
