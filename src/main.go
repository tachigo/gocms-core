// GoCMS v2.0 — Module-based Headless CMS Framework
// 入口：解析 CLI 命令 → 启动对应子命令（默认 server）
package main

import (
	"github.com/gogf/gf/v2/os/gctx"

	"github.com/tachigo/gocms-core/internal/cmd"
)

func main() {
	cmd.Main.Run(gctx.New())
}
