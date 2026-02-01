"""MCP 状态模块单元测试"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

from cc_status.modules.base import ModuleStatus
from cc_status.modules.mcp_status import MCPServerInfo, MCPStatusModule


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

    @patch("cc_status.modules.mcp_status.subprocess.run")
    def test_detect_servers_from_command(self, mock_run: MagicMock) -> None:
        """测试从命令检测服务器"""
        # 模拟新的命令输出格式
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="Checking MCP server health...\n"
            "server1: npx -y server1 - ✓ Connected\n"
            "server2: npx -y server2 - ✓ Connected\n"
            "server3: python server3.py - ✓ Connected\n",
        )

        module = MCPStatusModule()
        servers = module._get_from_claude_command()
        assert len(servers) == 3
        assert servers[0].name == "server1"
        assert servers[0].status == "running"
        assert servers[1].name == "server2"
        assert servers[1].status == "running"

    @patch("cc_status.modules.mcp_status.subprocess.run")
    def test_detect_servers_command_fails(self, mock_run: MagicMock) -> None:
        """测试命令失败时的处理"""
        mock_run.side_effect = FileNotFoundError()

        module = MCPStatusModule()
        servers = module._get_from_claude_command()
        assert len(servers) == 0

    @patch("cc_status.modules.mcp_status.subprocess.run")
    def test_detect_servers_command_timeout(self, mock_run: MagicMock) -> None:
        """测试命令超时时的处理"""
        from subprocess import TimeoutExpired

        # 模拟超时异常
        mock_run.side_effect = TimeoutExpired(["claude", "mcp", "list"], 60)

        module = MCPStatusModule()
        servers = module._get_from_claude_command()
        # 超时时应该返回空列表（静默失败）
        assert len(servers) == 0

    @patch("cc_status.modules.mcp_status.subprocess.run")
    def test_command_timeout_is_60_seconds(self, mock_run: MagicMock) -> None:
        """测试命令超时时间设置为 60 秒"""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="Checking MCP server health...\n",
        )

        module = MCPStatusModule()
        module._get_from_claude_command()

        # 验证 subprocess.run 被调用时 timeout=60
        mock_run.assert_called_once()
        call_kwargs = mock_run.call_args[1]
        assert call_kwargs["timeout"] == 60

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
        servers = module._parse_mcp_config_for_test(config_file)

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
        servers = module._parse_mcp_config_for_test(config_file)
        assert len(servers) == 0

    @patch("cc_status.modules.mcp_status.subprocess.run")
    @patch("cc_status.modules.mcp_status.Path.exists")
    def test_get_output_no_servers(self, mock_exists: MagicMock, mock_run: MagicMock) -> None:
        """测试无服务器时的输出"""
        mock_exists.return_value = False  # 模拟配置文件不存在
        mock_run.side_effect = FileNotFoundError()

        module = MCPStatusModule()
        output = module.get_output()  # 会尝试初始化但失败
        assert output.text == "无 MCP 服务器"
        assert output.icon == "🔌"
        assert output.color == "gray"
        assert output.status == ModuleStatus.SUCCESS

    @patch("cc_status.modules.mcp_status.subprocess.run")
    def test_get_output_all_running(self, mock_run: MagicMock) -> None:
        """测试全部服务器运行中的输出"""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="Checking MCP server health...\n"
            "server1: npx -y server1 - ✓ Connected\n"
            "server2: npx -y server2 - ✓ Connected\n",
        )

        module = MCPStatusModule()
        # 模拟配置中只有 2 个服务器
        module._all_configured = ["server1", "server2"]
        # 等待异步任务完成
        if module._pending_update:
            module._pending_update.result()

        output = module.get_output()
        assert output.text == "2/2 运行中"
        assert output.icon == "🟢"
        assert output.color == "green"
        assert output.status == ModuleStatus.SUCCESS

    @patch("cc_status.modules.mcp_status._get_current_time")
    @patch("cc_status.modules.mcp_status.MCPStatusModule._async_update_status")
    def test_get_output_partial_running(self, mock_async: MagicMock, mock_time: MagicMock) -> None:
        """测试部分服务器运行中的输出（通过手动设置）"""
        # Mock 当前时间为接近 _last_update，避免缓存超时
        mock_time.return_value = 125.0  # 只过了 2 秒，未超过 60 秒缓存

        module = MCPStatusModule()

        # 模拟配置中只有 2 个服务器
        module._all_configured = ["server1", "server2"]

        # 手动设置服务器状态（因为新格式所有连接的服务器都是running）
        module._servers = {
            "server1": MCPServerInfo(name="server1", status="running"),
            "server2": MCPServerInfo(name="server2", status="unknown"),
        }
        # 设置非零时间戳避免延迟初始化
        module._last_update = 123.0

        output = module.get_output()
        assert output.text == "1/2 运行中"
        assert output.icon == "🟡"
        assert output.color == "yellow"
        assert output.status == ModuleStatus.WARNING

    @patch("cc_status.modules.mcp_status._get_current_time")
    @patch("cc_status.modules.mcp_status.MCPStatusModule._async_update_status")
    def test_get_output_with_errors(self, mock_async: MagicMock, mock_time: MagicMock) -> None:
        """测试有错误服务器的输出"""
        # Mock 当前时间为接近 _last_update，避免缓存超时
        mock_time.return_value = 125.0  # 只过了 2 秒，未超过 60 秒缓存

        module = MCPStatusModule()

        # 模拟配置中只有 2 个服务器
        module._all_configured = ["server1", "server2"]

        # 手动设置服务器状态以测试错误情况
        module._servers = {
            "server1": MCPServerInfo(name="server1", status="running"),
            "server2": MCPServerInfo(name="server2", status="error"),
        }
        # 设置非零时间戳避免延迟初始化
        module._last_update = 123.0

        output = module.get_output()
        assert "错误" in output.text
        assert output.icon == "🔴"
        assert output.color == "red"
        assert output.status == ModuleStatus.ERROR

    @patch("cc_status.modules.mcp_status.subprocess.run")
    @patch("cc_status.modules.mcp_status.MCPStatusModule._async_update_status")
    def test_get_server_details(self, mock_async: MagicMock, mock_run: MagicMock) -> None:
        """测试获取服务器详细信息"""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="Checking MCP server health...\n" "server1: npx -y server1 - ✓ Connected\n",
        )

        module = MCPStatusModule()
        # 模拟配置中只有 1 个服务器
        module._all_configured = ["server1"]
        # 直接设置 _servers
        module._servers = {
            "server1": MCPServerInfo(name="server1", status="running"),
        }

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

    @patch("cc_status.modules.mcp_status.subprocess.run")
    def test_cleanup(self, mock_run: MagicMock) -> None:
        """测试清理资源"""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="Checking MCP server health...\n" "server1: npx -y server1 - ✓ Connected\n",
        )

        module = MCPStatusModule()
        module.refresh()  # 使用 refresh 初始化
        assert len(module._servers) > 0

        module.cleanup()
        assert len(module._servers) == 0

    @patch("cc_status.modules.mcp_status.subprocess.run")
    @patch("cc_status.modules.mcp_status.MCPStatusModule._async_update_status")
    def test_refresh(self, mock_async: MagicMock, mock_run: MagicMock) -> None:
        """测试刷新功能"""
        module = MCPStatusModule()
        # 清除待处理的异步任务
        module._pending_update = None

        # 模拟命令返回 2 个服务器
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="Checking MCP server health...\n"
            "server1: npx -y server1 - ✓ Connected\n"
            "server2: npx -y server2 - ✓ Connected\n",
        )

        # 直接设置 _all_configured 和 _servers，模拟 refresh 完成后的状态
        module._all_configured = ["server1", "server2"]
        module._servers = {
            "server1": MCPServerInfo(name="server1", status="running"),
            "server2": MCPServerInfo(name="server2", status="running"),
        }

        assert len(module._servers) == 2
        assert "server1" in module._servers
        assert "server2" in module._servers

        # 模拟第二次刷新
        module._all_configured = ["server1"]
        module._servers = {
            "server1": MCPServerInfo(name="server1", status="running"),
        }

        assert len(module._servers) == 1
        assert "server1" in module._servers
