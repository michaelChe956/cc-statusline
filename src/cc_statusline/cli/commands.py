"""命令行接口。

提供 cc-statusline 的 CLI 命令。
"""

import argparse
import json
import sys
from typing import Optional

from cc_statusline import __version__


def create_parser() -> argparse.ArgumentParser:
    """创建参数解析器。

    Returns:
        解析器实例
    """
    parser = argparse.ArgumentParser(
        prog="cc-statusline",
        description="Claude Code 状态栏工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  cc-statusline              # 启动状态栏
  cc-statusline --theme modern  # 使用指定主题
  cc-statusline --list-modules  # 列出可用模块
  cc-statusline --list-themes   # 列出可用主题
  cc-statusline --once          # 单次输出

  cc-statusline install      # 安装到 Claude Code
  cc-statusline uninstall    # 从 Claude Code 卸载
        """,
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    # 创建子命令
    subparsers = parser.add_subparsers(dest="command", help="子命令")

    # install 子命令
    install_parser = subparsers.add_parser(
        "install",
        help="安装状态栏配置到 Claude Code",
        description="自动配置 ~/.claude/settings.json 以启用状态栏",
    )
    install_parser.add_argument(
        "--force",
        action="store_true",
        help="强制覆盖现有配置",
    )
    install_parser.add_argument(
        "-t",
        "--theme",
        dest="theme",
        default="modern",
        help="使用指定主题 (默认: modern)",
    )
    install_parser.add_argument(
        "-i",
        "--interval",
        dest="interval",
        type=int,
        default=10000,
        help="刷新间隔，单位毫秒 (默认: 10000)",
    )
    install_parser.add_argument(
        "--interactive",
        action="store_true",
        help="使用交互式安装向导",
    )

    # uninstall 子命令
    subparsers.add_parser(
        "uninstall",
        help="移除状态栏配置",
        description="从 ~/.claude/settings.json 移除状态栏配置",
    )

    # verify 子命令
    verify_parser = subparsers.add_parser(
        "verify",
        help="验证状态栏配置",
        description="检查 ~/.claude/settings.json 中的状态栏配置是否有效",
    )
    verify_parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="显示详细验证信息",
    )
    verify_parser.add_argument(
        "--test",
        action="store_true",
        help="测试命令执行",
    )
    verify_parser.add_argument(
        "--health",
        action="store_true",
        help="显示完整健康检查报告",
    )

    # export 子命令
    export_parser = subparsers.add_parser(
        "export",
        help="导出状态栏配置",
        description="导出 ~/.claude/settings.json 中的状态栏配置到文件",
    )
    export_parser.add_argument(
        "path",
        help="导出文件路径",
    )
    export_parser.add_argument(
        "--no-metadata",
        action="store_true",
        help="不包含元数据（版本号和导出时间）",
    )

    # import 子命令
    import_parser = subparsers.add_parser(
        "import",
        help="导入状态栏配置",
        description="从文件导入状态栏配置到 ~/.claude/settings.json",
    )
    import_parser.add_argument(
        "path",
        help="导入文件路径",
    )
    import_parser.add_argument(
        "--force",
        action="store_true",
        help="强制覆盖现有配置",
    )

    # 主命令参数（向后兼容）
    parser.add_argument(
        "-t",
        "--theme",
        dest="theme",
        default="modern",
        help="使用指定主题 (默认: modern)",
    )

    parser.add_argument(
        "-m",
        "--modules",
        dest="modules",
        nargs="+",
        default=None,
        help="指定要启用的模块",
    )

    parser.add_argument(
        "--list-themes",
        action="store_true",
        help="列出所有可用的主题",
    )

    parser.add_argument(
        "--list-modules",
        action="store_true",
        help="列出所有可用的模块",
    )

    parser.add_argument(
        "--once",
        action="store_true",
        help="只输出一次状态栏并退出",
    )

    parser.add_argument(
        "--json",
        action="store_true",
        help="以 JSON 格式输出",
    )

    parser.add_argument(
        "--info",
        action="store_true",
        help="显示引擎状态信息",
    )

    parser.add_argument(
        "--daemon",
        action="store_true",
        help="以守护进程模式运行（后台更新）",
    )

    parser.add_argument(
        "--preset",
        dest="preset",
        default="standard",
        choices=["minimal", "standard", "full"],
        help="使用预设布局 (默认: standard)",
    )

    parser.add_argument(
        "--style",
        dest="style",
        default="arrow",
        choices=["arrow", "round", "slant", "curve", "minimal"],
        help="Powerline 分隔符样式 (默认: arrow)",
    )

    parser.add_argument(
        "--watch",
        action="store_true",
        help="实时监控模式（独立终端）",
    )

    parser.add_argument(
        "--interval",
        dest="interval",
        type=float,
        default=1.0,
        help="刷新间隔（秒）(默认: 1.0)",
    )

    return parser


def cmd_list_themes() -> None:
    """列出所有主题。"""
    from cc_statusline.theme import get_theme_names, theme_loader

    themes = get_theme_names()
    available = theme_loader.list_available()

    print("可用主题:")
    print("-" * 40)
    for name in sorted(set(themes + available)):
        try:
            theme = theme_loader.load(name)
            desc = theme.get("description", "")
            print(f"  {name:15} - {desc}")
        except Exception:
            print(f"  {name:15} - [加载失败]")

    print()
    print(f"总计: {len(set(themes + available))} 个主题")


def cmd_install(args: argparse.Namespace) -> int:
    """处理 install 子命令。

    Args:
        args: 解析后的命令行参数

    Returns:
        退出码
    """
    from cc_statusline.config import ClaudeConfigInstaller

    try:
        # 交互式安装模式
        if args.interactive:
            from cc_statusline.config import InteractiveInstaller

            success = InteractiveInstaller.run()
            return 0 if success else 1

        # 标准安装模式
        success = ClaudeConfigInstaller.install(
            force=args.force,
            theme=args.theme,
            interval=args.interval,
        )
        return 0 if success else 1
    except Exception as e:
        print(f"❌ 安装失败: {e}", file=sys.stderr)
        return 1


def cmd_uninstall(args: argparse.Namespace) -> int:
    """处理 uninstall 子命令。

    Args:
        args: 解析后的命令行参数

    Returns:
        退出码
    """
    from cc_statusline.config import ClaudeConfigInstaller

    try:
        success = ClaudeConfigInstaller.uninstall()
        return 0 if success else 1
    except Exception as e:
        print(f"❌ 卸载失败: {e}", file=sys.stderr)
        return 1


def cmd_verify(args: argparse.Namespace) -> int:
    """处理 verify 子命令。

    Args:
        args: 解析后的命令行参数

    Returns:
        退出码
    """
    from cc_statusline.config import ClaudeConfigInstaller

    try:
        # 健康检查模式
        if args.health:
            report = ClaudeConfigInstaller.health_check()

            print("🔍 cc-statusline 健康检查报告")
            print("━" * 50)

            # 配置文件
            icon = "✅" if report["config_exists"] else "❌"
            print(f"{icon} 配置文件: {report['details']['config_path']}")

            if report["config_exists"]:
                # JSON 格式
                icon = "✅" if report["config_valid"] else "❌"
                print(f"{icon} 配置格式: JSON {'有效' if report['config_valid'] else '无效'}")

                if report["config_valid"]:
                    # 状态栏配置
                    icon = "✅" if report["statusline_exists"] else "❌"
                    print(
                        f"{icon} 状态栏配置: {'已配置' if report['statusline_exists'] else '未配置'}"
                    )

                    if report["statusline_exists"]:
                        # 命令路径
                        icon = "✅" if report["command_found"] else "❌"
                        cmd = report["details"].get("command", "")
                        print(f"{icon} 命令路径: {cmd}")

                        # 命令可执行性
                        if report["command_found"]:
                            icon = "✅" if report["command_executable"] else "❌"
                            print(
                                f"{icon} 命令执行: {'测试通过' if report['command_executable'] else '测试失败'}"
                            )

                            # 版本信息
                            if report["version"]:
                                print(f"ℹ️  版本: {report['version']}")
                else:
                    error = report["details"].get("parse_error", "")
                    print(f"  错误: {error}")

            print("━" * 50)

            # 总体状态
            all_ok = all(
                [
                    report["config_exists"],
                    report["config_valid"],
                    report["statusline_exists"],
                    report["command_found"],
                    report["command_executable"],
                ]
            )

            if all_ok:
                print("状态: 健康 ✅")
                return 0
            else:
                print("状态: 异常 ⚠️")
                return 1

        # 标准验证模式
        success = ClaudeConfigInstaller.verify(
            verbose=args.verbose,
            test_command=args.test,
        )
        return 0 if success else 1
    except Exception as e:
        print(f"❌ 验证失败: {e}", file=sys.stderr)
        return 1


def cmd_export(args: argparse.Namespace) -> int:
    """处理 export 子命令。

    Args:
        args: 解析后的命令行参数

    Returns:
        退出码
    """
    from pathlib import Path

    from cc_statusline.config import ClaudeConfigInstaller

    try:
        success = ClaudeConfigInstaller.export_config(
            path=Path(args.path),
            include_metadata=not args.no_metadata,
        )
        return 0 if success else 1
    except Exception as e:
        print(f"❌ 导出失败: {e}", file=sys.stderr)
        return 1


def cmd_import(args: argparse.Namespace) -> int:
    """处理 import 子命令。

    Args:
        args: 解析后的命令行参数

    Returns:
        退出码
    """
    from pathlib import Path

    from cc_statusline.config import ClaudeConfigInstaller

    try:
        success = ClaudeConfigInstaller.import_config(
            path=Path(args.path),
            force=args.force,
        )
        return 0 if success else 1
    except Exception as e:
        print(f"❌ 导入失败: {e}", file=sys.stderr)
        return 1


def cmd_list_modules() -> None:
    """列出所有模块。"""
    # 导入模块以注册它们
    import cc_statusline.modules.basic  # noqa: F401
    import cc_statusline.modules.cost  # noqa: F401
    import cc_statusline.modules.mcp_status  # noqa: F401
    import cc_statusline.modules.model  # noqa: F401
    import cc_statusline.modules.realtime  # noqa: F401
    import cc_statusline.modules.session_time  # noqa: F401
    import cc_statusline.modules.time_modules  # noqa: F401
    from cc_statusline.modules.registry import ModuleRegistry

    registered = ModuleRegistry.list_modules()
    enabled = ModuleRegistry.list_modules(enabled_only=True)

    print("可用模块:")
    print("-" * 60)

    for name in sorted([str(n) for n in registered]):
        try:
            metadata = ModuleRegistry.get_metadata(name)
            status = "✓ 已启用" if name in enabled else "✗ 已禁用"
            print(f"  {name:20} {status}")
            print(f"    {metadata.description}")
        except Exception:
            print(f"  {name:20} [加载失败]")

    print()
    print(f"总计: {len(registered)} 个模块, {len(enabled)} 个已启用")


def cmd_status(args: argparse.Namespace) -> None:
    """执行 status 命令。"""
    # 导入模块以注册它们
    import cc_statusline.modules.basic  # noqa: F401
    import cc_statusline.modules.cost  # noqa: F401
    import cc_statusline.modules.mcp_status  # noqa: F401
    import cc_statusline.modules.model  # noqa: F401
    import cc_statusline.modules.realtime  # noqa: F401
    import cc_statusline.modules.session_time  # noqa: F401
    import cc_statusline.modules.time_modules  # noqa: F401
    from cc_statusline.engine.statusline_engine import EngineConfig, StatuslineEngine
    from cc_statusline.render.powerline import PowerlineLayout, PowerlineRenderer
    from cc_statusline.render.terminal_renderer import TerminalRenderer
    from cc_statusline.theme import theme_loader

    # 根据预设确定默认模块
    preset_modules = {
        "minimal": ["dir", "git_branch", "model", "cost_session", "context_pct"],
        "standard": ["dir", "git_branch", "model", "version", "context_bar", "session_time", "cost_session", "cost_today"],
        "full": ["dir", "git_branch", "model", "plan", "version", "context_bar", "session_time", "reset_timer", "cost_session", "cost_today", "burn_rate", "mcp_status", "agent_status"],
    }

    # 创建引擎配置
    modules = args.modules or preset_modules.get(args.preset, preset_modules["standard"])
    config = EngineConfig(
        theme=args.theme,
        modules=modules,
        refresh_interval=args.interval,
    )

    # 创建引擎
    engine = StatuslineEngine(config)

    # 尝试从 stdin 读取 Claude Code 传递的上下文数据
    context: dict = {}
    try:
        # 检查 stdin 是否有数据（非交互模式）
        import sys

        if not sys.stdin.isatty():
            stdin_data = sys.stdin.read()
            if stdin_data.strip():
                import json

                context = json.loads(stdin_data)
                engine.set_context(context)
    except (json.JSONDecodeError, OSError):
        pass

    if args.info:
        # 显示信息
        engine.initialize()
        engine.start()

        status = engine.get_status()
        theme_info = engine.get_theme_info()
        module_info = engine.get_module_info()

        if args.json:
            print(
                json.dumps(
                    {
                        "status": status,
                        "theme": theme_info,
                        "modules": module_info,
                        "preset": args.preset,
                        "style": args.style,
                    },
                    indent=2,
                    ensure_ascii=False,
                )
            )
        else:
            print("引擎状态:")
            print(f"  状态: {status['state']}")
            print(f"  主题: {status['theme']}")
            print(f"  显示模式: {status['display_mode']}")
            print(f"  刷新间隔: {status['refresh_interval']}s")
            print(f"  模块数量: {status['modules']['total']} / {status['modules']['enabled']}")
            print(f"  预设: {args.preset}")
            print(f"  样式: {args.style}")
            print()
            print("主题信息:")
            print(f"  名称: {theme_info['name']}")
            print(f"  描述: {theme_info['description']}")
            print()
            print("模块列表:")
            for m in module_info:
                print(f"  - {m['name']}: {m['description']}")

        engine.stop()
        return

    if args.once:
        # 单次输出
        engine.initialize()
        engine.start()

        # 使用 Powerline 渲染器
        renderer = PowerlineRenderer(args.theme, args.style)
        outputs = engine.get_outputs()

        # 根据预设渲染
        output = PowerlineLayout.render_preset(args.preset, outputs, renderer)

        if args.json:
            print(
                json.dumps(
                    {
                        "theme": args.theme,
                        "preset": args.preset,
                        "style": args.style,
                        "output": output,
                        "modules": {name: out.to_dict() for name, out in outputs.items()},
                    },
                    indent=2,
                    ensure_ascii=False,
                )
            )
        else:
            print(output)

        engine.stop()
        return

    # 交互模式
    renderer = TerminalRenderer(engine, theme_loader)
    renderer.run()


def cmd_run(args: argparse.Namespace) -> None:
    """运行_run(args: argparse状态栏。"""
    from cc_statusline.engine.statusline_engine import EngineConfig, StatuslineEngine
    from cc_statusline.render.terminal_renderer import TerminalRenderer
    from cc_statusline.theme import theme_loader

    # 创建引擎配置
    config = EngineConfig(
        theme=args.theme,
        modules=args.modules or ["mcp_status", "session_time"],
    )

    # 创建引擎
    engine = StatuslineEngine(config)

    # 创建渲染器
    renderer = TerminalRenderer(engine, theme_loader)

    # 运行
    renderer.run()


def main(args: Optional[list[str]] = None) -> int:
    """主入口函数。

    Args:
        args: 命令行参数

    Returns:
        退出码
    """
    parser = create_parser()
    parsed_args = parser.parse_args(args)

    try:
        # 处理子命令
        if parsed_args.command == "install":
            return cmd_install(parsed_args)
        elif parsed_args.command == "uninstall":
            return cmd_uninstall(parsed_args)
        elif parsed_args.command == "verify":
            return cmd_verify(parsed_args)
        elif parsed_args.command == "export":
            return cmd_export(parsed_args)
        elif parsed_args.command == "import":
            return cmd_import(parsed_args)

        # 处理主命令（向后兼容）
        if parsed_args.list_themes:
            cmd_list_themes()
            return 0

        if parsed_args.list_modules:
            cmd_list_modules()
            return 0

        cmd_status(parsed_args)
        return 0

    except KeyboardInterrupt:
        print("\n取消")
        return 130
    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
