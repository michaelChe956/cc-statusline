#!/bin/bash
# cc-statusline 发布脚本
# 用途：自动构建并上传到 PyPI

set -e  # 遇到错误立即退出

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# 显示帮助信息
show_help() {
    cat << EOF
${BLUE}cc-statusline 发布脚本${NC}

用法:
    $0 [选项]

选项:
    -t, --test        发布到 TestPyPI（默认）
    -p, --prod        发布到正式 PyPI
    -b, --build-only  仅构建，不上传
    -c, --check       检查构建产物
    -h, --help        显示此帮助信息

示例:
    $0                # 构建并上传到 TestPyPI
    $0 --prod         # 构建并上传到正式 PyPI
    $0 --build-only   # 仅构建，不上传

环境变量:
    TWINE_USERNAME    Twine 用户名（默认：__token__）
    TWINE_PASSWORD    Twine 密码/API Token
    TWINE_REPOSITORY  Twine 仓库（testpypi 或 pypi）

EOF
}

# 默认参数
REPOSITORY="testpypi"
BUILD_ONLY=false
CHECK_ONLY=false

# 解析参数
while [[ $# -gt 0 ]]; do
    case $1 in
        -t|--test)
            REPOSITORY="testpypi"
            shift
            ;;
        -p|--prod)
            REPOSITORY="pypi"
            shift
            ;;
        -b|--build-only)
            BUILD_ONLY=true
            shift
            ;;
        -c|--check)
            CHECK_ONLY=true
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            print_error "未知参数: $1"
            show_help
            exit 1
            ;;
    esac
done

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

print_info "项目根目录: $PROJECT_ROOT"
cd "$PROJECT_ROOT"

# 检查虚拟环境
if [ ! -d ".venv" ]; then
    print_error "未找到虚拟环境 .venv"
    print_info "请先运行: uv venv"
    exit 1
fi

# 检查构建工具
if ! .venv/bin/python -c "import build" 2>/dev/null; then
    print_warning "未安装 build 工具，正在安装..."
    uv pip install build
fi

if ! .venv/bin/python -c "import twine" 2>/dev/null; then
    print_warning "未安装 twine 工具，正在安装..."
    uv pip install twine
fi

# 显示当前配置
echo ""
print_info "发布配置"
echo "  仓库: $REPOSITORY"
echo "  仅构建: $BUILD_ONLY"
echo "  仅检查: $CHECK_ONLY"
echo ""

# 确认发布到正式 PyPI
if [ "$REPOSITORY" = "pypi" ]; then
    print_warning "您即将发布到${RED}正式 PyPI${NC}！"
    read -p "确认继续？(yes/no): " confirm
    if [ "$confirm" != "yes" ]; then
        print_info "已取消"
        exit 0
    fi
fi

# 步骤 1：清理旧的构建产物
print_info "步骤 1/4：清理旧的构建产物"
rm -rf dist/ build/ *.egg-info
print_success "清理完成"

# 步骤 2：构建包
print_info "步骤 2/4：构建包"
.venv/bin/python -m build

if [ ! -d "dist" ] || [ -z "$(ls -A dist)" ]; then
    print_error "构建失败：未找到 dist 目录或为空"
    exit 1
fi

print_success "构建完成"
ls -lh dist/

# 步骤 3：验证包
print_info "步骤 3/4：验证包完整性"
.venv/bin/twine check dist/*

if [ $? -ne 0 ]; then
    print_error "包验证失败"
    exit 1
fi

print_success "包验证通过"

# 仅检查模式
if [ "$CHECK_ONLY" = true ]; then
    print_success "检查完成，未上传"
    exit 0
fi

# 仅构建模式
if [ "$BUILD_ONLY" = true ]; then
    print_success "构建完成，未上传"
    exit 0
fi

# 步骤 4：上传包
print_info "步骤 4/4：上传到 $REPOSITORY"

# 检查 ~/.pypirc 配置
if [ ! -f "$HOME/.pypirc" ]; then
    print_warning "未找到 ~/.pypirc 配置文件"
    print_info "您可以使用以下模板创建："
    cat << EOF

[distutils]
index-servers =
    pypi
    testpypi

[testpypi]
username = __token__
password = <your-testpypi-token>

[pypi]
username = __token__
password = <your-pypi-token>
EOF
fi

# 上传
.venv/bin/twine upload --repository "$REPOSITORY" dist/*

if [ $? -eq 0 ]; then
    print_success "上传成功！"

    # 显示包链接
    echo ""
    print_info "包链接："
    if [ "$REPOSITORY" = "testpypi" ]; then
        VERSION=$(grep "^version = " pyproject.toml | sed 's/version = "\(.*\)"/\1/')
        echo "  https://test.pypi.org/project/cc-statusline/$VERSION/"
        echo ""
        print_info "验证安装命令："
        echo "  uvx --extra-index-url https://test.pypi.org/simple/ --index-strategy unsafe-best-match cc-statusline --version"
    else
        echo "  https://pypi.org/project/cc-statusline/"
        echo ""
        print_info "验证安装命令："
        echo "  uvx cc-statusline --version"
    fi
else
    print_error "上传失败"
    exit 1
fi
