# -*- coding: utf-8 -*-
"""
Telegram机器人集成 - 加密货币监控系统远程控制
"""

import asyncio
import json
import re
import threading
import time
import httpx
from datetime import datetime
from typing import Optional

try:
    from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False
    print("未安装python-telegram-bot库，请运行: pip install python-telegram-bot")
    # 定义空的类型避免NameError
    class Update: pass
    class ContextTypes:
        DEFAULT_TYPE = None
    class InlineKeyboardMarkup: pass
    class InlineKeyboardButton: pass

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from crypto_monitor_controller import CryptoMonitorController

# Telegram bot类型标识
CRYPTO_BOT_TYPE = 'crypto_monitor_project'

class CryptoTelegramBot:
    def __init__(self, token: str, chat_id: str, crypto_monitor):
        if not TELEGRAM_AVAILABLE:
            raise ImportError("需要安装python-telegram-bot库")
            
        self.token = token
        self.chat_id = chat_id
        self.crypto_monitor = crypto_monitor
        self.application = None
        self.running = False
        
        # 支持的角色列表
        self.supported_roles = {
            '技术分析师': 'technical_analysis',
            '市场分析师': 'market_sentiment', 
            '基本面分析师': 'fundamental_analysis',
            '宏观分析师': 'macro_analysis',
            '首席分析师': 'coin_chief_analysis',
            '研究部门总监': 'research_summary',
            '永续交易员': 'trader_decision'
        }
        
        # 动态币种列表 - 初始为空，从controller的symbol_monitors和配置中动态获取
        self.supported_symbols = self._get_monitored_symbols()
        
        # 交易确认状态管理
        self.pending_trades = {}  # 存储待确认的交易
        
        # 事件循环管理
        self.main_loop = None

    def _get_monitored_symbols(self):
        """动态获取正在监控的币种列表"""
        monitored = []

        if hasattr(self.crypto_monitor, 'symbol_monitors'):
            monitored.extend(list(self.crypto_monitor.symbol_monitors.keys()))

        if hasattr(self.crypto_monitor, 'settings') and hasattr(self.crypto_monitor.settings, 'monitor'):
            primary_symbols = getattr(self.crypto_monitor.settings.monitor, 'primary_symbols', []) or []
            secondary_symbols = getattr(self.crypto_monitor.settings.monitor, 'secondary_symbols', []) or []
            monitored.extend(primary_symbols)
            monitored.extend(secondary_symbols)

        return list(set(monitored))

    def _schedule_async_task(self, coro):
        """安全地调度异步任务到主事件循环"""
        try:
            if self.main_loop and not self.main_loop.is_closed():
                try:
                    asyncio.run_coroutine_threadsafe(coro, self.main_loop)
                except RuntimeError as e:
                    print(f"⚠️ 异步任务调度RuntimeError: {e}")
                    # 如果主循环有问题，尝试创建新的任务
                    try:
                        asyncio.create_task(coro) if asyncio.get_running_loop() else None
                    except:
                        print("❌ 无法创建异步任务")
                except Exception as e:
                    print(f"❌ 异步任务调度失败: {e}")
            else:
                # 如果没有主循环，尝试在新的事件循环中运行
                try:
                    # 检查是否已经在事件循环中
                    try:
                        current_loop = asyncio.get_running_loop()
                        # 如果在循环中，创建任务
                        asyncio.create_task(coro)
                        return
                    except RuntimeError:
                        # 不在循环中，创建新循环
                        pass

                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        loop.run_until_complete(coro)
                    finally:
                        loop.close()
                        asyncio.set_event_loop(None)
                except Exception as e:
                    print(f"❌ 异步任务执行失败: {e}")
        except Exception as e:
            print(f"❌ 异步任务调度发生严重错误: {e}")
            import traceback
            traceback.print_exc()
        
    def _create_main_menu(self):
        """创建主菜单键盘"""
        keyboard = [
            [
                InlineKeyboardButton("💰 账户状态", callback_data="account_status")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)


    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """启动命令处理"""
        welcome_msg = """🤖 **加密货币监控系统**

👋 欢迎！

📊 `/analyze 币种` - 技术分析
💰 点击下方按钮查看账户状态"""

        reply_markup = self._create_main_menu()
        await update.message.reply_text(welcome_msg, parse_mode='Markdown', reply_markup=reply_markup)

    async def analyze_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """技术分析命令"""
        try:
            if len(context.args) < 1:
                await update.message.reply_text(
                    "❌ 格式错误！\n正确格式：`/analyze 币种`\n例：`/analyze BTC`",
                    parse_mode='Markdown'
                )
                return

            symbol_input = context.args[0].upper()
            symbol = f"{symbol_input}USDT" if not symbol_input.endswith('USDT') else symbol_input

            await update.message.reply_text(f"🔍 正在分析 {symbol_input}...")

            # 执行技术分析
            try:
                analysis_result = self.crypto_monitor.analysis_service.analyze_technical(symbol)

                if analysis_result:
                    # 创建带监控按钮的键盘
                    keyboard = [
                        [
                            InlineKeyboardButton("🔔 开始监控", callback_data=f"monitor_start_{symbol}"),
                            InlineKeyboardButton("⏹️ 停止监控", callback_data=f"monitor_stop_{symbol}")
                        ]
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)

                    await self._send_long_message(update, f"📊 **{symbol_input} 技术分析**\n\n{analysis_result}", reply_markup)
                else:
                    await update.message.reply_text(f"❌ 无法获取 {symbol_input} 分析")

            except Exception as e:
                await update.message.reply_text(f"❌ 分析失败: {e}")

        except Exception as e:
            await update.message.reply_text(f"❌ 处理分析请求失败: {e}")


    async def _send_long_message(self, update: Update, message: str, reply_markup=None):
        """分段发送长消息"""
        max_length = 4000  # Telegram消息长度限制

        if len(message) <= max_length:
            await update.message.reply_text(message, parse_mode='Markdown', reply_markup=reply_markup)
        else:
            # 分段发送
            parts = []
            current_part = ""

            for line in message.split('\n'):
                if len(current_part + line + '\n') > max_length:
                    if current_part:
                        parts.append(current_part.strip())
                    current_part = line + '\n'
                else:
                    current_part += line + '\n'

            if current_part:
                parts.append(current_part.strip())

            for i, part in enumerate(parts):
                if i == 0:
                    await update.message.reply_text(part, parse_mode='Markdown', reply_markup=reply_markup if i == len(parts) - 1 else None)
                else:
                    await update.message.reply_text(f"📄 **续：** {part}", parse_mode='Markdown', reply_markup=reply_markup if i == len(parts) - 1 else None)
                await asyncio.sleep(1)  # 避免发送过快

    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理按钮点击"""
        query = update.callback_query
        await query.answer()

        data = query.data

        if data == "main_menu":
            await query.edit_message_text(
                """🤖 **加密货币监控系统**

👋 欢迎！

📊 `/analyze 币种` - 技术分析
💰 点击下方按钮查看账户状态""",
                parse_mode='Markdown',
                reply_markup=self._create_main_menu()
            )

        elif data == "account_status":
            await self._handle_account_status(query)

        elif data.startswith("monitor_start_"):
            symbol = data.replace("monitor_start_", "")
            await self._handle_monitor_start(query, symbol)

        elif data.startswith("monitor_stop_"):
            symbol = data.replace("monitor_stop_", "")
            await self._handle_monitor_stop(query, symbol)

    async def _handle_account_status(self, query):
        """处理账户状态按钮"""
        try:
            # 获取账户余额和持仓
            balance = self.crypto_monitor.get_account_balance()
            positions = self.crypto_monitor.get_current_positions()

            status_msg = f"""💰 **账户状态**
⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

"""
            # 显示余额
            if balance and 'error' not in balance and balance.get('success'):
                status_msg += f"总额 `${balance.get('total_wallet_balance', 0):.2f}` | 可用 `${balance.get('available_balance', 0):.2f}` | 盈亏 `${balance.get('total_unrealized_profit', 0):.2f}`\n\n"
            else:
                status_msg += f"❌ 余额获取失败\n\n"

            # 显示持仓 - 表格形式
            if positions and 'error' not in positions and positions.get('success') and positions.get('positions'):
                status_msg += "```\n"
                status_msg += "币种      价值     开仓价      盈亏\n"
                status_msg += "-----------------------------------\n"
                for pos in positions['positions']:
                    symbol = pos['symbol'].replace('USDT', '')[:6].ljust(6)
                    # 计算持仓价值 (数量 * 标记价格)
                    value = abs(pos['position_amt']) * pos['mark_price']
                    direction = "🟢" if pos['position_amt'] > 0 else "🔴"
                    entry_price = pos['entry_price']
                    pnl = pos['unrealized_profit']
                    pnl_sign = "+" if pnl > 0 else ""

                    status_msg += f"{direction}{symbol} ${value:6.0f} ${entry_price:7.2f} {pnl_sign}${pnl:5.2f}\n"
                status_msg += "```"
            else:
                status_msg += "无持仓"

            await query.edit_message_text(
                status_msg,
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔄 刷新", callback_data="account_status"), InlineKeyboardButton("◀️ 返回", callback_data="main_menu")]])
            )

        except Exception as e:
            await query.edit_message_text(
                f"❌ 获取账户状态失败: {e}",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ 返回", callback_data="main_menu")]])
            )

    async def _handle_monitor_start(self, query, symbol):
        """处理开始监控按钮"""
        try:
            result = self.crypto_monitor.start_symbol_monitor(symbol, interval_minutes=30)

            if result['success']:
                await query.edit_message_text(
                    f"✅ {result['message']}\n\n每30分钟自动分析并推送",
                    parse_mode='Markdown',
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⏹️ 停止监控", callback_data=f"monitor_stop_{symbol}")]])
                )
            else:
                await query.edit_message_text(
                    f"⚠️ {result['message']}",
                    parse_mode='Markdown',
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ 返回", callback_data="main_menu")]])
                )

        except Exception as e:
            await query.edit_message_text(
                f"❌ 启动监控失败: {e}",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ 返回", callback_data="main_menu")]])
            )

    async def _handle_monitor_stop(self, query, symbol):
        """处理停止监控按钮"""
        try:
            result = self.crypto_monitor.stop_symbol_monitor(symbol)

            if result['success']:
                await query.edit_message_text(
                    f"✅ {result['message']}",
                    parse_mode='Markdown',
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ 返回", callback_data="main_menu")]])
                )
            else:
                await query.edit_message_text(
                    f"⚠️ {result['message']}",
                    parse_mode='Markdown',
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ 返回", callback_data="main_menu")]])
                )

        except Exception as e:
            await query.edit_message_text(
                f"❌ 停止监控失败: {e}",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ 返回", callback_data="main_menu")]])
            )


    async def message_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理普通消息 - 支持直接消息转发给agent"""
        text = update.message.text.strip()
        user_name = update.message.from_user.first_name if update.message.from_user else "用户"
        chat_id = str(update.message.chat_id)

        print(f"Telegram received message: {text} (from: {user_name}, chat_id: {chat_id})")

        if CRYPTO_BOT_TYPE == 'crypto_monitor_project' and hasattr(self.crypto_monitor, 'process_user_message'):
            try:
                await update.message.reply_text("Processing your message...")

                response = self.crypto_monitor.process_user_message(text, chat_id=chat_id, source="telegram")

                if response:
                    await self._send_long_message(update, f"**AI Response:**\n\n{response}")
                else:
                    await update.message.reply_text("No response received, please try again")
                return

            except Exception as e:
                error_msg = f"Message processing failed: {e}"
                print(f"Telegram message processing error: {e}")
                import traceback
                traceback.print_exc()
                try:
                    await update.message.reply_text(error_msg)
                except:
                    print("Cannot send error message, possible network issue")

        if any(word in text.lower() for word in ['分析', 'analyze', '报告', 'report']):
            reply_markup = self._create_main_menu()
            try:
                await update.message.reply_text(
                    "**Quick Actions**\nClick buttons below for quick access:",
                    parse_mode='Markdown',
                    reply_markup=reply_markup
                )
            except:
                print("Failed to send quick action message")
        else:
            reply_markup = self._create_main_menu()
            try:
                await update.message.reply_text(
                    "I am crypto monitoring assistant!\n**Smart conversation mode**: Send me messages directly, I will process intelligently\n**Quick functions**: Click buttons below for quick access:",
                    reply_markup=reply_markup
                )
            except:
                print("Failed to send welcome message")

    def setup_handlers(self):
        """设置命令处理器"""
        if not self.application:
            return

        # 添加命令处理器
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("analyze", self.analyze_command))

        # 添加按钮处理器
        self.application.add_handler(CallbackQueryHandler(self.button_handler))

        # 添加消息处理器
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.message_handler))

    async def start_bot(self):
        """启动Telegram机器人 - 确保持续运行"""
        max_retries = 5
        retry_delay = 30

        try:
            if not TELEGRAM_AVAILABLE:
                print("❌ Telegram功能不可用：请安装python-telegram-bot库")
                return

            print("🤖 启动Telegram机器人...")

            # 保存主事件循环引用
            self.main_loop = asyncio.get_event_loop()

            # 创建应用，增加更长的超时时间和错误重试配置
            self.application = (Application.builder()
                               .token(self.token)
                               .read_timeout(120)
                               .write_timeout(120)
                               .connect_timeout(120)
                               .pool_timeout(120)
                               .get_updates_read_timeout(120)
                               .get_updates_write_timeout(120)
                               .get_updates_connect_timeout(120)
                               .get_updates_pool_timeout(120)
                               .build())

            # 设置处理器
            self.setup_handlers()

            # 启动机器人，修复初始化顺序
            for attempt in range(3):
                try:
                    print(f"🔄 尝试启动Telegram机器人 (第{attempt + 1}次)...")

                    # 正确的初始化顺序
                    await self.application.initialize()
                    await self.application.start()

                    # 验证bot是否正确初始化
                    bot_info = await self.application.bot.get_me()
                    print(f"✅ Bot已连接: @{bot_info.username}")
                    break

                except Exception as e:
                    print(f"❌ 启动失败 (第{attempt + 1}次): {e}")
                    if attempt < 2:
                        print("⏳ 等待15秒后重试...")
                        await asyncio.sleep(15)

                        # 清理之前的application实例
                        try:
                            if self.application:
                                await self.application.stop()
                                await self.application.shutdown()
                        except:
                            pass

                        # 重新创建application
                        self.application = (Application.builder()
                                           .token(self.token)
                                           .read_timeout(120)
                                           .write_timeout(120)
                                           .connect_timeout(120)
                                           .pool_timeout(120)
                                           .get_updates_read_timeout(120)
                                           .get_updates_write_timeout(120)
                                           .get_updates_connect_timeout(120)
                                           .get_updates_pool_timeout(120)
                                           .build())

                        # 重新设置处理器
                        self.setup_handlers()
                    else:
                        raise

            self.running = True
            print(f"✅ Telegram机器人已启动，Chat ID: {self.chat_id}")
            print("📱 智能对话模式已激活：用户可直接发送消息进行对话")

            # 发送启动通知（可选，如果网络有问题则跳过）
            try:
                welcome_text = """🚀 **加密货币监控系统已启动**

点击下方按钮查看账户状态"""

                reply_markup = self._create_main_menu()

                await self.application.bot.send_message(
                    chat_id=self.chat_id,
                    text=welcome_text,
                    parse_mode='Markdown',
                    reply_markup=reply_markup
                )
            except Exception as e:
                print(f"⚠️ 发送启动通知失败，继续运行: {e}")

            # 主运行循环 - 带有自动重连机制
            retry_count = 0
            while self.running and retry_count < max_retries:
                try:
                    print("🔄 开始轮询Telegram更新...")

                    # 确保updater已正确初始化
                    if not self.application.updater:
                        print("❌ Updater未初始化")
                        break

                    await self.application.updater.start_polling(
                        timeout=60,
                        drop_pending_updates=True
                    )
                    # 正常情况下会一直运行到这里
                    await asyncio.Future()  # 永远等待，直到被取消

                except asyncio.CancelledError:
                    print("📱 收到停止信号")
                    break

                except KeyboardInterrupt:
                    print("📱 收到停止信号")
                    break

                except Exception as e:
                    retry_count += 1
                    print(f"⚠️ 网络连接异常 (第{retry_count}次): {e}")

                    if retry_count < max_retries:
                        print(f"⏳ 等待{retry_delay}秒后重新连接...")
                        await asyncio.sleep(retry_delay)

                        # 尝试重新启动轮询
                        try:
                            if self.application.updater:
                                await self.application.updater.stop()
                            print("🔄 重新启动轮询连接...")
                        except Exception as cleanup_error:
                            print(f"⚠️ 清理轮询时出错: {cleanup_error}")
                    else:
                        print(f"❌ 达到最大重试次数({max_retries})，停止运行")
                        break

        except Exception as e:
            print(f"❌ Telegram机器人启动失败: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.running = False
            if self.application:
                try:
                    await self.application.stop()
                    await self.application.shutdown()
                    print("⏹️ Telegram机器人已关闭")
                except:
                    pass

    def stop_bot(self):
        """停止Telegram机器人"""
        self.running = False
        print("⏹️ Telegram机器人已停止")

# 在crypto_bot.py中集成的函数
def start_telegram_bot_thread(crypto_monitor, token: str, chat_id: str):
    """在独立线程中启动Telegram机器人"""
    if not TELEGRAM_AVAILABLE:
        print("❌ 无法启动Telegram机器人：缺少python-telegram-bot库")
        return None

    def run_bot():
        try:
            bot = CryptoTelegramBot(token, chat_id, crypto_monitor)
            asyncio.run(bot.start_bot())
        except Exception as e:
            print(f"❌ Telegram机器人线程异常: {e}")

    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    return bot_thread
