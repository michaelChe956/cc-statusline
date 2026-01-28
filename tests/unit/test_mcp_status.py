"""MCP 状态模块单元测试"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from cc_statusline.modules.mcp_status import MCPServerInfo, MCPStatusModule
from cc_statusline.modules.base import ModuleStatus


class TestMCPServerInfo:
    """MCP 服务器信息测试类"""

    def test_create_server_info(self) -> None:
        """测试创建服务器信息"""
        info = MCPServerInfo(
            name="test-server",
            status="running",
            command="npx -y server",
            host="localhost",
            port=3000,
        )
        assert info.name == "test-server"
        assert info.status == "running"
        assert info.command == "npx -y server"
        assert info.host == "localhost"
        assert info.port == 3000
        assert info.error_message is None


class TestMCPStatusModule:
    """MCP 状态模块测试类"""

    def test_metadata(self) -> None:
        """测试模块元数据"""
        module = MCPStatusModule()
        metadata = module.metadata

        assert metadata.name == "mcp_status"
        assert metadata.description == "显示所有 MCP 服务器状态"
        assert metadata.version == "1.0.0"
        assert metadata.author == "Claude Code"
        assert metadata.enabled is True

    @patch("cc_statusline.modules.mcp_status.subprocess.run")
    def test_detect_servers_from_command(self, mock_run: MagicMock) -> None:
        """测试从命令检测服务器"""
        # 模拟命令输出
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="server1 (running)\nserver2\nserver3 (running)\n",
        )

        module = MCPStatusModule()
        module.initialize()

        servers = module._get_from_claude_command()
        assert len(servers) == 3
        assert servers[0].name == "server1"
        assert servers[0].status == "running"
        assert servers[1].name == "server2"
        assert servers[1].status == "unknown"

    @patch("cc_statusline.modules.mcp_status.subprocess.run")
    def test_detect_servers_command_fails(self, mock_run: MagicMock) -> None:
        """测试命令失败时的处理"""
        mock_run.side_effect = FileNotFoundError()

        module = MCPStatusModule()
        servers = module._get_from_claude_command()
        assert len(servers) == 0

    def test_parse_mcp_config(self, tmp_path: Path) -> None:
        """测试解析 MCP 配置文件"""
        # 创建临时配置文件
        config_data = {
            "mcpServers": {
                "test-server": {
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-test"],
                },
                "another-server": {
                    "command": "python",
                    "args": ["server.py"],
                },
            }
        }

        config_file = tmp_path / "mcp.json"
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config_data, f)

        module = MCPStatusModule()
        servers = module._parse_mcp_config(config_file)

        assert len(servers) == 2
        assert servers[0].name == "test-server"
        assert servers[0].command == "npx -y @modelcontextprotocol/server-test"
        assert servers[1].name == "another-server"
        assert servers[1].command == "python server.py"

    def test_parse_mcp_config_invalid_json(self, tmp_path: Path) -> None:
        """测试解析无效 JSON 配置文件"""
        config_file = tmp_path / "mcp.json"
        with open(config_file, "w", encoding="utf-8") as f:
            f.write("invalid json")

        module = MCPStatusModule()
        servers = module._parse_mcp_config(config_file)
        assert len(servers) == 0

    @patch("cc_statusline.modules.mcp_status.subprocess.run")
    def test_get_output_no_servers(self, mock_run: MagicMock) -> None:
        """测试无服务器时的输出"""
        mock_run.side_effect = FileNotFoundError()

        module = MCPStatusModule()
        module.initialize()

        output = module.get_output()
        assert output.text == "无 MCP 服务器"
        assert output.icon == "🔌"
        assert output.color == "gray"
        assert output.status == ModuleStatus.SUCCESS

    @patch("cc_statusline.modules.mcp_status.subprocess.run")
    def test_get_output_all_running(self, mock_run: MagicMock) -> None:
        """测试全部服务器运行中的输出"""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="server1 (running)\nserver2 (running)\n",
        )

        module = MCPStatusModule()
        module.initialize()

        output = module.get_output()
        assert output.text == "2/2 运行中"
        assert output.icon == "🟢"
        assert output.color == "green"
        assert output.status == ModuleStatus.SUCCESS

    @patch("cc_statusline.modules.mcp_status.subprocess.run")
    def test_get_output_partial_running(self, mock_run: MagicMock) -> None:
        """测试部分服务器运行中的输出"""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="server1 (running)\nserver2\n",
        )

        module = MCPStatusModule()
        module.initialize()

        output = module.get_output()
        assert output.text == "1/2 运行中"
        assert output.icon == "🟡"
        assert output.color == "yellow"
        assert output.status == ModuleStatus.WARNING

    @patch("cc_statusline.modules.mcp_status.subprocess.run")
    def test_get_output_with_errors(self, mock_run: MagicMock) -> None:
        """测试有错误服务器的输出"""
        module = MCPStatusModule()

        # 手动设置服务器状态以测试错误情况
        module._servers = {
            "server1": MCPServerInfo(name="server1", status="running"),
            "server2": MCPServerInfo(name="server2", status="error"),
        }

        output = module.get_output()
        assert "错误" in output.text
        assert output.icon == "🔴"
        assert output.color == "red"
        assert output.status == ModuleStatus.ERROR

    @patch("cc_statusline.modules.mcp_status.subprocess.run")
    def test_get_server_details(self, mock_run: MagicMock) -> None:
        """测试获取服务器详细信息"""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="server1 (running)\n",
        )

        module = MCPStatusModule()
        module.initialize()

        details = module.get_server_details()
        assert len(details) == 1
        assert details[0]["name"] == "server1"
        assert details[0]["status"] == "running"

    def test_is_available(self) -> None:
        """测试模块可用性检查"""
        module = MCPStatusModule()
        assert module.is_available() is True

    def test_get_refresh_interval(self) -> None:
        """测试获取刷新间隔"""
        module = MCPStatusModule()
        assert module.get_refresh_interval() == 10.0

    @patch("cc_statusline.modules.mcp_status.subprocess.run")
    def test_cleanup(self, mock_run: MagicMock) -> None:
        """测试清理资源"""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="server1 (running)\n",
        )

        module = MCPStatusModule()
        module.initialize()
        assert len(module._servers) > 0

        module.cleanup()
        assert len(module._servers) == 0

    @patch("cc_statusline.modules.mcp_status.subprocess.run")
    def test_refresh(self, mock_run: MagicMock) -> None:
        """测试刷新功能"""
        # 第一次调用返回 2 个服务器
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="server1 (running)\nserver2 (running)\n",
        )

        module = MCPStatusModule()
        module.initialize()
        assert len(module._servers) == 2

        # 第二次调用返回 1 个服务器
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="server1 (running)\n",
        )

        module.refresh()
        assert len(module._servers) == 1
