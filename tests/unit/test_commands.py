"""CLI 命令模块单元测试"""

import argparse
from unittest.mock import MagicMock, patch

import pytest

from cc_status.cli import commands


class TestCreateParser:
    """参数解析器测试类"""

    def test_create_parser(self) -> None:
        """测试创建解析器"""
        parser = commands.create_parser()
        assert isinstance(parser, argparse.ArgumentParser)
        assert parser.prog == "cc-statusline"

    def test_parse_version(self) -> None:
        """测试解析版本参数"""
        parser = commands.create_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["--version"])

    def test_parse_list_themes(self) -> None:
        """测试解析列出主题参数"""
        parser = commands.create_parser()
        args = parser.parse_args(["--list-themes"])
        assert args.list_themes is True

    def test_parse_list_modules(self) -> None:
        """测试解析列出模块参数"""
        parser = commands.create_parser()
        args = parser.parse_args(["--list-modules"])
        assert args.list_modules is True

    def test_parse_once(self) -> None:
        """测试解析单次输出参数"""
        parser = commands.create_parser()
        args = parser.parse_args(["--once"])
        assert args.once is True

    def test_parse_theme(self) -> None:
        """测试解析主题参数"""
        parser = commands.create_parser()
        args = parser.parse_args(["--theme", "cyberpunk"])
        assert args.theme == "cyberpunk"

    def test_parse_install_command(self) -> None:
        """测试解析安装命令"""
        parser = commands.create_parser()
        args = parser.parse_args(["install"])
        assert args.command == "install"
        assert args.theme == "modern"
        assert args.interval == 10000
        assert args.force is False

    def test_parse_install_with_options(self) -> None:
        """测试解析安装命令（带选项）"""
        parser = commands.create_parser()
        args = parser.parse_args(["install", "--force", "--theme", "nord", "-i", "5000"])
        assert args.command == "install"
        assert args.force is True
        assert args.theme == "nord"
        assert args.interval == 5000

    def test_parse_install_interactive(self) -> None:
        """测试解析交互式安装"""
        parser = commands.create_parser()
        args = parser.parse_args(["install", "--interactive"])
        assert args.command == "install"
        assert args.interactive is True

    def test_parse_uninstall_command(self) -> None:
        """测试解析卸载命令"""
        parser = commands.create_parser()
        args = parser.parse_args(["uninstall"])
        assert args.command == "uninstall"

    def test_parse_verify_command(self) -> None:
        """测试解析验证命令"""
        parser = commands.create_parser()
        args = parser.parse_args(["verify"])
        assert args.command == "verify"
        assert args.verbose is False
        assert args.test is False
        assert args.health is False

    def test_parse_verify_with_options(self) -> None:
        """测试解析验证命令（带选项）"""
        parser = commands.create_parser()
        args = parser.parse_args(["verify", "--verbose", "--test", "--health"])
        assert args.command == "verify"
        assert args.verbose is True
        assert args.test is True
        assert args.health is True

    def test_parse_export_command(self) -> None:
        """测试解析导出命令"""
        parser = commands.create_parser()
        args = parser.parse_args(["export", "/tmp/config.json"])
        assert args.command == "export"
        assert args.path == "/tmp/config.json"
        assert args.no_metadata is False

    def test_parse_export_no_metadata(self) -> None:
        """测试解析导出命令（不带元数据）"""
        parser = commands.create_parser()
        args = parser.parse_args(["export", "/tmp/config.json", "--no-metadata"])
        assert args.command == "export"
        assert args.no_metadata is True

    def test_parse_import_command(self) -> None:
        """测试解析导入命令"""
        parser = commands.create_parser()
        args = parser.parse_args(["import", "/tmp/config.json"])
        assert args.command == "import"
        assert args.path == "/tmp/config.json"
        assert args.force is False

    def test_parse_import_force(self) -> None:
        """测试解析导入命令（强制覆盖）"""
        parser = commands.create_parser()
        args = parser.parse_args(["import", "/tmp/config.json", "--force"])
        assert args.command == "import"
        assert args.force is True


class TestCmdListThemes:
    """列出主题命令测试类"""

    @patch("cc_status.theme.theme_loader")
    @patch("cc_status.theme.get_theme_names")
    def test_cmd_list_themes(self, mock_get_names: MagicMock, mock_loader: MagicMock) -> None:
        """测试列出所有主题"""
        mock_get_names.return_value = ["modern", "minimal"]
        mock_loader.list_available.return_value = []
        mock_loader.load.side_effect = [
            {"name": "Modern", "description": "默认主题"},
            {"name": "Minimal", "description": "极简主题"},
        ]

        # 不应该抛出异常
        commands.cmd_list_themes()


class TestCmdListModules:
    """列出模块命令测试类"""

    @patch("cc_status.modules.registry.ModuleRegistry")
    def test_cmd_list_modules(self, mock_registry: MagicMock) -> None:
        """测试列出所有模块"""
        mock_registry.list_modules.return_value = [
            {"name": "mcp_status", "enabled": True},
            {"name": "session_time", "enabled": True},
        ]
        mock_registry.list_modules.return_value = [
            {"name": "mcp_status", "enabled": True},
            {"name": "session_time", "enabled": True},
        ]

        # 不应该抛出异常
        commands.cmd_list_modules()


class TestCmdInstall:
    """安装命令测试类"""

    @patch("cc_status.config.ClaudeConfigInstaller")
    def test_cmd_install_basic(self, mock_installer_class: MagicMock) -> None:
        """测试基本安装命令"""
        mock_installer_class.install.return_value = True

        args = argparse.Namespace(
            theme="modern",
            interval=10000,
            force=False,
            interactive=False,
        )

        result = commands.cmd_install(args)
        assert result == 0
        mock_installer_class.install.assert_called_once()

    @patch("cc_status.config.ClaudeConfigInstaller")
    def test_cmd_install_failure(self, mock_installer_class: MagicMock) -> None:
        """测试安装失败"""
        mock_installer_class.install.return_value = False

        args = argparse.Namespace(
            theme="modern",
            interval=10000,
            force=False,
            interactive=False,
        )

        result = commands.cmd_install(args)
        assert result == 1


class TestCmdUninstall:
    """卸载命令测试类"""

    @patch("cc_status.config.ClaudeConfigInstaller")
    def test_cmd_uninstall_basic(self, mock_installer_class: MagicMock) -> None:
        """测试基本卸载命令"""
        mock_installer_class.uninstall.return_value = True

        args = argparse.Namespace()

        result = commands.cmd_uninstall(args)
        assert result == 0
        mock_installer_class.uninstall.assert_called_once()

    @patch("cc_status.config.ClaudeConfigInstaller")
    def test_cmd_uninstall_failure(self, mock_installer_class: MagicMock) -> None:
        """测试卸载失败"""
        mock_installer_class.uninstall.return_value = False

        args = argparse.Namespace()

        result = commands.cmd_uninstall(args)
        assert result == 1


class TestCmdVerify:
    """验证命令测试类"""

    @patch("cc_status.config.ClaudeConfigInstaller")
    def test_cmd_verify_basic(self, mock_installer_class: MagicMock) -> None:
        """测试基本验证命令"""
        mock_installer_class.verify.return_value = True

        args = argparse.Namespace(verbose=False, test=False, health=False)

        result = commands.cmd_verify(args)
        assert result == 0

    @patch("cc_status.config.ClaudeConfigInstaller")
    def test_cmd_verify_verbose(self, mock_installer_class: MagicMock) -> None:
        """测试详细验证"""
        mock_installer_class.verify.return_value = True

        args = argparse.Namespace(verbose=True, test=False, health=False)

        result = commands.cmd_verify(args)
        assert result == 0
        mock_installer_class.verify.assert_called_with(verbose=True, test_command=False)

    @patch("cc_status.config.ClaudeConfigInstaller")
    def test_cmd_verify_with_test(self, mock_installer_class: MagicMock) -> None:
        """测试验证（带命令测试）"""
        mock_installer_class.verify.return_value = True

        args = argparse.Namespace(verbose=False, test=True, health=False)

        result = commands.cmd_verify(args)
        assert result == 0
        mock_installer_class.verify.assert_called_with(verbose=False, test_command=True)

    @patch("cc_status.config.ClaudeConfigInstaller")
    def test_cmd_verify_health_check(self, mock_installer_class: MagicMock) -> None:
        """测试健康检查"""
        mock_installer_class.health_check.return_value = {
            "config_exists": True,
            "config_valid": True,
            "statusline_exists": True,
            "command_found": True,
            "command_executable": True,
            "version": "0.0.1",
            "details": {"config_path": "~/.claude/settings.json"},
        }

        args = argparse.Namespace(verbose=False, test=False, health=True)

        result = commands.cmd_verify(args)
        assert result == 0
        mock_installer_class.health_check.assert_called_once()

    @patch("cc_status.config.ClaudeConfigInstaller")
    def test_cmd_verify_failure(self, mock_installer_class: MagicMock) -> None:
        """测试验证失败"""
        mock_installer_class.verify.return_value = False

        args = argparse.Namespace(verbose=False, test=False, health=False)

        result = commands.cmd_verify(args)
        assert result == 1


class TestCmdExport:
    """导出命令测试类"""

    @patch("cc_status.config.ClaudeConfigInstaller")
    def test_cmd_export_basic(self, mock_installer_class: MagicMock) -> None:
        """测试基本导出命令"""
        mock_installer_class.export_config.return_value = True

        args = argparse.Namespace(path="/tmp/export.json", no_metadata=False)

        result = commands.cmd_export(args)
        assert result == 0
        mock_installer_class.export_config.assert_called_once()

    @patch("cc_status.config.ClaudeConfigInstaller")
    def test_cmd_export_no_metadata(self, mock_installer_class: MagicMock) -> None:
        """测试导出（不带元数据）"""
        mock_installer_class.export_config.return_value = True

        args = argparse.Namespace(path="/tmp/export.json", no_metadata=True)

        result = commands.cmd_export(args)
        assert result == 0

    @patch("cc_status.config.ClaudeConfigInstaller")
    def test_cmd_export_failure(self, mock_installer_class: MagicMock) -> None:
        """测试导出失败"""
        mock_installer_class.export_config.return_value = False

        args = argparse.Namespace(path="/tmp/export.json", no_metadata=False)

        result = commands.cmd_export(args)
        assert result == 1


class TestCmdImport:
    """导入命令测试类"""

    @patch("cc_status.config.ClaudeConfigInstaller")
    def test_cmd_import_basic(self, mock_installer_class: MagicMock) -> None:
        """测试基本导入命令"""
        mock_installer_class.import_config.return_value = True

        args = argparse.Namespace(path="/tmp/import.json", force=False)

        result = commands.cmd_import(args)
        assert result == 0
        mock_installer_class.import_config.assert_called_once()

    @patch("cc_status.config.ClaudeConfigInstaller")
    def test_cmd_import_force(self, mock_installer_class: MagicMock) -> None:
        """测试强制导入"""
        mock_installer_class.import_config.return_value = True

        args = argparse.Namespace(path="/tmp/import.json", force=True)

        result = commands.cmd_import(args)
        assert result == 0

    @patch("cc_status.config.ClaudeConfigInstaller")
    def test_cmd_import_failure(self, mock_installer_class: MagicMock) -> None:
        """测试导入失败"""
        mock_installer_class.import_config.return_value = False

        args = argparse.Namespace(path="/tmp/import.json", force=False)

        result = commands.cmd_import(args)
        assert result == 1


class TestMain:
    """主函数测试类"""

    @patch("cc_status.cli.commands.cmd_list_themes")
    def test_main_list_themes(self, mock_cmd: MagicMock) -> None:
        """测试主函数（列出主题）"""
        result = commands.main(["--list-themes"])
        assert result == 0
        mock_cmd.assert_called_once()

    @patch("cc_status.cli.commands.create_parser")
    def test_main_no_args(self, mock_parser: MagicMock) -> None:
        """测试主函数（无参数）"""
        args = MagicMock()
        args.command = None
        args.list_themes = False
        args.list_modules = False
        args.once = False
        args.json = False
        args.info = False
        args.daemon = False

        mock_parser.return_value.parse_args.return_value = args

        # 不应该抛出异常
        try:
            commands.main([])
        except SystemExit:
            pass  # 预期的退出
