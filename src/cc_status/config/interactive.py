"""交互式安装器

提供用户友好的交互式配置向导
"""

from typing import Any, Optional

from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.validation import Validator

from cc_status.config.installer import ClaudeConfigInstaller
from cc_status.theme import get_theme_names


class InteractiveInstaller:
    """交互式安装器"""

    @classmethod
    def run(cls) -> bool:
        """运行交互式安装向导

        Returns:
            是否安装成功
        """
        print("━" * 60)
        print("🎨 cc-statusline 交互式安��向导")
        print("━" * 60)
        print()

        # 1. 主题选择
        theme = cls.select_theme()
        if not theme:
            print("\n❌ 取消安装")
            return False

        # 2. 刷新间隔配置
        interval = cls.configure_interval()
        if interval is None:
            print("\n❌ 取消安装")
            return False

        # 3. 确认安装
        config = {
            "theme": theme,
            "interval": interval,
        }

        if not cls.confirm_install(config):
            print("\n❌ 取消安装")
            return False

        # 4. 执行安装
        print("\n🚀 开始安装...")

        # mypy 类型断言
        theme_value = config["theme"]
        interval_value = config["interval"]
        assert isinstance(theme_value, str)
        assert isinstance(interval_value, int)

        success = ClaudeConfigInstaller.install(
            force=True,  # 交互式模式下默认覆盖
            theme=theme_value,
            interval=interval_value,
        )

        if success:
            print("\n✅ 安装完成！")
            print("\n下一步:")
            print("  1. 重启 Claude Code 以应用更改")
            print("  2. 使用 'cc-statusline verify --health' 验证配置")

        return success

    @classmethod
    def select_theme(cls) -> Optional[str]:
        """交互式主题选择

        Returns:
            选择的主题名称，取消则返回 None
        """
        print("📋 步骤 1/3: 选择主题")
        print("-" * 60)

        # 获取可用主题
        themes = sorted(get_theme_names())

        if not themes:
            print("❌ 未找到可用主题")
            return None

        # 显示主题列表
        print("\n可用主题:")
        for i, theme_name in enumerate(themes, 1):
            print(f"  {i}. {theme_name}")

        print()

        # 创建主题补全器
        theme_completer = WordCompleter(themes, ignore_case=True)

        # 提示用户输入
        while True:
            try:
                user_input = prompt(
                    "请输入主题名称或序号 (默认: modern, q 取消): ",
                    completer=theme_completer,
                    default="modern",
                )

                if user_input.lower() == "q":
                    return None

                # 检查是否为序号
                if user_input.isdigit():
                    idx = int(user_input) - 1
                    if 0 <= idx < len(themes):
                        selected = themes[idx]
                        break
                    else:
                        print(f"⚠️  无效序号，请输入 1-{len(themes)}")
                        continue

                # 检查是否为主题名称
                if user_input in themes:
                    selected = user_input
                    break
                else:
                    print(f"⚠️  未知主题: {user_input}")
                    continue

            except (KeyboardInterrupt, EOFError):
                return None

        # 预览主题
        cls.preview_theme(selected)

        return selected

    @classmethod
    def preview_theme(cls, theme: str) -> None:
        """预览主题效果

        Args:
            theme: 主题名称
        """
        print(f"\n🎨 主题预览: {theme}")
        print("-" * 60)

        try:
            from cc_status.engine.statusline_engine import EngineConfig, StatuslineEngine

            # 创建引擎预览
            config = EngineConfig(
                theme=theme,
                modules=["session_time", "mcp_status"],
            )
            engine = StatuslineEngine(config)
            engine.initialize()
            engine.start()

            output = engine.get_combined_output()
            print(output)

            engine.stop()
        except Exception as e:
            print(f"⚠️  预览失败: {e}")

        print("-" * 60)

    @classmethod
    def configure_interval(cls) -> Optional[int]:
        """配置刷新间隔

        Returns:
            刷新间隔（毫秒），取消则返回 None
        """
        print("\n📋 步骤 2/3: 配置刷新间隔")
        print("-" * 60)
        print("\n推荐值:")
        print("  5000ms  - 快速刷新（5秒）")
        print("  10000ms - 标准刷新（10秒，推荐）")
        print("  30000ms - 慢速刷新（30秒）")
        print()

        # 创建验证器
        class IntervalValidator(Validator):
            def validate(self, document: Any) -> None:
                text = document.text.strip()
                if text.lower() == "q":
                    return
                try:
                    value = int(text)
                    if value < 1000 or value > 60000:
                        raise ValueError("范围错误") from None
                except ValueError as e:
                    raise ValueError("请输入 1000-60000 之间的整数") from e

        # 提示用户输入
        while True:
            try:
                user_input = prompt(
                    "请输入刷新间隔(ms) (1000-60000, 默认: 10000, q 取消): ",
                    validator=IntervalValidator(),
                    default="10000",
                )

                if user_input.lower() == "q":
                    return None

                interval = int(user_input)
                return interval

            except (KeyboardInterrupt, EOFError):
                return None

    @classmethod
    def confirm_install(cls, config: dict[str, Any]) -> bool:
        """确认安装配置

        Args:
            config: 配置字典

        Returns:
            是否确认安装
        """
        print("\n📋 步骤 3/3: 确认配置")
        print("-" * 60)
        print("\n配置摘要:")
        print(f"  主题: {config['theme']}")
        print(f"  刷新间隔: {config['interval']}ms")
        print()

        try:
            confirm = prompt(
                "确认安装? (Y/n): ",
                default="Y",
            )
            return confirm.lower() in ["y", "yes", ""]
        except (KeyboardInterrupt, EOFError):
            return False
