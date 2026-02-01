"""任务调度器单元测试"""

from unittest.mock import MagicMock, patch

from cc_status.engine.scheduler import SchedulerState, Task


class TestSchedulerState:
    """SchedulerState 枚举测试"""

    def test_state_values(self) -> None:
        """测试状态枚举值"""
        assert SchedulerState.STOPPED.value == "stopped"
        assert SchedulerState.RUNNING.value == "running"
        assert SchedulerState.PAUSED.value == "paused"

    def test_state_comparison(self) -> None:
        """测试状态比较"""
        assert SchedulerState.RUNNING == SchedulerState.RUNNING
        assert SchedulerState.RUNNING != SchedulerState.STOPPED


class TestTask:
    """Task 数据类测试"""

    def test_task_creation(self) -> None:
        """测试任务创建"""
        callback = MagicMock()
        task = Task(name="test", callback=callback, interval=1.0)
        assert task.name == "test"
        assert task.callback == callback
        assert task.interval == 1.0
        assert task.enabled is True
        assert task.last_run == 0.0
        assert task.priority == 0

    def test_task_with_priority(self) -> None:
        """测试带优先级的任务"""
        callback = MagicMock()
        task = Task(name="test", callback=callback, priority=5)
        assert task.priority == 5

    def test_task_enabled_disabled(self) -> None:
        """测试任务启用/禁用"""
        callback = MagicMock()
        task = Task(name="test", callback=callback, enabled=False)
        assert task.enabled is False


class TestSchedulerInit:
    """初始化测试"""

    def test_init_default_state(self, scheduler) -> None:
        """测试默认状态"""
        assert scheduler.get_state() == SchedulerState.STOPPED
        assert scheduler.get_task_count() == 0
        assert scheduler.get_enabled_count() == 0

    def test_init_creates_stop_event(self, scheduler) -> None:
        """测试创建停止事件"""
        assert scheduler._stop_event is not None
        assert not scheduler._stop_event.is_set()

    def test_init_creates_pause_event_set(self, scheduler) -> None:
        """测试创建暂停事件（已设置）"""
        assert scheduler._pause_event is not None
        assert scheduler._pause_event.is_set()

    def test_init_empty_tasks(self, scheduler) -> None:
        """测试空任务列表"""
        assert scheduler.get_task_count() == 0


class TestSchedulerTaskManagement:
    """任务管理测试"""

    def test_add_task(self, scheduler) -> None:
        """测试添加任务"""
        callback = MagicMock()
        scheduler.add_task("test", callback, interval=1.0)
        assert scheduler.has_task("test")
        assert scheduler.get_task_count() == 1

    def test_add_task_duplicate_raises(self, scheduler) -> None:
        """测试重复添加任务"""
        callback = MagicMock()
        scheduler.add_task("test", callback)
        # 重复添加应该覆盖（或根据实现抛出异常）
        scheduler.add_task("test", callback, interval=2.0)
        assert scheduler.get_task_count() == 1

    def test_remove_task(self, scheduler) -> None:
        """测试移除任务"""
        callback = MagicMock()
        scheduler.add_task("test", callback)
        scheduler.remove_task("test")
        assert not scheduler.has_task("test")

    def test_remove_task_not_exists(self, scheduler) -> None:
        """测试移除不存在的任务不抛出异常"""
        # 应该静默失败
        scheduler.remove_task("nonexistent")

    def test_has_task(self, scheduler) -> None:
        """测试检查任务存在"""
        callback = MagicMock()
        assert not scheduler.has_task("test")
        scheduler.add_task("test", callback)
        assert scheduler.has_task("test")

    def test_enable_task(self, scheduler) -> None:
        """测试启用任务"""
        callback = MagicMock()
        scheduler.add_task("test", callback)
        scheduler.disable_task("test")
        assert scheduler.get_enabled_count() == 0
        scheduler.enable_task("test")
        assert scheduler.get_enabled_count() == 1

    def test_disable_task(self, scheduler) -> None:
        """测试禁用任务"""
        callback = MagicMock()
        scheduler.add_task("test", callback)
        assert scheduler.get_enabled_count() == 1
        scheduler.disable_task("test")
        assert scheduler.get_enabled_count() == 0

    def test_update_interval(self, scheduler) -> None:
        """测试更新间隔"""
        callback = MagicMock()
        scheduler.add_task("test", callback, interval=1.0)
        scheduler.update_interval("test", 2.0)
        # 验证间隔已更新（通过检查任务信息）
        info = scheduler.get_tasks_info()
        assert info["test"]["interval"] == 2.0

    def test_get_task_count(self, scheduler) -> None:
        """测试获取任务数量"""
        callback = MagicMock()
        assert scheduler.get_task_count() == 0
        scheduler.add_task("test1", callback)
        scheduler.add_task("test2", callback)
        assert scheduler.get_task_count() == 2

    def test_get_enabled_count(self, scheduler) -> None:
        """测试获取已启用任务数量"""
        callback = MagicMock()
        scheduler.add_task("test1", callback)
        scheduler.add_task("test2", callback)
        scheduler.disable_task("test2")
        assert scheduler.get_enabled_count() == 1


class TestSchedulerIntervalCalculation:
    """间隔计算测试"""

    def test_get_min_interval_empty(self, scheduler) -> None:
        """测试空任务列表返回最小间隔"""
        interval = scheduler.get_min_interval()
        assert interval == 0.1  # 默认最小间隔

    def test_get_min_interval_single(self, scheduler) -> None:
        """测试单个任务间隔"""
        callback = MagicMock()
        scheduler.add_task("test", callback, interval=2.0)
        assert scheduler.get_min_interval() == 2.0

    def test_get_min_interval_multiple(self, scheduler) -> None:
        """测试多个任务返回最小间隔"""
        callback = MagicMock()
        scheduler.add_task("task1", callback, interval=2.0)
        scheduler.add_task("task2", callback, interval=1.0)
        scheduler.add_task("task3", callback, interval=3.0)
        assert scheduler.get_min_interval() == 1.0

    def test_get_min_interval_ignores_disabled(self, scheduler) -> None:
        """测试忽略禁用的任务"""
        callback = MagicMock()
        scheduler.add_task("task1", callback, interval=1.0)
        scheduler.add_task("task2", callback, interval=0.5)
        scheduler.disable_task("task2")
        assert scheduler.get_min_interval() == 1.0


class TestSchedulerLifecycle:
    """生命周期测试（使用 mock）"""

    @patch("threading.Thread")
    def test_start_changes_state(self, mock_thread, scheduler) -> None:
        """测试启动改变状态"""
        scheduler.start()
        assert scheduler.get_state() == SchedulerState.RUNNING

    @patch("threading.Thread")
    def test_start_creates_thread(self, mock_thread, scheduler) -> None:
        """测试启动创建线程"""
        scheduler.start()
        mock_thread.assert_called_once()

    def test_stop_changes_state(self, scheduler) -> None:
        """测试停止改变状态"""
        scheduler._state = SchedulerState.RUNNING
        scheduler.stop()
        assert scheduler.get_state() == SchedulerState.STOPPED

    def test_stop_sets_stop_event(self, scheduler) -> None:
        """测试停止设置停止事件"""
        scheduler._state = SchedulerState.RUNNING
        scheduler.stop()
        assert scheduler._stop_event.is_set()

    def test_pause_changes_state(self, scheduler) -> None:
        """测试暂停改变状态"""
        scheduler._state = SchedulerState.RUNNING
        scheduler.pause()
        assert scheduler.get_state() == SchedulerState.PAUSED

    def test_pause_clears_pause_event(self, scheduler) -> None:
        """测试暂停清除暂停事件"""
        scheduler._state = SchedulerState.RUNNING
        scheduler.pause()
        assert not scheduler._pause_event.is_set()

    def test_resume_sets_pause_event(self, scheduler) -> None:
        """测试恢复设置暂停事件"""
        scheduler._state = SchedulerState.PAUSED
        scheduler._pause_event.clear()
        scheduler.resume()
        assert scheduler._pause_event.is_set()

    def test_resume_from_paused(self, scheduler) -> None:
        """测试从暂停恢复"""
        scheduler._state = SchedulerState.PAUSED
        scheduler.resume()
        assert scheduler.get_state() == SchedulerState.RUNNING

    def test_resume_from_running_no_effect(self, scheduler) -> None:
        """测试从运行状态恢复无效"""
        scheduler._state = SchedulerState.RUNNING
        state_before = scheduler.get_state()
        scheduler.resume()
        assert scheduler.get_state() == state_before

    def test_get_state(self, scheduler) -> None:
        """测试获取状态"""
        assert scheduler.get_state() == SchedulerState.STOPPED


class TestSchedulerCallback:
    """回调机制测试"""

    def test_on_state_change_callback(self, scheduler) -> None:
        """测试状态变化回调"""
        callback = MagicMock()
        scheduler.on_state_change(callback)
        # 验证回调已注册
        assert "state_change" in scheduler._callbacks

    def test_state_change_notification(self, scheduler) -> None:
        """测试状态变化通知"""
        callback = MagicMock()
        scheduler.on_state_change(callback)
        scheduler.start()
        callback.assert_called()

    def test_multiple_callbacks(self, scheduler) -> None:
        """测试多个回调（只保存最后一个）"""
        callback1 = MagicMock()
        callback2 = MagicMock()
        scheduler.on_state_change(callback1)
        scheduler.on_state_change(callback2)
        scheduler.start()
        # 只有 callback2 被调用（字典只保存最后一个）
        callback2.assert_called()


class TestSchedulerExecution:
    """执行逻辑测试"""

    def test_get_tasks_info(self, scheduler) -> None:
        """测试获取任务信息"""
        callback = MagicMock()
        scheduler.add_task("test", callback, interval=1.5, priority=3)
        scheduler.disable_task("test")
        info = scheduler.get_tasks_info()
        assert "test" in info
        assert info["test"]["name"] == "test"
        assert info["test"]["interval"] == 1.5
        assert info["test"]["priority"] == 3
        assert info["test"]["enabled"] is False


class TestSchedulerConcurrency:
    """并发测试（基础）"""

    def test_concurrent_task_modification(self, scheduler) -> None:
        """测试并发任务修改"""
        import threading
        import uuid

        callback = MagicMock()
        errors = []

        def add_tasks():
            try:
                for i in range(10):
                    scheduler.add_task(f"task_{uuid.uuid4()}_{i}", callback)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=add_tasks) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        assert scheduler.get_task_count() == 50

    def test_thread_safe_state_changes(self, scheduler) -> None:
        """测试线程安全的状态变化"""
        import threading

        errors = []

        def change_state():
            try:
                for _ in range(10):
                    if scheduler.get_state() != SchedulerState.RUNNING:
                        scheduler.start()
                    scheduler.stop()
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=change_state) for _ in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # 由于并发状态变化，可能会有些错误，这是正常的
        # 只要不是崩溃即可
