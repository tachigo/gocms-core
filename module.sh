#!/bin/bash

# ============================================================
# GoCMS 项目管理脚本 (Local Project CLI)
# ============================================================

set -e

# 获取当前项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${PROJECT_ROOT}/.env.gocms" 

# --- 1. 环境加载与探测 ---
if [[ -f "$ENV_FILE" ]]; then
    # shellcheck source=/dev/null
    source "$ENV_FILE"
fi

# --- 2. 跨平台兼容性补丁 ---
sed_i() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i "" "$@"
    else
        sed -i "$@"
    fi
}

ASSEMBLY_FILE="${PROJECT_ROOT}/src/cmd/assembly.go"

# --- 3. 核心工具函数 ---
log_info() { echo -e "\033[34m[INFO]\033[0m $1"; }
log_ok()   { echo -e "\033[32m[OK]\033[0m $1"; }
log_err()  { echo -e "\033[31m[ERR]\033[0m $1"; }

# 自动刷新导入中心 (assembly.go)
update_assembly() {
    local module="$1"
    local import_line="_ \"gocms/module/$module\""
    
    # 逻辑适配：如果这个项目是 app 层，可能需要引用内核的 module 或者是本地的 module
    # 这里我们统一采用 Go Module 命名空间逻辑
    
    # 检查是否已存在
    if grep -q "module/$module\"" "$ASSEMBLY_FILE" 2>/dev/null; then
        return 0
    fi
    
    # 在 import ( 之后安全插入内容，兼容 Mac/Linux
    log_info "正在装配模块 $module 到 assembly.go..."
    local awk_cmd="/import \\(/ { print; print \"    _ \\\"gocms/module/$module\\\"\"; next } { print }"
    awk "$awk_cmd" "$ASSEMBLY_FILE" > "$ASSEMBLY_FILE.tmp" && mv "$ASSEMBLY_FILE.tmp" "$ASSEMBLY_FILE"
    gofmt -w "$ASSEMBLY_FILE"
}

# --- 4. 命令实现 ---

# 4.1 挂载本地源码
cmd_link() {
    local name="$1"
    if [[ -z "$name" ]]; then
        log_err "请指定模块名，例如: ./module.sh link user"
        exit 1
    fi

    if [[ -z "$GOCMS_MODULES_PATH" ]]; then
        log_err "❌ GOCMS_MODULES_PATH 未配置，请检查 .env.gocms"
        exit 1
    fi

    local module_src="../../${GOCMS_MODULES_PATH}/${name}"
    local target_path="${name}"
    cd "${PROJECT_ROOT}/src/module"
    if [[ ! -d "$module_src" ]]; then
        log_err "错误: 模块源码不存在: $module_src"
        exit 1
    fi

    mkdir -p "${PROJECT_ROOT}/src/module"
    ln -sf "$module_src" "$target_path"
    log_ok "模块软链已挂载: $target_path"

    # 执行装配
    update_assembly "$name"
}

# 4.2 物理下载模块
cmd_install() {
    local full_name="$1" # e.g. user@v1.0.1
    if [[ -z "$full_name" ]]; then
        log_err "请指定模块版本，例如: ./module.sh install user@v1.0.1"
        exit 1
    fi

    local name="${full_name%@*}"
    local version="${full_name#*@}"
    [[ "$name" == "$full_name" ]] && version="main"

    log_info "正在安装模块: $name ($version)"

    local target_path="${PROJECT_ROOT}/src/internal/module/${name}"
    mkdir -p "$(dirname "$target_path")"

    # 克隆特定版本 (假设 github.com/tachigo/gocms-modules 结构)
    # 注意：这里的逻辑可能需要动态适配不同的 Git 仓库结构
    # 目前我们暂时模拟克隆
    log_info "git clone --branch $version ..."
    # git clone --branch "$version" "..." "$target_path"

    # 执行装配
    update_assembly "$name"
}

# --- 5. 入口分发 ---
case "$1" in
    link)    cmd_link "$2" ;;
    install) cmd_install "$2" ;;
    *) echo "用法: $0 {link|install} <module_name>" ;;
esac
