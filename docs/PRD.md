# GoCMS v2.0 功能需求文档（PRD）

> 版本：v2.0-PRD | 日期：2026-03-29 | 作者：阿产（@pm）
>
> 基于老板确认的《v2.0 架构方向》编写

---

## 1. 背景与目标

### 1.1 v1.0 回顾

v1.0 采用 YAML 配置驱动，通过 SchemaEngine 统一解析配置并自动生成数据库/API/界面。核心问题：

| 痛点 | 根因 |
|------|------|
| 动态表 + `map[string]interface{}` 性能差、缺乏类型安全 | YAML 驱动的泛型方案天花板 |
| SchemaEngine 是上帝对象，所有逻辑耦合 | 单一引擎承担太多职责 |
| 菜单、权限等模块硬编码特殊逻辑 | 没有统一的模块抽象 |
| API 文档手写，文档与代码频繁脱节 | 缺乏自动化生成机制 |
| 前后端耦合（SSR 模板） | CMS 框架不应绑定展示层 |

### 1.2 v2.0 核心目标

**一句话定位：GoCMS v2.0 是一个 Module 化的 Headless CMS 框架。**

| 目标 | 说明 |
|------|------|
| **一切皆 Module** | 文章/页面/菜单/用户/权限全部是 Module，框架只做容器和协调 |
| **类型安全** | Go struct 定义模型，编译期检查，IDE 友好 |
| **Headless** | 纯 API 输出，不绑定前端，OpenAPI/Swagger 自动生成 |
| **解耦** | Module 间通过 Event 总线通信，不直接依赖 |
| **可扩展** | 第三方可按规范接口开发新 Module |

### 1.3 范围声明

**v2.0 包含：**
- 框架核心（Module 容器 + Event 总线 + API 路由）
- 8 个内置 Module（user / permission / media / settings / article / page / menu / taxonomy）
- OpenAPI 3.0 自动生成 + Swagger UI
- 单二进制部署（保留 v1.0 优势）

**v2.0 不包含：**
- 管理后台前端（Headless 架构，前端独立项目）
- 多租户/多站点（见 [9.1 节](#91-多租户多站点)）
- 第三方 Module 插件市场（见 [9.2 节](#92-第三方-module-接入机制)）
- SSR 模板渲染（v1.0 的模板系统不带入 v2.0）

---

## 2. 架构概览

### 2.1 系统架构

```
┌──────────────────────────────────────────────────────────┐
│                     GoCMS Core（框架层）                   │
│                                                          │
│  ┌────────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │ Module Registry │  │ Event Bus    │  │ Router       │ │
│  │ 注册 / 生命周期  │  │ 发布 / 订阅  │  │ GoFrame Bind │ │
│  │ 依赖解析        │  │ 异步 / 同步  │  │ OpenAPI 生成  │ │
│  └────────┬───────┘  └──────┬───────┘  └──────┬───────┘ │
│           │                 │                  │         │
│  ┌────────┴─────────────────┴──────────────────┴───────┐ │
│  │              Middleware Pipeline                     │ │
│  │  [Logger] [Recovery] [CORS] [JWT] [Permission]      │ │
│  └─────────────────────────┬───────────────────────────┘ │
│                            │                             │
│  ┌─────────────────────────┴───────────────────────────┐ │
│  │                 App Context                         │ │
│  │  DB(GORM) / Cache(bigcache|Redis) / Config / Logger │ │
│  └─────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────┘
           │           │           │           │
    ┌──────┴───┐ ┌─────┴────┐ ┌───┴─────┐ ┌───┴──────┐
    │ user     │ │ article  │ │ media   │ │ taxonomy │  ...
    │ module   │ │ module   │ │ module  │ │ module   │
    └──────────┘ └──────────┘ └─────────┘ └──────────┘
```

### 2.2 请求生命周期

```
HTTP Request
  → GoFrame Router（自动匹配 Bind struct 定义的路径）
  → Middleware Pipeline
    → Logger → Recovery → CORS
    → JWT Auth（提取用户身份）
    → Permission（根据 Module Schema 声明的权限校验）
  → Module Controller（请求参数自动绑定到 Request struct）
  → Module Logic / Service
  → Response（自动序列化 Response struct → JSON）
  → OpenAPI 文档自动同步
```

---

## 3. Module 规范接口

### 3.1 接口总览

| 接口 | 必须/可选 | 说明 |
|------|----------|------|
| `Name()` | ✅ 必须 | Module 唯一标识符 |
| `Description()` | ✅ 必须 | Module 描述 |
| `Init(app *App)` | ✅ 必须 | 初始化（建表、种子数据、注册事件监听） |
| `RegisterRoutes(group)` | ✅ 必须 | 注册 API 路由 |
| `Schema()` | ✅ 必须 | 声明字段、关系、权限需求 |
| `Dependencies()` | 可选 | 依赖的其他 Module（默认无依赖） |
| `RegisterCommands()` | 可选 | 注册 CLI 子命令 |
| `Shutdown()` | 可选 | 优雅关闭时的清理逻辑 |

### 3.2 完整接口定义

```go
// Module 必须实现的核心接口
type Module interface {
    // === 身份 ===
    Name() string           // 唯一标识，如 "article"、"user"
    Description() string    // 人类可读描述，如 "文章管理"

    // === 生命周期 ===
    Init(app *App) error    // 初始化：自动迁移、种子数据、事件监听注册

    // === 路由 ===
    RegisterRoutes(group *RouterGroup)  // 注册 API 路由（GoFrame Bind 模式）

    // === Schema 声明 ===
    Schema() ModuleSchema   // 声明模块的元信息
}

// DependencyAware 可选：声明依赖
type DependencyAware interface {
    Dependencies() []string
}

// CommandProvider 可选：注册 CLI 命令
type CommandProvider interface {
    RegisterCommands(root *CommandGroup)
}

// Shutdownable 可选：优雅关闭
type Shutdownable interface {
    Shutdown() error
}
```

### 3.3 ModuleSchema 定义

每个 Module 通过 `Schema()` 向框架声明自己的元信息，供权限系统、健康检查、后台 UI 使用：

```go
type ModuleSchema struct {
    // 类型标记
    Kind        ModuleKind    // "content" | "infrastructure"

    // 字段声明（用于后台 UI 自动渲染，可选）
    Fields      []FieldDef
    Groups      []FieldGroup

    // 权限声明
    Permissions []PermissionDef

    // 关联声明
    Relations   []RelationDef
}

// ModuleKind Module 类型
type ModuleKind string
const (
    KindContent        ModuleKind = "content"        // 内容型（article, page, menu, taxonomy）
    KindInfrastructure ModuleKind = "infrastructure"  // 基础设施（user, permission, media, settings）
)

// FieldDef 字段声明（供后台 UI 使用）
type FieldDef struct {
    ID          string         // 字段标识
    Type        FieldType      // text / richtext / number / image / select / ...
    Label       string         // 显示标签
    Required    bool
    Default     interface{}
    Validations map[string]interface{}
    Options     map[string]interface{}
}

// FieldGroup 字段分组
type FieldGroup struct {
    ID     string
    Label  string
    Fields []string
}

// PermissionDef 权限声明
type PermissionDef struct {
    Action      string   // "create" / "read" / "update" / "delete" / "manage"
    Description string   // "创建文章" / "管理用户"
    Scopes      []string // "own" / "all" — 数据范围
}

// RelationDef 关联声明
type RelationDef struct {
    Field      string // 本模块的字段
    Target     string // 目标模块名
    Type       string // "belongs_to" / "has_many" / "many_to_many"
    OnDelete   string // "set_null" / "restrict" / "cascade"
}
```

### 3.4 App Context（框架注入给 Module 的能力）

```go
type App struct {
    // 数据库
    DB     *gorm.DB

    // 缓存
    Cache  CacheEngine

    // 事件总线
    Events EventBus

    // 配置
    Config *AppConfig

    // 日志
    Logger *Logger

    // 获取其他 Module 的 Service（通过依赖声明后）
    GetService(moduleName string) interface{}
}
```

### 3.5 Module 生命周期

```
1. 框架启动
2. 扫描并注册所有 Module
3. 解析 Dependencies() → 构建依赖图 → 拓扑排序
4. 按依赖顺序逐个调用 Init(app)：
   a. 数据库迁移（GORM AutoMigrate）
   b. 种子数据（默认角色、初始管理员等）
   c. 注册事件监听
5. 逐个调用 RegisterRoutes(group)
6. 调用 RegisterCommands(root)（如有）
7. 启动 HTTP Server
   ...
8. 收到 Shutdown 信号
9. 逆序调用 Shutdown()（如有）
10. 关闭数据库连接、缓存等
```

**依赖解析规则：**
- 循环依赖 → 启动报错，终止
- 缺失依赖 → 启动报错，终止
- 无依赖声明 → 默认无依赖，随机顺序初始化

**推荐依赖顺序：**
```
settings → user → permission → media → taxonomy → article / page / menu
```

---

## 4. 内置 Module 功能范围

### 4.1 user（用户模块）

**类型：** 基础设施

**依赖：** 无

**功能范围：**

| 功能 | 说明 |
|------|------|
| 用户注册 | 用户名 + 邮箱 + 密码创建账号 |
| 用户登录 | JWT Token 签发，支持配置过期时间 |
| 用户登出 | Token 黑名单机制 |
| 个人信息 | 查看/修改昵称、邮箱、头像 |
| 修改密码 | 验证旧密码 + 设置新密码 |
| 用户管理（管理员） | 用户列表、创建/编辑/禁用/删除用户 |
| 角色分配（管理员） | 为用户分配角色 |

**数据模型：**

```go
type User struct {
    ID        int64     `gorm:"primaryKey;autoIncrement"`
    Username  string    `gorm:"size:50;uniqueIndex;not null"`
    Email     string    `gorm:"size:100;uniqueIndex;not null"`
    Password  string    `gorm:"size:255;not null"`  // bcrypt hash
    Nickname  string    `gorm:"size:50;not null;default:''"`
    Avatar    string    `gorm:"size:500;not null;default:''"`
    Status    string    `gorm:"size:20;not null;default:'active'"` // active | disabled
    CreatedAt time.Time
    UpdatedAt time.Time
    DeletedAt gorm.DeletedAt `gorm:"index"`
}
```

**API 端点：**

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| POST | `/api/auth/login` | 登录 | 公开 |
| POST | `/api/auth/logout` | 登出 | 已登录 |
| GET | `/api/auth/profile` | 获取当前用户信息 | 已登录 |
| PUT | `/api/auth/password` | 修改密码 | 已登录 |
| GET | `/api/users` | 用户列表 | user.read.all |
| POST | `/api/users` | 创建用户 | user.create |
| GET | `/api/users/:id` | 用户详情 | user.read.all |
| PUT | `/api/users/:id` | 编辑用户 | user.update.all |
| DELETE | `/api/users/:id` | 删除用户 | user.delete.all |

**发布的事件：**
- `user.created` — 用户创建后
- `user.updated` — 用户信息更新后
- `user.deleted` — 用户删除后
- `user.login` — 用户登录成功
- `user.password_changed` — 密码修改后

**权限声明：**

```go
Permissions: []PermissionDef{
    {Action: "create", Description: "创建用户"},
    {Action: "read",   Description: "查看用户", Scopes: []string{"own", "all"}},
    {Action: "update", Description: "编辑用户", Scopes: []string{"own", "all"}},
    {Action: "delete", Description: "删除用户"},
}
```

---

### 4.2 permission（权限模块）

**类型：** 基础设施

**依赖：** `["user"]`

**功能范围：**

| 功能 | 说明 |
|------|------|
| 角色管理 | 内置 3 个默认角色（admin / editor / author），支持自定义角色 |
| 权限分配 | 为角色分配权限（基于各 Module 的 Schema 权限声明） |
| 请求拦截 | 全局中间件，校验当前用户对请求资源的操作权限 |
| 数据范围控制 | 支持 own（仅自己的数据）和 all（全部数据）两种范围 |

**权限模型：RBAC（基于角色的访问控制）**

```
User ──(N:M)──> Role ──(1:N)──> Permission

Permission = {
    module:  "article",       // 目标 Module
    action:  "update",        // 操作（create/read/update/delete/manage）
    scope:   "own"            // 数据范围（own/all）
}
```

**数据模型：**

```go
type Role struct {
    ID          int64  `gorm:"primaryKey;autoIncrement"`
    Name        string `gorm:"size:50;uniqueIndex;not null"` // admin / editor / author / custom_xxx
    Label       string `gorm:"size:100;not null"`             // 管理员 / 编辑 / 作者
    Description string `gorm:"type:text;not null;default:''"`
    IsSystem    bool   `gorm:"not null;default:false"`        // 系统内置角色不可删除
    CreatedAt   time.Time
    UpdatedAt   time.Time
}

type UserRole struct {
    UserID int64 `gorm:"primaryKey"`
    RoleID int64 `gorm:"primaryKey"`
}

type Permission struct {
    ID       int64  `gorm:"primaryKey;autoIncrement"`
    RoleID   int64  `gorm:"index;not null"`
    Module   string `gorm:"size:50;not null"`  // Module Name
    Action   string `gorm:"size:20;not null"`  // create / read / update / delete / manage
    Scope    string `gorm:"size:20;not null;default:'all'"` // own / all
}
```

**默认角色与权限：**

| 角色 | Module | Action | Scope | 说明 |
|------|--------|--------|-------|------|
| admin | * | * | all | 所有模块、所有操作、所有数据 |
| editor | article, page, menu, taxonomy, media | create, read, update | all | 内容模块全部操作 |
| editor | article, page | delete | own | 只能删除自己的内容 |
| author | article, page | create, read, update | own | 只能操作自己的内容 |
| author | media | create, read | own | 只能上传和查看自己的媒体 |
| author | taxonomy | read | all | 只能查看分类（不能管理） |

**API 端点：**

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| GET | `/api/roles` | 角色列表 | permission.manage |
| POST | `/api/roles` | 创建自定义角色 | permission.manage |
| GET | `/api/roles/:id` | 角色详情（含权限列表） | permission.manage |
| PUT | `/api/roles/:id` | 编辑角色权限 | permission.manage |
| DELETE | `/api/roles/:id` | 删除自定义角色 | permission.manage |
| GET | `/api/permissions/available` | 获取所有可用权限（来自各 Module Schema） | permission.manage |

**中间件工作流程：**

```
请求进入 Permission 中间件
  → 从 JWT 中提取 user_id
  → 查询用户角色（缓存优先）
  → 解析请求路径 → 确定目标 Module + Action
  → 查询角色权限（缓存优先）
  → 匹配权限：
    → admin 角色 → 直接放行
    → 有 module + action 权限：
      → scope=all → 放行
      → scope=own → 注入过滤条件（created_by = current_user_id）
    → 无权限 → 返回 403
```

**发布的事件：**
- `permission.role_created` — 角色创建后
- `permission.role_updated` — 角色权限变更后
- `permission.role_deleted` — 角色删除后

---

### 4.3 media（媒体模块）

**类型：** 基础设施

**依赖：** `["user"]`

**功能范围：**

| 功能 | 说明 |
|------|------|
| 文件上传 | 单文件上传，支持 multipart/form-data |
| 缩略图生成 | 图片上传后自动生成配置的样式（尺寸由 settings module 定义） |
| 文件夹管理 | 创建、重命名、删除文件夹 |
| 媒体元信息 | Alt 文本、标题、MIME 类型、尺寸信息 |
| 媒体列表 | 分页、按文件夹筛选、按类型筛选 |
| 存储抽象 | 本地存储（默认），接口预留云存储扩展 |

**数据模型：**

```go
type Media struct {
    ID          int64  `gorm:"primaryKey;autoIncrement"`
    FolderID    *int64 `gorm:"index"`
    Filename    string `gorm:"size:255;not null"`
    StoragePath string `gorm:"size:500;not null"`
    MimeType    string `gorm:"size:100;not null"`
    Size        int64  `gorm:"not null"`
    Width       *int
    Height      *int
    Alt         string `gorm:"size:255;not null;default:''"`
    Title       string `gorm:"size:255;not null;default:''"`
    Styles      JSON   // {"thumbnail": "/uploads/...", "medium": "/uploads/..."}
    UploadedBy  int64  `gorm:"index;not null"`
    CreatedAt   time.Time
    UpdatedAt   time.Time
    DeletedAt   gorm.DeletedAt `gorm:"index"`
}

type MediaFolder struct {
    ID        int64  `gorm:"primaryKey;autoIncrement"`
    Name      string `gorm:"size:100;not null"`
    ParentID  *int64 `gorm:"index"`
    Sort      int    `gorm:"not null;default:0"`
    CreatedAt time.Time
    UpdatedAt time.Time
}
```

**API 端点：**

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| GET | `/api/media` | 媒体列表 | media.read |
| POST | `/api/media/upload` | 上传文件 | media.create |
| GET | `/api/media/:id` | 媒体详情 | media.read |
| PUT | `/api/media/:id` | 更新元信息 | media.update |
| DELETE | `/api/media/:id` | 删除文件 | media.delete |
| GET | `/api/media/folders` | 文件夹树 | media.read |
| POST | `/api/media/folders` | 创建文件夹 | media.create |
| PUT | `/api/media/folders/:id` | 重命名文件夹 | media.update |
| DELETE | `/api/media/folders/:id` | 删除文件夹 | media.delete |

**发布的事件：**
- `media.uploaded` — 文件上传完成后（含缩略图生成完成）
- `media.deleted` — 文件删除后

---

### 4.4 settings（设置模块）

**类型：** 基础设施

**依赖：** 无

**功能范围：**

| 功能 | 说明 |
|------|------|
| 站点配置读取 | 从 `config/site.yaml` 读取站点名称、Logo、联系方式等 |
| 配置 API | 提供只读 API 供前端获取站点配置 |
| 图片样式定义 | 定义缩略图尺寸（供 media module 使用） |
| SEO 默认值 | 标题后缀、默认描述、关键词 |
| 分页配置 | 默认每页条数 |

**API 端点：**

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| GET | `/api/settings` | 获取站点配置（公开 API，无需认证） | 公开 |
| GET | `/api/settings/admin` | 获取完整站点配置（含敏感信息） | settings.manage |

**发布的事件：**
- `settings.reloaded` — 配置热重载后

---

### 4.5 article（文章模块）

**类型：** 内容

**依赖：** `["user", "media", "taxonomy"]`

**功能范围：**

| 功能 | 说明 |
|------|------|
| 文章 CRUD | 创建、读取、更新、删除文章 |
| 发布流程 | 草稿 → 已发布 → 已归档 三种状态 |
| URL 别名 | 自定义 slug，唯一约束 |
| 封面图 | 关联 media module |
| 分类/标签 | 关联 taxonomy module |
| 作者关联 | 关联 user module |
| 置顶 | 布尔标记 + 列表排序 |
| SEO | 自定义 SEO 标题和描述 |

**数据模型：**

```go
type Article struct {
    ID          int64      `gorm:"primaryKey;autoIncrement"`
    Title       string     `gorm:"size:200;not null"`
    Slug        string     `gorm:"size:200;uniqueIndex;not null"`
    Summary     string     `gorm:"type:text"`
    Body        string     `gorm:"type:text;not null"`
    CoverImage  *int64     // FK → media.id
    AuthorID    int64      `gorm:"index;not null"` // FK → user.id
    Status      string     `gorm:"size:20;index;not null;default:'draft'"`
    PublishedAt *time.Time `gorm:"index"`
    IsTop       bool       `gorm:"not null;default:false"`
    SeoTitle    string     `gorm:"size:200;not null;default:''"`
    SeoDesc     string     `gorm:"size:500;not null;default:''"`
    CreatedBy   int64      `gorm:"index;not null"`
    UpdatedBy   *int64
    CreatedAt   time.Time
    UpdatedAt   time.Time
    DeletedAt   gorm.DeletedAt `gorm:"index"`
}

// 文章-分类关联（多对多）
type ArticleTaxonomy struct {
    ArticleID int64  `gorm:"primaryKey"`
    FieldID   string `gorm:"primaryKey;size:50"` // "category" / "tags"
    TermID    int64  `gorm:"primaryKey"`
}
```

**API 端点：**

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| GET | `/api/articles` | 文章列表（公开，仅 published） | 公开 |
| GET | `/api/articles/:id` | 文章详情（公开，仅 published） | 公开 |
| GET | `/api/articles/slug/:slug` | 文章详情 by slug（公开） | 公开 |
| GET | `/api/admin/articles` | 文章管理列表（全部状态） | article.read |
| POST | `/api/admin/articles` | 创建文章 | article.create |
| GET | `/api/admin/articles/:id` | 文章管理详情 | article.read |
| PUT | `/api/admin/articles/:id` | 编辑文章 | article.update |
| DELETE | `/api/admin/articles/:id` | 删除文章 | article.delete |

**发布的事件：**
- `article.created` — 文章创建后
- `article.updated` — 文章更新后
- `article.deleted` — 文章删除后
- `article.published` — 文章状态变为 published
- `article.archived` — 文章状态变为 archived

**Schema 声明（关联）：**

```go
Relations: []RelationDef{
    {Field: "AuthorID",   Target: "user",  Type: "belongs_to", OnDelete: "set_null"},
    {Field: "CoverImage", Target: "media", Type: "belongs_to", OnDelete: "set_null"},
    {Field: "categories", Target: "taxonomy", Type: "many_to_many"},
    {Field: "tags",       Target: "taxonomy", Type: "many_to_many"},
}
```

---

### 4.6 page（页面模块）

**类型：** 内容

**依赖：** `["user", "media"]`

**功能范围：**

| 功能 | 说明 |
|------|------|
| 页面 CRUD | 创建、读取、更新、删除独立页面 |
| 模板选择 | 支持选择页面模板（default / full_width / sidebar） |
| 排序权重 | 自定义排序 |
| SEO | 自定义 SEO 标题和描述 |

**数据模型：**

```go
type Page struct {
    ID          int64      `gorm:"primaryKey;autoIncrement"`
    Title       string     `gorm:"size:200;not null"`
    Slug        string     `gorm:"size:200;uniqueIndex;not null"`
    Body        string     `gorm:"type:text;not null"`
    CoverImage  *int64
    Template    string     `gorm:"size:50;not null;default:'default'"`
    SortOrder   int        `gorm:"not null;default:0"`
    Status      string     `gorm:"size:20;index;not null;default:'draft'"`
    SeoTitle    string     `gorm:"size:200;not null;default:''"`
    SeoDesc     string     `gorm:"size:500;not null;default:''"`
    CreatedBy   int64      `gorm:"index;not null"`
    UpdatedBy   *int64
    CreatedAt   time.Time
    UpdatedAt   time.Time
    DeletedAt   gorm.DeletedAt `gorm:"index"`
}
```

**API 端点：**

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| GET | `/api/pages` | 页面列表（公开，仅 published） | 公开 |
| GET | `/api/pages/:id` | 页面详情（公开） | 公开 |
| GET | `/api/pages/slug/:slug` | 页面详情 by slug | 公开 |
| GET | `/api/admin/pages` | 页面管理列表 | page.read |
| POST | `/api/admin/pages` | 创建页面 | page.create |
| GET | `/api/admin/pages/:id` | 页面管理详情 | page.read |
| PUT | `/api/admin/pages/:id` | 编辑页面 | page.update |
| DELETE | `/api/admin/pages/:id` | 删除页面 | page.delete |

**发布的事件：**
- `page.created` / `page.updated` / `page.deleted` / `page.published`

---

### 4.7 menu（菜单模块）

**类型：** 内容

**依赖：** 无

**功能范围：**

| 功能 | 说明 |
|------|------|
| 多套菜单 | 支持多套独立菜单（main / footer / sidebar 等） |
| 多级菜单项 | 支持无限层级（建议不超过 3 级） |
| 菜单项排序 | 拖拽排序 / sort 权重 |
| 外链支持 | 支持链接到外部 URL |
| 内容关联 | 菜单项可关联 article / page / taxonomy |
| YAML 初始化 | 首次启动从 `config/menus/*.yaml` 导入 |
| 后台管理覆盖 | 后台编辑后覆盖 YAML 配置 |

**数据模型：**

```go
type Menu struct {
    ID        string `gorm:"primaryKey;size:50"` // "main" / "footer"
    Name      string `gorm:"size:100;not null"`
    Source    string  `gorm:"size:10;not null;default:'yaml'"` // yaml | database
    CreatedAt time.Time
    UpdatedAt time.Time
}

type MenuItem struct {
    ID           int64   `gorm:"primaryKey;autoIncrement"`
    MenuID       string  `gorm:"size:50;index;not null"`
    ItemID       string  `gorm:"size:50;not null"`
    Label        string  `gorm:"size:100;not null"`
    URL          string  `gorm:"size:500;not null;default:''"`
    ParentID     *int64  `gorm:"index"`
    Sort         int     `gorm:"not null;default:0"`
    External     bool    `gorm:"not null;default:false"`
    Target       string  `gorm:"size:20;not null;default:'_self'"`
    ContentType  string  `gorm:"size:50;not null;default:''"`
    Icon         string  `gorm:"size:50;not null;default:''"`
    CreatedAt    time.Time
    UpdatedAt    time.Time
}
```

**API 端点：**

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| GET | `/api/menus` | 所有菜单列表（公开） | 公开 |
| GET | `/api/menus/:menuId` | 菜单详情含菜单项树（公开） | 公开 |
| GET | `/api/admin/menus` | 菜单管理列表 | menu.read |
| GET | `/api/admin/menus/:menuId` | 菜单管理详情 | menu.read |
| PUT | `/api/admin/menus/:menuId` | 更新菜单（整体替换菜单项） | menu.update |
| POST | `/api/admin/menus/:menuId/reset` | 重置为 YAML 配置 | menu.manage |

**发布的事件：**
- `menu.updated` — 菜单更新后

---

### 4.8 taxonomy（分类模块）

**类型：** 内容

**依赖：** 无

**功能范围：**

| 功能 | 说明 |
|------|------|
| 词汇表管理 | 从 YAML 配置加载分类词汇表定义 |
| 层级分类 | 支持树形结构（hierarchical: true） |
| 扁平标签 | 支持无层级标签（hierarchical: false） |
| 术语 CRUD | 创建、编辑、删除分类术语 |
| SEO | 术语可设置 SEO 标题和描述 |

**数据模型：**

```go
type Taxonomy struct {
    ID           string `gorm:"primaryKey;size:50"`
    Name         string `gorm:"size:100;not null"`
    Description  string `gorm:"type:text;not null;default:''"`
    Hierarchical bool   `gorm:"not null;default:false"`
    CreatedAt    time.Time
    UpdatedAt    time.Time
}

type TaxonomyTerm struct {
    ID          int64   `gorm:"primaryKey;autoIncrement"`
    TaxonomyID  string  `gorm:"size:50;index;not null"`
    Name        string  `gorm:"size:100;not null"`
    Slug        string  `gorm:"size:100;not null"`
    Description string  `gorm:"type:text;not null;default:''"`
    ParentID    *int64  `gorm:"index"`
    Sort        int     `gorm:"not null;default:0"`
    SeoTitle    string  `gorm:"size:200;not null;default:''"`
    SeoDesc     string  `gorm:"size:500;not null;default:''"`
    CreatedAt   time.Time
    UpdatedAt   time.Time
}
```

**API 端点：**

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| GET | `/api/taxonomies` | 词汇表列表（公开） | 公开 |
| GET | `/api/taxonomies/:vocabId/terms` | 术语列表/树（公开） | 公开 |
| GET | `/api/admin/taxonomies` | 词汇表管理列表 | taxonomy.read |
| GET | `/api/admin/taxonomies/:vocabId/terms` | 术语管理列表 | taxonomy.read |
| POST | `/api/admin/taxonomies/:vocabId/terms` | 创建术语 | taxonomy.create |
| PUT | `/api/admin/taxonomies/:vocabId/terms/:id` | 编辑术语 | taxonomy.update |
| DELETE | `/api/admin/taxonomies/:vocabId/terms/:id` | 删除术语 | taxonomy.delete |

**发布的事件：**
- `taxonomy.term_created` / `taxonomy.term_updated` / `taxonomy.term_deleted`

---

## 5. Event 事件标准化

### 5.1 命名规范

```
{module}.{action}

module = Module 的 Name() 返回值
action = 动作（past tense）
```

**示例：** `article.published`、`user.created`、`media.uploaded`

### 5.2 标准事件列表

#### 通用内容事件（article / page 等内容型 Module）

| 事件名 | 触发时机 | 载荷 |
|--------|---------|------|
| `{module}.created` | 内容创建后 | `ContentEvent{ID, Data, UserID}` |
| `{module}.updated` | 内容更新后 | `ContentEvent{ID, OldData, NewData, UserID}` |
| `{module}.deleted` | 内容删除后 | `ContentEvent{ID, UserID}` |
| `{module}.published` | 状态变为 published | `ContentEvent{ID, Data, UserID}` |
| `{module}.archived` | 状态变为 archived | `ContentEvent{ID, UserID}` |

#### 基础设施事件

| 事件名 | 触发时机 | 载荷 |
|--------|---------|------|
| `user.created` | 用户注册/创建后 | `UserEvent{UserID}` |
| `user.updated` | 用户信息更新后 | `UserEvent{UserID}` |
| `user.deleted` | 用户删除后 | `UserEvent{UserID}` |
| `user.login` | 登录成功 | `UserEvent{UserID, IP}` |
| `user.password_changed` | 密码修改后 | `UserEvent{UserID}` |
| `permission.role_updated` | 角色权限变更 | `RoleEvent{RoleID}` |
| `media.uploaded` | 文件上传完成 | `MediaEvent{MediaID, MimeType}` |
| `media.deleted` | 文件删除后 | `MediaEvent{MediaID}` |
| `menu.updated` | 菜单更新后 | `MenuEvent{MenuID}` |
| `settings.reloaded` | 站点配置重载后 | `SettingsEvent{}` |

### 5.3 事件载荷结构

```go
// ContentEvent 通用内容事件载荷
type ContentEvent struct {
    Module  string      // 模块名
    ID      int64       // 内容 ID
    Data    interface{} // 当前数据（创建/发布时）
    OldData interface{} // 旧数据（更新时）
    UserID  int64       // 操作人
}

// UserEvent 用户事件载荷
type UserEvent struct {
    UserID int64
    IP     string // 仅 login 事件
}

// RoleEvent 角色事件载荷
type RoleEvent struct {
    RoleID int64
}

// MediaEvent 媒体事件载荷
type MediaEvent struct {
    MediaID  int64
    MimeType string
}

// MenuEvent 菜单事件载荷
type MenuEvent struct {
    MenuID string
}

// SettingsEvent 配置事件载荷
type SettingsEvent struct{}
```

### 5.4 Event Bus 接口

```go
type EventBus interface {
    // Emit 发布事件（同步执行所有监听器）
    Emit(event string, payload interface{})

    // EmitAsync 异步发布事件（goroutine 中执行）
    EmitAsync(event string, payload interface{})

    // On 注册事件监听器
    On(event string, handler EventHandler)

    // Off 移除事件监听器
    Off(event string, handler EventHandler)
}

type EventHandler func(payload interface{})
```

### 5.5 内置事件监听（框架默认注册）

| 事件 | 监听者 | 处理逻辑 |
|------|--------|---------|
| `*.created` / `*.updated` / `*.deleted` | CacheInvalidator | 清除对应 Module 的缓存 |
| `permission.role_updated` | PermissionCache | 刷新权限缓存 |
| `settings.reloaded` | 所有缓存 | 全量缓存失效 |
| `user.deleted` | 各内容 Module | 将 created_by / author_id 置空 |

---

## 6. API 设计规范

### 6.1 GoFrame Bind 模式

v2.0 所有 API 使用 GoFrame 的 Bind 模式定义，框架自动处理参数绑定、校验、文档生成：

```go
// 定义 Request struct
type CreateArticleReq struct {
    g.Meta `path:"/admin/articles" method:"post" tags:"文章管理" summary:"创建文章"`
    Title  string `json:"title" v:"required|max-length:200" dc:"文章标题"`
    Slug   string `json:"slug" v:"required|regex:^[a-z0-9-]+$" dc:"URL别名"`
    Body   string `json:"body" v:"required" dc:"正文（HTML）"`
    Status string `json:"status" v:"in:draft,published,archived" d:"draft" dc:"状态"`
}

// 定义 Response struct
type CreateArticleRes struct {
    g.Meta `mime:"application/json"`
    ID     int64  `json:"id" dc:"文章ID"`
    Title  string `json:"title" dc:"标题"`
    Slug   string `json:"slug" dc:"URL别名"`
}
```

**框架自动获得的能力：**
- ✅ 参数自动绑定（JSON body → struct）
- ✅ 参数校验（`v` tag → GoFrame validation）
- ✅ 默认值（`d` tag）
- ✅ OpenAPI 3.0 文档自动生成
- ✅ Swagger UI 在 `/swagger` 路径可访问

### 6.2 路由前缀约定

| 前缀 | 说明 | 认证 |
|------|------|------|
| `/api/` | 公开 API，面向前端/第三方 | 无需 |
| `/api/admin/` | 后台管理 API | 需 JWT + RBAC |

### 6.3 统一响应格式

```go
// 成功响应
type SuccessRes struct {
    Code    int         `json:"code"`    // 0
    Message string      `json:"message"` // "ok"
    Data    interface{} `json:"data"`
}

// 错误响应
type ErrorRes struct {
    Code    int    `json:"code"`    // 非0错误码
    Message string `json:"message"` // 错误描述
}

// 分页响应
type PageRes struct {
    List     interface{} `json:"list"`
    Total    int64       `json:"total"`
    Page     int         `json:"page"`
    PageSize int         `json:"page_size"`
}
```

### 6.4 自动生成的文档端点

| 路径 | 说明 |
|------|------|
| `/api.json` | OpenAPI 3.0 JSON 文档 |
| `/swagger` | Swagger UI 交互式文档 |

---

## 7. 非功能需求

### 7.1 性能

| 指标 | 目标 |
|------|------|
| API 响应时间 | < 50ms（P95，缓存命中） |
| API 响应时间 | < 200ms（P95，缓存未命中） |
| 并发读 QPS | 1000+（SQLite + bigcache） |
| 启动时间 | < 3 秒（8 个 Module 全部初始化） |

### 7.2 安全

| 措施 | 说明 |
|------|------|
| SQL 注入防护 | GORM 参数化查询 |
| XSS 防护 | 富文本内容 sanitize（bluemonday） |
| 密码安全 | bcrypt hash（cost=10） |
| JWT 安全 | HS256 签名 + 24h 过期 + Token 黑名单 |
| 文件上传 | 类型白名单 + 大小限制 + 图片重编码 |
| 登录限流 | 同 IP 5 次/分钟 |
| RBAC 权限 | 每个 API 请求经过 Permission 中间件校验 |

### 7.3 部署

| 项目 | 说明 |
|------|------|
| 产物 | 单二进制文件（`go build`） |
| 数据库 | SQLite（默认）/ PostgreSQL（可选） |
| 缓存 | bigcache（默认）/ Redis（可选） |
| 容器化 | Dockerfile + docker-compose |
| 配置外置 | `config/` 目录（YAML 格式） |

---

## 8. 与 v1.0 的核心区别

| 维度 | v1.0 | v2.0 |
|------|------|------|
| 定位 | 全栈 CMS | Headless CMS 框架 |
| 核心架构 | SchemaEngine（大管家） | Module 容器 + Event 总线 |
| 字段定义 | YAML 配置驱动 | Go struct（Module 自管） |
| 数据操作 | `map[string]interface{}`（动态） | 强类型 struct（静态） |
| 内容类型 | 通用 CRUD，差异仅在字段 | 每个 Module 有独立 logic |
| 模块通信 | 直接调用，耦合 | Event 总线，解耦 |
| API 文档 | 手写（频繁脱节） | OpenAPI 自动生成 |
| 前端 | Vue3 管理后台 + Go Template SSR | 不含前端（Headless） |
| 权限 | 内容类型级别 + 数据范围 | Module 声明式 + 中间件拦截 |
| 扩展性 | 加 YAML 配置文件 | 写 Go Module |

---

## 9. 待深化问题回答

### 9.1 多租户/多站点

**结论：v2.0 不纳入，保持单实例单站点。**

**理由：**
1. 多租户增加每张表 `tenant_id`，所有查询都要过滤，复杂度大幅上升
2. GoCMS 定位是私活快速交付，客户通常只有一个站点
3. Module 架构已为未来多租户预留扩展点（App Context 可注入 tenant 信息）

**预留方案（v3.0）：**
- `App` 注入 `TenantID`
- 各 Module 的 `Init()` 建表时自动添加 `tenant_id` 列
- Permission 中间件注入 tenant 范围过滤

### 9.2 第三方 Module 接入机制

**v2.0 方案：本地代码级别注册（Go import）。**

开发者在 `main.go` 中手动注册第三方 Module：

```go
func main() {
    app := gocms.New()

    // 注册内置 Module
    app.RegisterBuiltins()

    // 注册第三方 Module
    app.Register(&thirdparty.ProductModule{})
    app.Register(&thirdparty.OrderModule{})

    app.Run()
}
```

**第三方 Module 开发规范：**
1. 实现 `Module` 接口
2. 以 Go package 形式发布（`go get`）
3. 自带数据模型、API 定义、业务逻辑
4. 通过 `Dependencies()` 声明依赖内置 Module
5. 通过 Event 总线与其他 Module 通信

**不在 v2.0 范围的：**
- ❌ 动态加载（Go plugin）— 兼容性差，不推荐
- ❌ 插件市场 — v3.0 规划
- ❌ Module 的可视化安装/卸载 — v3.0 规划

---

## 10. 范围与排期

### 10.1 v2.0 交付清单

| # | 交付物 | 说明 |
|---|--------|------|
| 1 | 框架核心 | Module 容器 + Event 总线 + App Context |
| 2 | API 路由层 | GoFrame Bind 模式 + OpenAPI 自动生成 |
| 3 | 中间件管道 | JWT + RBAC Permission + CORS + Cache |
| 4 | user Module | 用户认证 + 管理 |
| 5 | permission Module | RBAC 角色权限 + 中间件 |
| 6 | media Module | 文件上传 + 缩略图 + 文件夹 |
| 7 | settings Module | 站点配置 |
| 8 | article Module | 文章 CRUD + 发布流程 |
| 9 | page Module | 页面 CRUD |
| 10 | menu Module | 菜单管理 + YAML 初始化 |
| 11 | taxonomy Module | 分类/标签 |
| 12 | 部署支持 | 单二进制 + Dockerfile |
| 13 | OpenAPI 文档 | 自动生成，/swagger 可访问 |

### 10.2 里程碑建议

| 阶段 | 内容 | 预估 |
|------|------|------|
| **M1 — 框架核心** | Module 容器 + Event 总线 + App Context + GoFrame Bind + 中间件管道 | 5 天 |
| **M2 — 基础设施 Module** | user + permission + media + settings | 5 天 |
| **M3 — 内容 Module** | article + page + menu + taxonomy | 5 天 |
| **M4 — 联调 & 优化** | 全流程联调 + 缓存优化 + 构建部署 | 3 天 |
| **合计** | | **18 天** |

---

## 附录 A：完整 API 端点汇总

| Module | 公开 API | 管理 API | 合计 |
|--------|---------|---------|------|
| user | 0 | 9（含 auth 4 + user CRUD 5） | 9 |
| permission | 0 | 6 | 6 |
| media | 0 | 9 | 9 |
| settings | 1 | 1 | 2 |
| article | 3 | 5 | 8 |
| page | 3 | 5 | 8 |
| menu | 2 | 4 | 6 |
| taxonomy | 2 | 5 | 7 |
| **合计** | **11** | **44** | **55** |

## 附录 B：配置文件结构

```
config/
├── config.yaml           # 应用配置（端口、数据库、缓存、JWT）
├── site.yaml             # 站点全局配置（名称、Logo、联系方式）
├── content-types/        # 【废弃】v2.0 不再使用 YAML 定义内容类型
├── taxonomies/           # 分类词汇表定义（taxonomy module 读取）
│   ├── article_category.yaml
│   └── tags.yaml
└── menus/                # 菜单初始配置（menu module 读取）
    ├── main.yaml
    └── footer.yaml
```

---

_PRD v2.0 完成。后续变更请基于此版本迭代。_

_— 阿产（@pm）2026-03-29_
