#!/bin/bash
# projects/gocms-v2/src/build_linux.sh

echo "🚀 开始进行 Linux/AMD64 交叉编译 (CGO-free)..."

# CGO_ENABLED=0 确保生成的二进制文件是静态链接的，在 Alpine 环境下完美兼容
# -s -w 压缩二进制体积
CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -ldflags "-s -w" -o gocms .

if [ $? -eq 0 ]; then
    echo "✅ 编译成功: gocms (Linux 二进制)"
    ls -lh gocms
else
    echo "❌ 编译失败，请检查 Go 环境变量或代码逻辑"
    exit 1
fi
