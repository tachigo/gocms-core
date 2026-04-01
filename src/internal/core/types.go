// Package core 公共类型定义
// ModuleSchema / FieldDef / PermissionDef / RelationDef / Event 载荷等
package core

// ---------------------------------------------------------------------------
// Module 类型标记
// ---------------------------------------------------------------------------

// ModuleKind 模块类型枚举
type ModuleKind string

const (
	// KindContent 内容型模块（article, page, menu, taxonomy）
	KindContent ModuleKind = "content"
	// KindInfrastructure 基础设施模块（user, permission, media, settings）
	KindInfrastructure ModuleKind = "infrastructure"
)

// ---------------------------------------------------------------------------
// ModuleSchema — 模块元信息声明
// ---------------------------------------------------------------------------

// ModuleSchema 每个 Module 通过 Schema() 向框架声明的元信息
// 供权限系统、健康检查、后台 UI 使用
type ModuleSchema struct {
	// Kind 模块类型：content / infrastructure
	Kind ModuleKind

	// Fields 字段声明（供后台 UI 自动渲染，内容型模块使用）
	Fields []FieldDef

	// Groups 字段分组
	Groups []FieldGroup

	// Permissions 权限声明（供 permission 模块构建权限矩阵）
	Permissions []PermissionDef

	// Relations 关联声明（供依赖分析和级联删除使用）
	Relations []RelationDef
}

// ---------------------------------------------------------------------------
// 字段定义
// ---------------------------------------------------------------------------

// FieldType 字段类型枚举
type FieldType string

const (
	FieldText     FieldType = "text"
	FieldTextarea FieldType = "textarea"
	FieldRichtext FieldType = "richtext"
	FieldNumber   FieldType = "number"
	FieldBoolean  FieldType = "boolean"
	FieldDate     FieldType = "date"
	FieldDatetime FieldType = "datetime"
	FieldSelect   FieldType = "select"
	FieldImage    FieldType = "image"
	FieldFile     FieldType = "file"
	FieldSlug     FieldType = "slug"
	FieldColor    FieldType = "color"
	FieldJSON     FieldType = "json"
)

// FieldDef 字段定义（供后台 UI 使用）
type FieldDef struct {
	ID          string                 `json:"id"`          // 字段标识（对应 Go struct 的 json tag）
	Type        FieldType              `json:"type"`        // 字段类型
	Label       string                 `json:"label"`       // 显示标签
	Required    bool                   `json:"required"`    // 是否必填
	Default     interface{}            `json:"default"`     // 默认值
	Validations map[string]interface{} `json:"validations"` // 校验规则
	Options     map[string]interface{} `json:"options"`     // 附加选项（如 select 的选项列表）
}

// FieldGroup 字段分组（控制后台表单布局）
type FieldGroup struct {
	ID     string   `json:"id"`     // 分组标识
	Label  string   `json:"label"`  // 分组标签
	Fields []string `json:"fields"` // 包含的字段 ID 列表
}

// ---------------------------------------------------------------------------
// 权限定义
// ---------------------------------------------------------------------------

// PermissionDef 权限声明
// 每个 Module 声明自己需要的权限，permission 模块据此构建完整权限矩阵
type PermissionDef struct {
	Action      string   `json:"action"`      // 操作：create / read / update / delete / manage
	Description string   `json:"description"` // 描述：如 "创建文章"
	Scopes      []string `json:"scopes"`      // 数据范围：["own", "all"]
}

// ---------------------------------------------------------------------------
// 关联定义
// ---------------------------------------------------------------------------

// RelationDef 关联声明
type RelationDef struct {
	Field    string `json:"field"`     // 本模块的字段
	Target   string `json:"target"`    // 目标模块名
	Type     string `json:"type"`      // belongs_to / has_many / many_to_many
	OnDelete string `json:"on_delete"` // set_null / restrict / cascade
}

// ---------------------------------------------------------------------------
// Event 载荷类型
// ---------------------------------------------------------------------------

// ContentEvent 通用内容事件载荷（article/page 等内容型模块使用）
type ContentEvent struct {
	Module  string      `json:"module"`   // 模块名
	ID      int64       `json:"id"`       // 内容 ID
	Data    interface{} `json:"data"`     // 当前数据
	OldData interface{} `json:"old_data"` // 旧数据（仅 update 事件）
	UserID  int64       `json:"user_id"`  // 操作人 ID
}

// UserEvent 用户事件载荷
type UserEvent struct {
	UserID int64  `json:"user_id"`
	IP     string `json:"ip"` // 仅 login 事件
}

// RoleEvent 角色事件载荷
type RoleEvent struct {
	RoleID int64 `json:"role_id"`
}

// MediaEvent 媒体事件载荷
type MediaEvent struct {
	MediaID  int64  `json:"media_id"`
	MimeType string `json:"mime_type"`
}

// MenuEvent 菜单事件载荷
type MenuEvent struct {
	MenuID string `json:"menu_id"`
}

// SettingsEvent 配置事件载荷
type SettingsEvent struct{}
