"""配置安装器的单元测试"""

import json
from unittest.mock import MagicMock, patch

import pytest

from cc_status.config.installer import ClaudeConfigInstaller


class TestClaudeConfigInstaller:
    """ClaudeConfigInstaller 类的测试"""

    def test_read_config_empty(self, tmp_path):
        """测试读取不存在的配置文件"""
        with patch.object(ClaudeConfigInstaller, "CONFIG_PATH", tmp_path / "settings.json"):
            config = ClaudeConfigInstaller._read_config()
            assert config == {}

    def test_read_config_existing(self, tmp_path):
        """测试读取已存在的配置文件"""
        config_path = tmp_path / "settings.json"
        test_config = {"key": "value", "nested": {"item": 123}}

        config_path.write_text(json.dumps(test_config))

        with patch.object(ClaudeConfigInstaller, "CONFIG_PATH", config_path):
            config = ClaudeConfigInstaller._read_config()
            assert config == test_config

    def test_write_config(self, tmp_path):
        """测试写入配置文件"""
        config_path = tmp_path / "settings.json"
        test_config = {"statusLine": {"type": "command"}}

        with patch.object(ClaudeConfigInstaller, "CONFIG_PATH", config_path):
            ClaudeConfigInstaller._write_config(test_config)

            assert config_path.exists()
            written_config = json.loads(config_path.read_text())
            assert written_config == test_config

    def test_backup_config(self, tmp_path):
        """测试备份配置文件"""
        config_path = tmp_path / "settings.json"
        config_path.write_text(json.dumps({"test": "data"}))

        with patch.object(ClaudeConfigInstaller, "CONFIG_PATH", config_path):
            backup_path = ClaudeConfigInstaller.backup_config()

            assert backup_path.exists()
            assert backup_path.name.startswith("settings.json.backup.")
            assert json.loads(backup_path.read_text()) == {"test": "data"}

    def test_backup_config_no_file(self, tmp_path):
        """测试备份不存在的文件应抛出异常"""
        config_path = tmp_path / "settings.json"

        with patch.object(ClaudeConfigInstaller, "CONFIG_PATH", config_path):
            with pytest.raises(FileNotFoundError):
                ClaudeConfigInstaller.backup_config()

    @patch("subprocess.run")
    def test_detect_command_uvx(self, mock_run):
        """测试检测 uvx 命令"""
        # 模拟 uvx 可用
        mock_run.side_effect = [
            MagicMock(returncode=0),  # uvx --version
            MagicMock(returncode=0),  # uvx cc-statusline --version
        ]

        command = ClaudeConfigInstaller.detect_command()
        assert command == "uvx cc-statusline"

    @patch("subprocess.run")
    def test_detect_command_global(self, mock_run):
        """测试检测全局安装命令"""
        # 模拟 uvx 不可用，全局命令可用
        mock_run.side_effect = [
            MagicMock(returncode=1),  # uvx --version 失败
            MagicMock(returncode=0),  # cc-statusline --version
        ]

        command = ClaudeConfigInstaller.detect_command()
        assert command == "cc-statusline"

    @patch("subprocess.run")
    def test_detect_command_python(self, mock_run):
        """测试检测 python -m 命令"""
        # 模拟前两个都不可用
        mock_run.side_effect = [
            MagicMock(returncode=1),  # uvx --version 失败
            MagicMock(returncode=1),  # cc-statusline --version 失败
            MagicMock(returncode=0),  # python -m cc_status --version
        ]

        command = ClaudeConfigInstaller.detect_command()
        assert command == "python -m cc_status"

    @patch("subprocess.run")
    def test_detect_command_none(self, mock_run):
        """测试所有命令都不可用"""
        # 所有命令都失败
        mock_run.side_effect = [
            MagicMock(returncode=1),  # uvx
            MagicMock(returncode=1),  # cc-statusline
            MagicMock(returncode=1),  # python -m
        ]

        command = ClaudeConfigInstaller.detect_command()
        assert command is None

    @patch.object(ClaudeConfigInstaller, "detect_command")
    @patch("builtins.print")
    def test_install_no_command(self, mock_print, mock_detect):
        """测试命令检测失败时的安装"""
        mock_detect.return_value = None

        success = ClaudeConfigInstaller.install()
        assert not success

    @patch.object(ClaudeConfigInstaller, "detect_command")
    @patch.object(ClaudeConfigInstaller, "backup_config")
    def test_install_success(self, mock_backup, mock_detect, tmp_path):
        """测试成功安装配置"""
        config_path = tmp_path / "settings.json"
        mock_detect.return_value = "uvx cc-statusline"
        mock_backup.return_value = tmp_path / "backup"

        with patch.object(ClaudeConfigInstaller, "CONFIG_PATH", config_path):
            success = ClaudeConfigInstaller.install(force=True, theme="modern", interval=5000)

            assert success
            assert config_path.exists()

            config = json.loads(config_path.read_text())
            assert "statusLine" in config
            assert config["statusLine"]["type"] == "command"
            assert "uvx cc-statusline" in config["statusLine"]["command"]
            assert config["statusLine"]["refreshInterval"] == 5000

    @patch.object(ClaudeConfigInstaller, "detect_command")
    @patch("builtins.print")
    def test_install_already_exists(self, mock_print, mock_detect, tmp_path):
        """测试配置已存在时的安装"""
        config_path = tmp_path / "settings.json"
        existing_config = {"statusLine": {"type": "command"}}
        config_path.write_text(json.dumps(existing_config))

        mock_detect.return_value = "uvx cc-statusline"

        with patch.object(ClaudeConfigInstaller, "CONFIG_PATH", config_path):
            success = ClaudeConfigInstaller.install(force=False)

            assert not success  # 未强制覆盖，应返回 False

    @patch.object(ClaudeConfigInstaller, "backup_config")
    def test_uninstall_success(self, mock_backup, tmp_path):
        """测试成功卸载配置"""
        config_path = tmp_path / "settings.json"
        config = {"statusLine": {"type": "command"}, "otherKey": "value"}
        config_path.write_text(json.dumps(config))

        mock_backup.return_value = tmp_path / "backup"

        with patch.object(ClaudeConfigInstaller, "CONFIG_PATH", config_path):
            success = ClaudeConfigInstaller.uninstall()

            assert success

            # 验证 statusLine 被移除，但其他配置保留
            updated_config = json.loads(config_path.read_text())
            assert "statusLine" not in updated_config
            assert updated_config["otherKey"] == "value"

    @patch("builtins.print")
    def test_uninstall_no_config(self, mock_print, tmp_path):
        """测试配置文件不存在时的卸载"""
        config_path = tmp_path / "settings.json"

        with patch.object(ClaudeConfigInstaller, "CONFIG_PATH", config_path):
            success = ClaudeConfigInstaller.uninstall()

            assert not success

    def test_verify_valid(self, tmp_path):
        """测试验证有效配置"""
        config_path = tmp_path / "settings.json"
        config = {
            "statusLine": {
                "type": "command",
                "command": "uvx cc-statusline --once",
                "refreshInterval": 10000,
            }
        }
        config_path.write_text(json.dumps(config))

        with patch.object(ClaudeConfigInstaller, "CONFIG_PATH", config_path):
            assert ClaudeConfigInstaller.verify()

    @patch("builtins.print")
    def test_verify_missing_file(self, mock_print, tmp_path):
        """测试验证不存在的配置文件"""
        config_path = tmp_path / "settings.json"

        with patch.object(ClaudeConfigInstaller, "CONFIG_PATH", config_path):
            assert not ClaudeConfigInstaller.verify()

    @patch("builtins.print")
    def test_verify_invalid_type(self, mock_print, tmp_path):
        """测试验证无效类型的配置"""
        config_path = tmp_path / "settings.json"
        config = {"statusLine": {"type": "text", "command": "test"}}
        config_path.write_text(json.dumps(config))

        with patch.object(ClaudeConfigInstaller, "CONFIG_PATH", config_path):
            assert not ClaudeConfigInstaller.verify()
