"""任务调度器。

提供定时任务调度功能，支持刷新间隔管理。
"""

import threading
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Optional


class SchedulerState(Enum):
    """调度器状态枚举。"""

    STOPPED = "stopped"
    RUNNING = "running"
    PAUSED = "paused"


@dataclass
class Task:
    """任务定义。"""

    name: str
    callback: Callable[[], None]
    interval: float = 1.0  # 刷新间隔（秒）
    last_run: float = 0.0
    enabled: bool = True
    priority: int = 0  # 优先级，数值越小优先级越高


class Scheduler:
    """任务调度器。

    管理多个任务的定时执行。
    """

    def __init__(self) -> None:
        self._tasks: dict[str, Task] = {}
        self._state = SchedulerState.STOPPED
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._pause_event = threading.Event()
        self._pause_event.set()  # 非暂停状态
        self._lock = threading.Lock()
        self._callbacks: dict[str, Callable[[str], None]] = {}  # 状态变化回调
        self._min_interval: float = 0.1  # 最小间隔 100ms

    def add_task(
        self,
        name: str,
        callback: Callable[[], None],
        interval: float = 1.0,
        priority: int = 0,
    ) -> None:
        """添加任务。

        Args:
            name: 任务名称
            callback: 回调函数
            interval: 刷新间隔（秒）
            priority: 优先级
        """
        with self._lock:
            self._tasks[name] = Task(
                name=name,
                callback=callback,
                interval=max(interval, self._min_interval),
                priority=priority,
            )

    def remove_task(self, name: str) -> None:
        """移除任务。

        Args:
            name: 任务名称
        """
        with self._lock:
            self._tasks.pop(name, None)

    def has_task(self, name: str) -> bool:
        """检查任务是否存在。

        Args:
            name: 任务名称

        Returns:
            是否存在
        """
        return name in self._tasks

    def enable_task(self, name: str) -> None:
        """启用任务。

        Args:
            name: 任务名称
        """
        with self._lock:
            if name in self._tasks:
                self._tasks[name].enabled = True

    def disable_task(self, name: str) -> None:
        """禁用任务。

        Args:
            name: 任务名称
        """
        with self._lock:
            if name in self._tasks:
                self._tasks[name].enabled = False

    def update_interval(self, name: str, interval: float) -> None:
        """更新任务间隔。

        Args:
            name: 任务名称
            interval: 新间隔
        """
        with self._lock:
            if name in self._tasks:
                self._tasks[name].interval = max(interval, self._min_interval)

    def get_min_interval(self) -> float:
        """获取最小任务间隔。

        Returns:
            最小间隔
        """
        if not self._tasks:
            return self._min_interval

        enabled_tasks = [t for t in self._tasks.values() if t.enabled]
        if not enabled_tasks:
            return self._min_interval

        return min(t.interval for t in enabled_tasks)

    def on_state_change(self, callback: Callable[[str], None]) -> None:
        """注册状态变化回调。

        Args:
            callback: 回调函数，接收新状态
        """
        self._callbacks["state_change"] = callback

    def _notify_state_change(self, state: str) -> None:
        """通知状态变化。

        Args:
            state: 新状态
        """
        callback = self._callbacks.get("state_change")
        if callback:
            try:
                callback(state)
            except Exception:
                pass

    def start(self) -> None:
        """启动调度器。"""
        if self._state == SchedulerState.RUNNING:
            return

        self._stop_event.clear()
        self._pause_event.set()
        self._state = SchedulerState.RUNNING
        self._notify_state_change(self._state.value)

        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """停止调度器。"""
        if self._state == SchedulerState.STOPPED:
            return

        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=2.0)

        self._state = SchedulerState.STOPPED
        self._notify_state_change(self._state.value)

    def pause(self) -> None:
        """暂停调度器。"""
        if self._state == SchedulerState.RUNNING:
            self._pause_event.clear()
            self._state = SchedulerState.PAUSED
            self._notify_state_change(self._state.value)

    def resume(self) -> None:
        """恢复调度器。"""
        if self._state == SchedulerState.PAUSED:
            self._pause_event.set()
            self._state = SchedulerState.RUNNING
            self._notify_state_change(self._state.value)

    def _run_loop(self) -> None:
        """运行主循环。"""
        while not self._stop_event.is_set():
            # 检查暂停状态
            self._pause_event.wait()

            current_time = time.time()

            with self._lock:
                tasks_to_run = [
                    t
                    for t in self._tasks.values()
                    if t.enabled and (current_time - t.last_run) >= t.interval
                ]

            # 按优先级排序
            tasks_to_run.sort(key=lambda t: t.priority)

            # 执行任务
            for task in tasks_to_run:
                if self._stop_event.is_set() or not self._pause_event.is_set():
                    break

                try:
                    task.callback()
                except Exception:
                    pass

                task.last_run = time.time()

            # 短暂休眠
            time.sleep(self._min_interval)

    def get_state(self) -> SchedulerState:
        """获取调度器状态。

        Returns:
            当前状态
        """
        return self._state

    def get_task_count(self) -> int:
        """获取任务数量。

        Returns:
            任务数量
        """
        return len(self._tasks)

    def get_enabled_count(self) -> int:
        """获取已启用任务数量。

        Returns:
            已启用任务数量
        """
        return sum(1 for t in self._tasks.values() if t.enabled)

    def get_tasks_info(self) -> dict[str, dict[str, Any]]:
        """获取所有任务信息。

        Returns:
            任务信息字典
        """
        return {
            name: {
                "name": task.name,
                "interval": task.interval,
                "enabled": task.enabled,
                "priority": task.priority,
                "last_run": task.last_run,
            }
            for name, task in self._tasks.items()
        }


# 全局调度器实例
scheduler = Scheduler()
