// Package cmd GoCMS CLI 命令入口
// 定义根命令和 server 子命令，管理应用完整生命周期
package cmd

import (
	"context"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/gogf/gf/v2/frame/g"
	"github.com/gogf/gf/v2/os/gcmd"
	"gorm.io/gorm"
	"gorm.io/gorm/logger"

	"github.com/glebarez/sqlite"

	"gocms/internal/core"
)

// Main 根命令，程序入口
var Main = &gcmd.Command{
	Name:        "gocms",
	Brief:       "GoCMS v2.0 — Module-based Headless CMS Framework",
	Description: "一切皆 Module 的 Headless CMS 框架，纯 API 输出 + OpenAPI 自动生成",
}

// init 注册子命令（避免 struct literal 循环引用）
func init() {
	if err := Main.AddCommand(&serverCmd, &versionCmd); err != nil {
		panic(err)
	}
}

// serverCmd 启动 HTTP 服务
var serverCmd = gcmd.Command{
	Name:  "server",
	Brief: "Start the HTTP server",
	Func:  runServer,
}

// versionCmd 输出版本号
var versionCmd = gcmd.Command{
	Name:  "version",
	Brief: "Print version information",
	Func: func(ctx context.Context, parser *gcmd.Parser) error {
		g.Log().Info(ctx, "GoCMS v2.0.0")
		return nil
	},
}

// runServer 启动 HTTP 服务的完整流程
// 步骤：配置 → DB → Cache → EventBus → App → Registry → InitAll → Routes → Server
func runServer(ctx context.Context, parser *gcmd.Parser) error {
	log := g.Log()
	log.Info(ctx, "========================================")
	log.Info(ctx, "  GoCMS v2.0 starting...")
	log.Info(ctx, "========================================")

	// ------------------------------------------------------------------
	// 1. 加载配置
	// ------------------------------------------------------------------
	appConfig, err := loadConfig(ctx)
	if err != nil {
		return err
	}
	log.Infof(ctx, "[Boot] config loaded: address=%s, db=%s", appConfig.Server.Address, appConfig.Database.Driver)

	// ------------------------------------------------------------------
	// 2. 初始化数据库（GORM）
	// ------------------------------------------------------------------
	db, err := initDatabase(appConfig)
	if err != nil {
		return err
	}
	log.Info(ctx, "[Boot] database connected ✓")

	// ------------------------------------------------------------------
	// 3. 初始化缓存引擎
	// ------------------------------------------------------------------
	cacheTTL := time.Duration(appConfig.Cache.TTL) * time.Second
	if cacheTTL == 0 {
		cacheTTL = 10 * time.Minute // 默认 10 分钟
	}
	cache, err := core.NewBigCacheEngine(cacheTTL)
	if err != nil {
		return err
	}
	log.Info(ctx, "[Boot] cache engine initialized ✓")

	// ------------------------------------------------------------------
	// 4. 创建 Event 总线
	// ------------------------------------------------------------------
	events := core.NewEventBus(log)
	log.Info(ctx, "[Boot] event bus created ✓")

	// ------------------------------------------------------------------
	// 5. 创建 App 容器
	// ------------------------------------------------------------------
	app := core.NewApp(db, cache, events, appConfig, log)

	// ------------------------------------------------------------------
	// 6. 创建 Registry 并注册内置 Module
	// ------------------------------------------------------------------
	registry := core.NewRegistry(log)
	registerBuiltinModules(registry)

	// ------------------------------------------------------------------
	// 7. 按依赖拓扑排序，逐个初始化所有 Module
	// ------------------------------------------------------------------
	if err := registry.InitAll(app); err != nil {
		log.Errorf(ctx, "[Boot] module initialization failed: %v", err)
		return err
	}

	// ------------------------------------------------------------------
	// 8. 注册 Module CLI 命令（M2+ 启用，当前无 CommandProvider Module）
	// ------------------------------------------------------------------
	// TODO: M2 实现后启用，需通过参数传入 root command 避免循环引用
	// registry.RegisterAllCommands(rootCmd)

	// ------------------------------------------------------------------
	// 9. 创建 HTTP Server 并注册路由
	// ------------------------------------------------------------------
	server := core.SetupServer(registry, app)

	// ------------------------------------------------------------------
	// 10. 优雅关闭
	// ------------------------------------------------------------------
	go func() {
		quit := make(chan os.Signal, 1)
		signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
		sig := <-quit
		log.Infof(ctx, "[Boot] received signal: %v, shutting down...", sig)
		registry.ShutdownAll()
		log.Info(ctx, "[Boot] all modules shut down, bye!")
	}()

	// ------------------------------------------------------------------
	// 11. 启动 HTTP Server（阻塞）
	// ------------------------------------------------------------------
	log.Infof(ctx, "[Boot] HTTP server starting on %s", appConfig.Server.Address)
	log.Infof(ctx, "[Boot] Swagger UI: http://localhost%s/swagger", appConfig.Server.Address)
	log.Infof(ctx, "[Boot] OpenAPI:    http://localhost%s/api.json", appConfig.Server.Address)
	server.Run()
	return nil
}

// ---------------------------------------------------------------------------
// 配置加载
// ---------------------------------------------------------------------------

// loadConfig 从 GoFrame 配置系统加载应用配置
func loadConfig(ctx context.Context) (*core.AppConfig, error) {
	cfg := g.Cfg()
	config := &core.AppConfig{}

	// Server
	config.Server.Address = cfg.MustGet(ctx, "server.address", ":8080").String()

	// Database
	config.Database.Driver = cfg.MustGet(ctx, "database.driver", "sqlite").String()
	config.Database.DSN = cfg.MustGet(ctx, "database.dsn", "data/gocms.db").String()

	// Cache
	config.Cache.Driver = cfg.MustGet(ctx, "cache.driver", "bigcache").String()
	config.Cache.TTL = cfg.MustGet(ctx, "cache.ttl", 600).Int()

	// JWT
	config.JWT.Secret = cfg.MustGet(ctx, "jwt.secret", "gocms-dev-secret-change-in-production").String()
	config.JWT.Expire = cfg.MustGet(ctx, "jwt.expire", 24).Int()
	config.JWT.Issuer = cfg.MustGet(ctx, "jwt.issuer", "gocms").String()

	return config, nil
}

// ---------------------------------------------------------------------------
// 数据库初始化
// ---------------------------------------------------------------------------

// initDatabase 根据配置初始化 GORM 数据库连接
// 支持 sqlite（默认）和 postgres
func initDatabase(config *core.AppConfig) (*gorm.DB, error) {
	var dialector gorm.Dialector

	switch config.Database.Driver {
	case "sqlite":
		// 确保数据目录存在
		os.MkdirAll("data", 0755)
		dialector = sqlite.Open(config.Database.DSN)
	default:
		// PostgreSQL 等其他驱动在 M2+ 按需添加
		dialector = sqlite.Open(config.Database.DSN)
	}

	db, err := gorm.Open(dialector, &gorm.Config{
		Logger: logger.Default.LogMode(logger.Info),
	})
	if err != nil {
		return nil, err
	}

	// SQLite 性能优化：开启 WAL 模式 + 外键约束
	if config.Database.Driver == "sqlite" {
		sqlDB, _ := db.DB()
		sqlDB.Exec("PRAGMA journal_mode=WAL")
		sqlDB.Exec("PRAGMA foreign_keys=ON")
	}

	return db, nil
}

// ---------------------------------------------------------------------------
// 内置 Module 注册
// ---------------------------------------------------------------------------

// registerBuiltinModules 注册所有内置 Module
// 注册顺序不影响初始化顺序（由依赖拓扑排序决定）
func registerBuiltinModules(registry *core.Registry) {
	// 内置 Module 已自动通过 init() 注册到全局注册表
	// 无需手动注册，模块自注册机制会自动完成
}
