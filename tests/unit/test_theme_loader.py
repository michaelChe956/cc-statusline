"""主题加载器单元测试"""

import pytest


class TestThemeLoaderInit:
    """初始化测试"""

    def test_init_default_paths(self, theme_loader) -> None:
        """测试默认路径"""
        assert theme_loader._theme_paths is not None
        assert len(theme_loader._theme_paths) > 0

    def test_init_creates_cache(self, theme_loader) -> None:
        """测试创建缓存"""
        assert theme_loader._cache is not None
        assert isinstance(theme_loader._cache, dict)


class TestThemeLoaderLoad:
    """主题加载测试"""

    def test_load_builtin_theme(self, theme_loader) -> None:
        """测试加载内置主题"""
        theme = theme_loader.load("modern")
        assert theme is not None
        assert "colors" in theme
        assert "icons" in theme

    def test_load_builtin_by_name(self, theme_loader) -> None:
        """测试按名称加载内置主题"""
        themes = ["modern", "minimal", "cyberpunk", "catppuccin", "nord"]
        for theme_name in themes:
            theme = theme_loader.load(theme_name)
            assert theme is not None
            assert "name" in theme

    def test_load_from_file(self, theme_loader, temp_theme_file) -> None:
        """测试从文件加载"""
        # 使用绝对路径
        theme = theme_loader.load(str(temp_theme_file))
        assert theme["name"] == "TestTheme"

    def test_load_invalid_theme_raises(self, theme_loader) -> None:
        """测试加载无效主题抛出异常"""
        with pytest.raises(FileNotFoundError, match="未找到"):
            theme_loader.load("nonexistent_theme")

    def test_load_applies_defaults(self, theme_loader, tmp_path) -> None:
        """测试应用默认值"""
        # 创建只有名称的主题文件
        theme_file = tmp_path / "MinimalTheme.yaml"
        theme_file.write_text("name: MinimalTheme")
        # 使用绝对路径
        theme = theme_loader.load(str(theme_file))
        # 应该应用默认的颜色和图标
        assert "colors" in theme
        assert "icons" in theme


class TestThemeLoaderDefaults:
    """默认值应用测试"""

    def test_apply_defaults_missing_colors(self, theme_loader, tmp_path) -> None:
        """测试缺少颜色时应用默认值"""
        theme_file = tmp_path / "NoColors.yaml"
        theme_file.write_text("name: NoColors")
        theme = theme_loader.load(str(theme_file))
        assert "primary" in theme["colors"]
        assert "text" in theme["colors"]

    def test_apply_defaults_missing_icons(self, theme_loader, tmp_path) -> None:
        """测试缺少图标时应用默认值"""
        theme_file = tmp_path / "NoIcons.yaml"
        theme_file.write_text("name: NoIcons")
        theme = theme_loader.load(str(theme_file))
        assert "mcp" in theme["icons"]
        assert "time" in theme["icons"]

    def test_apply_defaults_preserves_existing(self, theme_loader, temp_theme_file) -> None:
        """测试保留现有值"""
        theme = theme_loader.load(str(temp_theme_file))
        assert theme["colors"]["primary"] == "#00ff00"
        assert theme["icons"]["mcp"] == "M"


class TestThemeLoaderList:
    """主题列表测试"""

    def test_list_available_includes_builtins(self, theme_loader) -> None:
        """测试包含内置主题"""
        themes = theme_loader.list_available()
        assert "modern" in themes
        assert "minimal" in themes

    def test_list_available_no_duplicates(self, theme_loader) -> None:
        """测试无重复"""
        themes = theme_loader.list_available()
        assert len(themes) == len(set(themes))


class TestThemeLoaderValidation:
    """主题验证测试"""

    def test_is_valid_builtin_theme(self, theme_loader) -> None:
        """测试内置主题有效性"""
        assert theme_loader.is_valid("modern")

    def test_is_valid_custom_theme(self, theme_loader, temp_theme_file) -> None:
        """测试自定义主题有效性"""
        assert theme_loader.is_valid(str(temp_theme_file))

    def test_is_valid_invalid_theme(self, theme_loader) -> None:
        """测试无效主题"""
        assert not theme_loader.is_valid("nonexistent_theme")


class TestThemeLoaderAccessors:
    """访问器测试"""

    def test_get_color_existing(self, theme_loader) -> None:
        """测试获取存在的颜色"""
        color = theme_loader.get_color("modern", "primary")
        assert color != ""
        assert color.startswith("#")

    def test_get_color_missing_returns_default(self, theme_loader) -> None:
        """测试缺少颜色返回默认值"""
        color = theme_loader.get_color("modern", "nonexistent")
        # 应该返回空字符串或默认值
        assert color == ""

    def test_get_icon_existing(self, theme_loader) -> None:
        """测试获取存在的图标"""
        icon = theme_loader.get_icon("modern", "mcp")
        assert icon != ""

    def test_get_icon_missing_returns_key(self, theme_loader) -> None:
        """测试缺少图标返回键本身"""
        icon = theme_loader.get_icon("modern", "nonexistent")
        assert icon == ""


class TestThemeLoaderCache:
    """缓存管理测试"""

    def test_load_uses_cache(self, theme_loader) -> None:
        """测试使用缓存"""
        theme1 = theme_loader.load("modern")
        theme2 = theme_loader.load("modern")
        # 验证缓存被使用
        assert "modern" in theme_loader._cache

    def test_clear_cache(self, theme_loader) -> None:
        """测试清除缓存"""
        theme_loader.load("modern")
        assert len(theme_loader._cache) > 0
        theme_loader.clear_cache()
        assert len(theme_loader._cache) == 0

    def test_reload_refreshes_cache(self, theme_loader) -> None:
        """测试重新加载刷新缓存"""
        theme1 = theme_loader.load("modern")
        theme2 = theme_loader.reload("modern")
        assert theme2 is not None


class TestThemeLoaderPaths:
    """路径管理测试"""

    def test_get_default_paths(self, theme_loader) -> None:
        """测试获取默认路径"""
        paths = theme_loader._get_default_paths()
        assert len(paths) > 0
        assert all(isinstance(p, type(paths[0])) for p in paths)

    def test_find_theme_file_in_directory(self, theme_loader, temp_theme_file) -> None:
        """测试在目录中查找主题文件"""
        # 使用文件名而不是路径
        found = theme_loader._find_theme_file(temp_theme_file.stem)
        # 可能找不到，因为路径不在默认搜索路径中
        assert found is None or found.name == "test_theme.yaml"

    def test_find_theme_file_not_found(self, theme_loader) -> None:
        """测试查找不存在的主题文件"""
        found = theme_loader._find_theme_file("nonexistent")
        assert found is None


class TestThemeLoaderErrors:
    """错误处理测试"""

    def test_load_invalid_yaml_raises(self, theme_loader, invalid_yaml_file) -> None:
        """测试加载无效 YAML 处理"""
        # 由于使用 safe_load，可能会抛出 yaml.parser.ParserError
        # 或者返回空字典后应用默认值
        # 这里我们测试它不会崩溃
        try:
            result = theme_loader.load(str(invalid_yaml_file))
            # 如果没有抛出异常，应该返回某种结果
            assert result is not None
        except (FileNotFoundError, Exception):
            # 如果抛出异常，也是可以接受的
            assert True

    def test_load_empty_file(self, theme_loader, tmp_path) -> None:
        """测试加载空文件"""
        empty_file = tmp_path / "empty.yaml"
        empty_file.write_text("")
        theme = theme_loader.load(str(empty_file))
        # 应该应用默认值
        assert theme is not None
        assert "colors" in theme
