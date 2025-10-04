# -*- coding: utf-8 -*-
"""
定时任务调度服务
负责定时执行宏观、市场和基本面分析
"""

import time
import threading
from typing import Optional, Callable
from datetime import datetime

from config import Settings


class SchedulerService:
    """定时任务调度服务"""

    def __init__(self, settings: Settings):
        """
        初始化定时任务服务

        Args:
            settings: 系统配置
        """
        self.settings = settings
        self.is_running = False
        self.scheduler_thread: Optional[threading.Thread] = None
        self.analysis_callback: Optional[Callable] = None

        print("✅ 定时任务调度服务初始化完成")

    def set_analysis_callback(self, callback: Callable):
        """
        设置分析回调函数

        Args:
            callback: 执行分析的回调函数
        """
        self.analysis_callback = callback

    def start_scheduler(self):
        """启动定时任务调度器"""
        if self.is_running:
            print("⚠️ 定时任务调度器已在运行")
            return

        self.is_running = True

        # 启动时立即执行一次基础分析
        print("🕐 启动时执行基础分析...")
        self._run_scheduled_analysis()

        # 启动后台线程监控定时任务
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.scheduler_thread.start()

        print("✅ 定时任务调度器已启动")
        print("📅 定时任务：每晚23:00、凌晨4:00执行宏观+市场+基本面分析")

    def stop_scheduler(self):
        """停止定时任务调度器"""
        self.is_running = False
        print("⏹️ 定时任务调度器已停止")

    def _scheduler_loop(self):
        """定时任务循环 - 后台线程"""
        last_23_run = None
        last_04_run = None

        while self.is_running:
            try:
                now = datetime.now()
                current_date = now.date()
                current_hour = now.hour
                current_minute = now.minute

                # 检查是否到了23:00
                if current_hour == 23 and current_minute == 0:
                    if last_23_run != current_date:
                        print(f"🕐 定时任务触发: 23:00 执行基础分析")
                        self._run_scheduled_analysis()
                        last_23_run = current_date

                # 检查是否到了04:00
                elif current_hour == 4 and current_minute == 0:
                    if last_04_run != current_date:
                        print(f"🕐 定时任务触发: 04:00 执行基础分析")
                        self._run_scheduled_analysis()
                        last_04_run = current_date

                # 每分钟检查一次
                time.sleep(60)

            except Exception as e:
                print(f"❌ 定时任务调度器异常: {e}")
                import traceback
                traceback.print_exc()
                time.sleep(60)

    def _run_scheduled_analysis(self):
        """执行定时分析 - 宏观+市场+基本面"""
        if not self.analysis_callback:
            print("⚠️ 未设置分析回调函数")
            return

        try:
            print("="*80)
            print("🌍 定时任务：执行宏观、市场、基本面分析")
            print("="*80)

            # 调用回调函数执行分析
            self.analysis_callback()

            print("="*80)
            print("✅ 定时分析任务完成")
            print("="*80)

        except Exception as e:
            print(f"❌ 定时分析任务失败: {e}")
            import traceback
            traceback.print_exc()

    def get_status(self) -> dict:
        """获取调度器状态"""
        return {
            'is_running': self.is_running,
            'has_callback': self.analysis_callback is not None,
            'schedule': ['启动时', '每晚23:00', '凌晨04:00']
        }
