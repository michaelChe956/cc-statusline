"""Claude Code 配置安装器

自动配置 ~/.claude/settings.json 以启用 cc-statusline 状态栏
"""

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import yaml


class ClaudeConfigInstaller:
    """Claude Code 配置安装器"""

    CONFIG_PATH = Path.home() / ".claude" / "settings.json"

    @classmethod
    def install(
        cls,
        force: bool = False,
        theme: str = "default",
        interval: int = 10000,
    ) -> bool:
        """安装状态栏配置到 Claude Code

        Args:
            force: 是否强制覆盖现有配置
            theme: 主题名称
            interval: 刷新间隔（毫秒）

        Returns:
            是否安装成功
        """
        # 检测最佳命令路径
        command = cls.detect_command()
        if not command:
            print("❌ 错误: 无法检测到 cc-statusline 命令")
            print("请确保已安装 cc-statusline:")
            print("  pip install cc-statusline")
            print("  或")
            print("  uvx cc-statusline install")
            return False

        # 读取现有配置
        config = cls._read_config()

        # 检查是否已配置
        if not force and "statusLine" in config:
            print("⚠️  状态栏配置已存在")
            print(f"当前配置: {json.dumps(config['statusLine'], indent=2)}")
            print("使用 --force 强制覆盖")
            return False

        # 备份原配置
        if cls.CONFIG_PATH.exists():
            backup_path = cls.backup_config()
            print(f"✅ 已备份原配置: {backup_path}")

        # 构建状态栏配置
        statusline_config = {
            "type": "command",
            "command": f"{command} --once --theme {theme}",
            "refreshInterval": interval,
            "padding": 0,
        }

        # 合并配置
        config["statusLine"] = statusline_config

        # 写入配置
        cls._write_config(config)
        print("✅ 状态栏配置已安装")
        print(f"命令: {command}")
        print(f"主题: {theme}")
        print(f"刷新间隔: {interval}ms")
        print("\n重启 Claude Code 以应用更改")

        return True

    @classmethod
    def uninstall(cls) -> bool:
        """移除状态栏配置

        Returns:
            是否卸载成功
        """
        if not cls.CONFIG_PATH.exists():
            print("⚠️  配置文件不存在")
            return False

        # 读取配置
        config = cls._read_config()

        # 检查是否有状态栏配置
        if "statusLine" not in config:
            print("⚠️  未找到状态栏配置")
            return False

        # 备份原配置
        backup_path = cls.backup_config()
        print(f"✅ 已备份原配置: {backup_path}")

        # 移除状态栏配置
        del config["statusLine"]

        # 写入配置
        cls._write_config(config)
        print("✅ 状态栏配置已移除")
        print("\n重启 Claude Code 以应用更改")

        return True

    @classmethod
    def verify(cls, verbose: bool = False, test_command: bool = False) -> bool:  # noqa: C901
        """验证状态栏配置是否正确（增强版本）

        Args:
            verbose: 是否显示详细验证信息
            test_command: 是否测试命令执行

        Returns:
            配置是否有效
        """
        if verbose:
            print("🔍 开始验证 cc-statusline 配置...")
            print("━" * 50)

        # 1. 配置文件存在性检查
        if not cls.CONFIG_PATH.exists():
            print(f"❌ 配置文件不存在: {cls.CONFIG_PATH}")
            return False

        if verbose:
            print(f"✅ 配置文件存在: {cls.CONFIG_PATH}")

        # 2. JSON 格式有效性
        try:
            config = cls._read_config()
        except json.JSONDecodeError as e:
            print(f"❌ 配置文件 JSON 格式错误: {e}")
            return False

        if verbose:
            print("✅ 配置格式有效: JSON 解析成功")

        # 3. 状态栏配置存在性
        if "statusLine" not in config:
            print("❌ 未找到状态栏配置 (statusLine)")
            return False

        if verbose:
            print("✅ 状态栏配置存在")

        statusline = config["statusLine"]

        # 4. 必需字段检查
        required_fields = ["type", "command"]
        missing = [f for f in required_fields if f not in statusline]
        if missing:
            print(f"❌ 缺少必需字段: {', '.join(missing)}")
            return False

        if verbose:
            print("✅ 必需字段完整: type, command")

        # 5. 类型字段验证
        if statusline["type"] != "command":
            print(f"❌ type 字段必须是 'command', 实际: {statusline['type']}")
            return False

        if verbose:
            print("✅ type 字段正确: command")

        # 6. 命令路径有效性
        command = statusline["command"]
        if "cc-statusline" not in command:
            print(f"⚠️  命令可能不正确: {command}")
            if not verbose:
                return False

        if verbose:
            print(f"✅ 命令路径有效: {command}")

        # 7. 命令执行测试 (可选)
        if test_command:
            if cls.test_command(command):
                if verbose:
                    print("✅ 命令执行测试通过")
            else:
                print("❌ 命令执行测试失败")
                return False

        if verbose:
            print("━" * 50)

        print("✅ 状态栏配置验证通过")
        if not verbose:
            print(json.dumps(statusline, indent=2, ensure_ascii=False))

        return True

    @classmethod
    def health_check(cls) -> dict[str, Any]:
        """完整的健康检查报告

        Returns:
            健康检查结果字典
        """
        report: dict[str, Any] = {
            "config_exists": False,
            "config_valid": False,
            "statusline_exists": False,
            "command_found": False,
            "command_executable": False,
            "version": None,
            "details": {},
        }

        # 1. 配置文件存在性
        report["config_exists"] = cls.CONFIG_PATH.exists()
        report["details"]["config_path"] = str(cls.CONFIG_PATH)

        if not report["config_exists"]:
            return report

        # 2. JSON 格式有效性
        try:
            config = cls._read_config()
            report["config_valid"] = True
        except json.JSONDecodeError as e:
            report["details"]["parse_error"] = str(e)
            return report

        # 3. 状态栏配置存在性
        report["statusline_exists"] = "statusLine" in config
        if report["statusline_exists"]:
            report["details"]["statusline_config"] = config["statusLine"]

            # 4. 命令路径有效性
            command = config["statusLine"].get("command", "")
            report["details"]["command"] = command
            report["command_found"] = "cc-statusline" in command

            # 5. 命令可执行性测试
            if report["command_found"]:
                report["command_executable"] = cls.test_command(command)

                # 6. 版本信息
                if report["command_executable"]:
                    from cc_status import __version__

                    report["version"] = __version__

        return report

    @classmethod
    def test_command(cls, command: Optional[str] = None) -> bool:
        """测试状态栏命令能否正常执行

        Args:
            command: 要测试的命令，如果为 None 则从配置中读取

        Returns:
            命令是否可执行
        """
        import subprocess

        if command is None:
            config = cls._read_config()
            if "statusLine" not in config:
                return False
            command = config["statusLine"].get("command", "")

        if not command:
            return False

        # 提取基础命令 (去除参数)
        base_cmd = command.split()[0:2]  # 例如: ["uvx", "cc-statusline"]

        try:
            result = subprocess.run(
                [*base_cmd, "--version"],
                capture_output=True,
                timeout=5,
                text=True,
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    @classmethod
    def detect_command(cls) -> Optional[str]:
        """检测可用的 cc-statusline 命令路径

        优先级:
        1. uvx cc-statusline (推荐)
        2. 全局安装的 cc-statusline
        3. 本地虚拟环境中的 python -m cc_status

        Returns:
            可用的命令字符串，如果未找到则返回 None
        """
        import subprocess

        # 1. 尝试 uvx
        try:
            result = subprocess.run(
                ["uvx", "--version"],
                capture_output=True,
                timeout=2,
            )
            if result.returncode == 0:
                # 验证 uvx cc-statusline 可用
                result = subprocess.run(
                    ["uvx", "cc-statusline", "--version"],
                    capture_output=True,
                    timeout=5,
                )
                if result.returncode == 0:
                    return "uvx cc-statusline"
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

        # 2. 尝试全局安装
        try:
            result = subprocess.run(
                ["cc-statusline", "--version"],
                capture_output=True,
                timeout=2,
            )
            if result.returncode == 0:
                return "cc-statusline"
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

        # 3. 尝试 python -m
        try:
            result = subprocess.run(
                ["python", "-m", "cc_status", "--version"],
                capture_output=True,
                timeout=2,
            )
            if result.returncode == 0:
                return "python -m cc_status"
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

        return None

    @classmethod
    def backup_config(cls) -> Path:
        """备份当前配置文件

        Returns:
            备份文件路径
        """
        if not cls.CONFIG_PATH.exists():
            raise FileNotFoundError(f"配置文件不存在: {cls.CONFIG_PATH}")

        # 生成备份文件名: settings.json.backup.YYYYMMDD_HHMMSS
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = cls.CONFIG_PATH.with_suffix(f".json.backup.{timestamp}")

        # 复制文件
        shutil.copy2(cls.CONFIG_PATH, backup_path)

        return backup_path

    @classmethod
    def _read_config(cls) -> dict[str, Any]:
        """读取配置文件

        Returns:
            配置字典
        """
        if not cls.CONFIG_PATH.exists():
            # 配置文件不存在，创建空配置
            cls.CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
            return {}

        try:
            with open(cls.CONFIG_PATH, encoding="utf-8") as f:
                result: dict[str, Any] = json.load(f)
                return result
        except json.JSONDecodeError:
            print(f"⚠️  配置文件格式错误: {cls.CONFIG_PATH}")
            return {}

    @classmethod
    def _write_config(cls, config: dict[str, Any]) -> None:
        """写入配置文件

        Args:
            config: 配置字典
        """
        cls.CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)

        with open(cls.CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
            f.write("\n")  # 末尾换行符

    @classmethod
    def export_config(cls, path: Path, include_metadata: bool = True) -> bool:
        """导出 statusLine 配置到文件

        Args:
            path: 导出文件路径
            include_metadata: 是否包含元数据

        Returns:
            是否导出成功
        """
        if not cls.CONFIG_PATH.exists():
            print("❌ 配置文件不存在")
            return False

        config = cls._read_config()

        if "statusLine" not in config:
            print("❌ 未找到状态栏配置")
            return False

        # 构建导出数据
        export_data: dict[str, Any] = {}

        if include_metadata:
            from cc_status import __version__

            export_data = {
                "version": __version__,
                "exported_at": datetime.now().isoformat(),
                "statusLine": config["statusLine"],
            }
        else:
            export_data = {"statusLine": config["statusLine"]}

        # 写入文件 (YAML 格式)
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(path, "w", encoding="utf-8") as f:
                yaml.dump(export_data, f, allow_unicode=True, default_flow_style=False)

            print(f"✅ 配置已导出: {path}")
            return True
        except Exception as e:
            print(f"❌ 导出失败: {e}")
            return False

    @classmethod
    def import_config(cls, path: Path, force: bool = False) -> bool:
        """从文件导入 statusLine 配置

        Args:
            path: 导入文件路径
            force: 是否强制覆盖现有配置

        Returns:
            是否导入成功
        """
        path = Path(path)

        if not path.exists():
            print(f"❌ 文件不存在: {path}")
            return False

        # 读取导入文件
        try:
            with open(path, encoding="utf-8") as f:
                import_data = yaml.safe_load(f)
        except Exception as e:
            print(f"❌ 读取文件失败: {e}")
            return False

        # 验证数据
        if not isinstance(import_data, dict):
            print("❌ 配置文件格式错误")
            return False

        if "statusLine" not in import_data:
            print("❌ 配置文件中未找到 statusLine 配置")
            return False

        # 读取现有配置
        config = cls._read_config()

        # 检查是否已配置
        if not force and "statusLine" in config:
            print("⚠️  状态栏配置已存在")
            print(f"当前配置: {json.dumps(config['statusLine'], indent=2)}")
            print("使用 --force 强制覆盖")
            return False

        # 备份原配置
        if cls.CONFIG_PATH.exists():
            backup_path = cls.backup_config()
            print(f"✅ 已备份原配置: {backup_path}")

        # 合并配置
        config["statusLine"] = import_data["statusLine"]

        # 写入配置
        cls._write_config(config)

        print("✅ 配置已导入")
        print(json.dumps(config["statusLine"], indent=2, ensure_ascii=False))
        print("\n重启 Claude Code 以应用更改")

        return True

    @classmethod
    def get_config_version(cls) -> Optional[str]:
        """获取当前配置版本

        Returns:
            配置版本字符串，如果未配置则返回 None
        """
        from cc_status import __version__

        if not cls.CONFIG_PATH.exists():
            return None

        config = cls._read_config()

        if "statusLine" not in config:
            return None

        # 返回当前包版本
        return __version__
