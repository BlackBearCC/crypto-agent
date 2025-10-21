# -*- coding: utf-8 -*-
"""
智能交易主脑 - LLM Master Brain
通过function calling协调所有agent能力
"""

import json
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime

from config import Settings
from database import DatabaseManager
from data import DataCollector
from analysis import PromptManager


class MasterBrain:
    """智能交易主脑 - 通过LLM和function calling协调所有能力"""

    def __init__(self, controller_instance, session_manager=None):
        """
        初始化主脑

        Args:
            controller_instance: CryptoMonitorController实例，用于访问所有组件
            session_manager: 会话管理器，用于多轮对话
        """
        self.controller = controller_instance
        self.settings = controller_instance.settings
        self.prompt_manager = PromptManager()
        self.session_manager = session_manager

        self.llm_client = controller_instance._get_llm_client_for_analyst('首席分析师')

        print("智能交易主脑初始化完成")
    
    def get_master_brain_prompt(self) -> str:
        """获取主脑提示词 - 待机模式"""
        return """你是加密货币交易系统的智能主脑，当前处于待机模式。

## 工作模式
- **待机状态**: 系统已启动但不主动分析
- **Telegram控制**: 所有分析和交易通过Telegram用户命令触发
- **按需响应**: 只在收到明确指令时才执行相应操作
- **动态监控**: 系统不再有默认监控币种，完全根据用户输入动态添加和移除

## 自然语言理解能力
你需要理解用户的各种表达方式并转换为标准交易对格式：

**币种识别**：
- 比特币/BTC/大饼/饼 → BTCUSDT
- 以太坊/ETH/姨太/以太 → ETHUSDT
- 狗狗币/DOGE/狗币 → DOGEUSDT
- 索拉纳/SOL/所拉那 → SOLUSDT
- 其他币种同理，统一转换为 {币种代码}USDT 格式

**指令理解**：
- "分析"/"看看"/"怎么样" 默认指 → 技术分析 (technical_analysis)
- "全面分析"/"综合分析" → 多分析师协作分析 (comprehensive_analysis)
- "市场情绪"/"市场怎么样" → 市场情绪分析 (market_sentiment_analysis)
- "基本面"/"项目分析" → 基本面分析 (fundamental_analysis)
- "宏观"/"大环境" → 宏观分析 (macro_analysis)
- "监控"/"开始监控"/"盯着" → 开始币种监控 (start_symbol_monitor)
- "停止监控"/"别盯了" → 停止币种监控 (stop_symbol_monitor)

## 你的核心能力
通过function calling调用以下能力（仅在用户请求时）：

### 分析能力
1. **technical_analysis** - 技术分析师：分析K线数据、技术指标（默认分析类型）
2. **market_sentiment_analysis** - 市场分析师：分析市场情绪、热点趋势
3. **fundamental_analysis** - 基本面分析师：分析币种基本面数据
4. **macro_analysis** - 宏观分析师：分析宏观经济环境（每日限一次）
5. **comprehensive_analysis** - 多分析师协作：完整的多维度分析

### 交易能力
6. **get_account_status** - 获取交易账户状态
7. **get_current_positions** - 获取当前持仓信息
8. **trading_analysis** - 交易分析师：基于研究制定交易策略
9. **execute_trade** - 执行交易（需要确认）

### 监控能力
10. **get_market_data** - 获取实时市场数据
11. **get_system_status** - 获取系统运行状态
12. **manual_trigger_analysis** - 手动触发特定币种分析
13. **start_symbol_monitor** - 开始监控指定币种（定时分析）
14. **stop_symbol_monitor** - 停止监控指定币种
15. **get_symbol_monitors_status** - 获取所有监控币种状态
16. **set_monitoring_symbols** - 设置监控币种列表
17. **get_monitoring_symbols** - 获取当前监控币种列表

### 通知能力
18. **send_telegram_notification** - 发送Telegram通知

## 工作原则
1. **按需服务**：只在收到用户明确请求时执行操作
2. **智能决策**：根据用户请求选择合适的能力组合
3. **风险优先**：任何交易决策都要优先考虑风险控制
4. **透明执行**：清晰说明你的思考过程和调用的能力
5. **资源优化**：宏观分析每日限一次，避免重复调用
6. **动态监控**：用户可以随时添加或移除监控币种

## 响应格式
- 首先说明你的理解和计划
- 然后调用相应的function
- 最后总结结果并给出建议

现在系统处于待机状态，等待用户通过Telegram发送指令。"""

    def process_request(self, request: str, chat_id: str = "default", context: Optional[Dict[str, Any]] = None) -> str:
        """
        处理用户请求或心跳事件

        Args:
            request: 用户请求或系统事件描述
            chat_id: 聊天ID，用于多轮对话
            context: 附加上下文信息

        Returns:
            主脑的响应和处理结果
        """
        try:
            context_info = self._prepare_context(context or {})

            functions = self._get_function_definitions()

            response = self._call_llm_with_functions(request, chat_id, context_info, functions)

            if self.session_manager:
                self.session_manager.add_message(chat_id, 'user', request)
                self.session_manager.add_message(chat_id, 'assistant', response)
                self.session_manager.check_and_compress(chat_id)

            return response

        except Exception as e:
            error_msg = f"Master brain request processing failed: {e}"
            print(error_msg)
            return error_msg
    
    def heartbeat_decision(self, market_conditions: Dict[str, Any]) -> str:
        """
        心跳决策 - 待机模式不执行自动决策
        
        Args:
            market_conditions: 当前市场情况
            
        Returns:
            主脑的待机响应
        """
        return f"""🧠 系统待机中...
        
📊 市场监控正常：
- 币种: {market_conditions.get('symbol', 'N/A')}
- 价格: ${market_conditions.get('latest_price', 'N/A')}
- 状态: 数据收集正常

📱 请通过Telegram机器人发送指令进行分析或交易操作。
"""
    
    def _prepare_context(self, context: Dict[str, Any]) -> str:
        """准备上下文信息"""
        primary_symbols = self.settings.monitor.primary_symbols or []
        monitored_symbols = "无(等待用户添加)" if not primary_symbols else ', '.join([s.replace('USDT', '') for s in primary_symbols])

        context_lines = [
            f"系统时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"监控币种: {monitored_symbols}",
            f"系统模式: {self.settings.system.mode}"
        ]

        if context:
            context_lines.extend([f"{k}: {v}" for k, v in context.items()])

        return '\n'.join(context_lines)
    
    def _get_function_definitions(self) -> List[Dict[str, Any]]:
        """获取所有可用的function definitions"""
        return [
            {
                "name": "technical_analysis",
                "description": "执行技术分析",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "symbol": {"type": "string", "description": "交易对，如BTCUSDT"}
                    },
                    "required": ["symbol"]
                }
            },
            {
                "name": "market_sentiment_analysis", 
                "description": "分析市场情绪",
                "parameters": {"type": "object", "properties": {}}
            },
            {
                "name": "fundamental_analysis",
                "description": "执行基本面分析", 
                "parameters": {
                    "type": "object",
                    "properties": {
                        "symbol": {"type": "string", "description": "交易对，如BTCUSDT"}
                    },
                    "required": ["symbol"]
                }
            },
            {
                "name": "macro_analysis",
                "description": "执行宏观分析",
                "parameters": {"type": "object", "properties": {}}
            },
            {
                "name": "comprehensive_analysis",
                "description": "执行多分析师协作的完整分析",
                "parameters": {
                    "type": "object", 
                    "properties": {
                        "question": {"type": "string", "description": "分析问题或主题"},
                        "symbols": {"type": "array", "items": {"type": "string"}, "description": "要分析的交易对列表"}
                    },
                    "required": ["question"]
                }
            },
            {
                "name": "get_account_status",
                "description": "获取交易账户状态",
                "parameters": {"type": "object", "properties": {}}
            },
            {
                "name": "get_current_positions",
                "description": "获取当前持仓信息", 
                "parameters": {"type": "object", "properties": {}}
            },
            {
                "name": "trading_analysis",
                "description": "执行交易分析和策略制定",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "analysis_results": {"type": "string", "description": "基础分析结果"},
                        "question": {"type": "string", "description": "交易相关问题"}
                    },
                    "required": ["analysis_results", "question"]
                }
            },
            {
                "name": "get_market_data",
                "description": "获取实时市场数据（价格、RSI、MACD等）",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "symbol": {"type": "string", "description": "交易对，如BTCUSDT（单个）"},
                        "symbols": {"type": "array", "items": {"type": "string"}, "description": "交易对列表（多个）"}
                    }
                }
            },
            {
                "name": "manual_trigger_analysis", 
                "description": "手动触发特定币种的完整分析",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "symbol": {"type": "string", "description": "交易对，如BTCUSDT"}
                    },
                    "required": ["symbol"]
                }
            },
            {
                "name": "send_telegram_notification",
                "description": "发送Telegram通知",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "message": {"type": "string", "description": "通知消息内容"}
                    },
                    "required": ["message"]
                }
            },
            {
                "name": "get_system_status",
                "description": "获取系统运行状态",
                "parameters": {"type": "object", "properties": {}}
            },
            {
                "name": "set_monitoring_symbols",
                "description": "设置动态监控币种列表",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "primary_symbols": {
                            "type": "array", 
                            "items": {"type": "string"}, 
                            "description": "主要监控币种列表，如[\"BTCUSDT\", \"ETHUSDT\"]"
                        },
                        "secondary_symbols": {
                            "type": "array", 
                            "items": {"type": "string"}, 
                            "description": "次要监控币种列表，如[\"SOLUSDT\"]"
                        }
                    },
                    "required": ["primary_symbols"]
                }
            },
            {
                "name": "get_monitoring_symbols",
                "description": "获取当前监控币种列表",
                "parameters": {"type": "object", "properties": {}}
            },
            {
                "name": "set_heartbeat_interval",
                "description": "设置心跳监控间隔时间",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "interval_seconds": {
                            "type": "number", 
                            "description": "心跳间隔秒数，如300表示5分钟"
                        }
                    },
                    "required": ["interval_seconds"]
                }
            },
            {
                "name": "get_heartbeat_settings",
                "description": "获取当前心跳设置",
                "parameters": {"type": "object", "properties": {}}
            },
            {
                "name": "start_symbol_monitor",
                "description": "开始监控指定币种，定时执行技术分析",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "symbol": {"type": "string", "description": "交易对，如BTCUSDT"},
                        "interval_minutes": {"type": "number", "description": "监控间隔（分钟），默认30分钟"}
                    },
                    "required": ["symbol"]
                }
            },
            {
                "name": "stop_symbol_monitor",
                "description": "停止监控指定币种",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "symbol": {"type": "string", "description": "交易对，如BTCUSDT"}
                    },
                    "required": ["symbol"]
                }
            },
            {
                "name": "get_symbol_monitors_status",
                "description": "获取所有币种监控状态",
                "parameters": {"type": "object", "properties": {}}
            }
        ]
    
    def _call_llm_with_functions(self, user_request: str, chat_id: str, context_info: str, functions: List[Dict[str, Any]]) -> str:
        """调用LLM with function calling - 支持多轮对话"""
        if not self.llm_client:
            print("Master brain: LLM client not initialized")
            return "LLM client not initialized"

        try:
            function_list = "\n".join([f"- {f['name']}: {f['description']}" for f in functions])
            system_prompt = f"""{self.get_master_brain_prompt()}

可用的函数调用:
{function_list}

如果需要调用函数，请用以下格式：
FUNCTION_CALL: function_name(param1=value1, param2=value2)

注意：字符串参数要用引号，数组参数用方括号。"""

            user_message = f"""## 当前上下文
{context_info}

## 用户请求
{user_request}

请智能分析并执行相应操作。"""

            history = []
            if self.session_manager:
                history = self.session_manager.get_history(chat_id, limit=10)

            if history:
                print(f"Master brain using conversation history: {len(history)} messages")

            print(f"Master brain calling LLM")
            print(f"  - System prompt length: {len(system_prompt)} chars")
            print(f"  - User message length: {len(user_message)} chars")
            print(f"  - History messages: {len(history)}")

            response = self.llm_client.call(
                system_prompt_or_full_prompt=system_prompt,
                user_message=user_message,
                agent_name='智能主脑'
            )
            print(f"LLM raw response length: {len(response)} chars")

            processed_response = self._process_function_calls(response)
            print(f"Processed response length: {len(processed_response)} chars")

            return processed_response

        except Exception as e:
            return f"LLM call failed: {e}"
    
    def _process_function_calls(self, response: str) -> str:
        """处理响应中的function calls - 简化版本"""
        lines = response.split('\n')
        processed_lines = []

        for line in lines:
            if line.strip().startswith('FUNCTION_CALL:'):
                try:
                    func_call = line.replace('FUNCTION_CALL:', '').strip()

                    # 控制台输出调用日志
                    print(f"[Master Brain] Executing: {func_call}")

                    result = self._execute_function_call(func_call)

                    # 控制台输出结果
                    print(f"[Master Brain] Result: {result[:200]}..." if len(result) > 200 else f"[Master Brain] Result: {result}")

                    # 不再添加调用信息到返回给用户的响应中
                    # 只添加结果（如果需要的话可以格式化）
                    if result and not result.startswith('❌'):
                        processed_lines.append(result)
                    elif result.startswith('❌'):
                        processed_lines.append(result)

                except Exception as e:
                    import traceback
                    error_detail = traceback.format_exc()
                    print(f"[Master Brain] Error: {e}")
                    print(f"[Master Brain] Traceback: {error_detail}")
                    processed_lines.append(f"❌ 执行失败: {e}")
            else:
                processed_lines.append(line)

        return '\n'.join(processed_lines)
    
    def _execute_function_call(self, func_call: str) -> str:
        """执行具体的function call"""
        try:
            # 简单的函数调用解析（实际项目中可以用更完善的解析器）
            if 'technical_analysis(' in func_call:
                symbol = self._extract_param(func_call, 'symbol')
                return self.controller.analyze_kline_data(symbol)
            
            elif 'market_sentiment_analysis(' in func_call:
                return self.controller.analyze_market_sentiment()
            
            elif 'fundamental_analysis(' in func_call:
                symbol = self._extract_param(func_call, 'symbol') 
                return self.controller.analyze_fundamental_data(symbol)
            
            elif 'macro_analysis(' in func_call:
                return self.controller.analyze_macro_data()
            
            elif 'comprehensive_analysis(' in func_call:
                question = self._extract_param(func_call, 'question')
                symbols = self._extract_param(func_call, 'symbols')
                # symbols 现在可能是列表或字符串
                if isinstance(symbols, str) and symbols:
                    symbols = [symbols]  # 单个symbol转为列表
                return self.controller.ask_claude_with_data(question, symbols)
            
            elif 'get_account_status(' in func_call:
                return json.dumps(self.controller.get_account_info(), ensure_ascii=False, indent=2, default=self._json_serializer)
            
            elif 'get_current_positions(' in func_call:
                # 获取当前持仓信息
                positions = self.controller.portfolio_manager.get_positions()
                return json.dumps(positions, ensure_ascii=False, indent=2, default=self._json_serializer)
            
            elif 'manual_trigger_analysis(' in func_call:
                symbol = self._extract_param(func_call, 'symbol')
                if symbol:
                    return self.controller.manual_analysis(symbol)
                else:
                    # 尝试从symbols参数获取（数组格式）
                    symbols = self._extract_param(func_call, 'symbols')
                    if symbols and isinstance(symbols, list):
                        results = []
                        for s in symbols:
                            result = self.controller.manual_analysis(s)
                            results.append(f"{s}: {result}")
                        return "\n".join(results)
                    else:
                        return "❌ 未找到有效的symbol或symbols参数"
            
            elif 'send_telegram_notification(' in func_call:
                message = self._extract_param(func_call, 'message')
                result = self.controller.telegram_integration.send_notification(message)
                return f"通知发送{'成功' if result else '失败'}"
            
            elif 'get_system_status(' in func_call:
                return json.dumps(self.controller.get_system_status(), ensure_ascii=False, indent=2, default=self._json_serializer)
            
            elif 'set_monitoring_symbols(' in func_call:
                primary_symbols = self._extract_param(func_call, 'primary_symbols')
                secondary_symbols = self._extract_param(func_call, 'secondary_symbols') or []
                return self.controller.set_monitoring_symbols(primary_symbols, secondary_symbols)
            
            elif 'get_monitoring_symbols(' in func_call:
                return json.dumps(self.controller.get_monitoring_symbols(), ensure_ascii=False, indent=2)
            
            elif 'set_heartbeat_interval(' in func_call:
                interval_seconds = self._extract_param(func_call, 'interval_seconds')
                return self.controller.set_heartbeat_interval(float(interval_seconds))
            
            elif 'get_heartbeat_settings(' in func_call:
                return json.dumps(self.controller.get_heartbeat_settings(), ensure_ascii=False, indent=2)

            elif 'start_symbol_monitor(' in func_call:
                symbol = self._extract_param(func_call, 'symbol')
                interval_minutes = self._extract_param(func_call, 'interval_minutes')
                interval = int(interval_minutes) if interval_minutes else 30
                result = self.controller.start_symbol_monitor(symbol, interval)
                return result['message']

            elif 'stop_symbol_monitor(' in func_call:
                symbol = self._extract_param(func_call, 'symbol')
                result = self.controller.stop_symbol_monitor(symbol)
                return result['message']

            elif 'get_symbol_monitors_status(' in func_call:
                return json.dumps(self.controller.get_symbol_monitors_status(), ensure_ascii=False, indent=2)

            elif 'get_market_data(' in func_call:
                symbol = self._extract_param(func_call, 'symbol')
                symbols = self._extract_param(func_call, 'symbols')

                # 支持单个symbol或symbols数组
                symbol_list = []
                if symbol:
                    symbol_list = [symbol]
                elif symbols:
                    if isinstance(symbols, list):
                        symbol_list = symbols
                    elif isinstance(symbols, str):
                        symbol_list = [symbols]

                if not symbol_list:
                    return "❌ 缺少symbol或symbols参数"

                results = []
                for sym in symbol_list:
                    kline_data = self.controller.data_service.collect_kline_data(sym)
                    if kline_data:
                        latest = kline_data[-1] if isinstance(kline_data, list) else kline_data
                        results.append({
                            'symbol': sym,
                            'price': latest.get('close'),
                            'rsi': latest.get('rsi'),
                            'macd': latest.get('macd'),
                            'volume': latest.get('volume'),
                            'timestamp': latest.get('timestamp')
                        })
                    else:
                        results.append({'symbol': sym, 'error': '无法获取数据'})

                return json.dumps(results, ensure_ascii=False, indent=2)

            else:
                return f"❌ 未知的函数调用: {func_call}"
                
        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            return f"❌ 函数执行失败: {e}\n详细错误: {error_detail}"
    
    def _extract_param(self, func_call: str, param_name: str) -> Optional[str]:
        """从函数调用字符串中提取参数值"""
        try:
            import re
            
            # 简单的参数提取 - 数组参数特殊处理
            if param_name == 'symbols' and '[' in func_call and ']' in func_call:
                pattern = f'{param_name}=(\\[[^\\]]+\\])'
                match = re.search(pattern, func_call)
                if match:
                    array_str = match.group(1)
                    # 简单解析数组内容
                    array_content = array_str[1:-1].strip()  # 移除[]
                    if array_content:
                        items = [item.strip().strip('"\'') for item in array_content.split(',')]
                        return items
                    return []
            
            # 普通参数处理 - 简化版
            pattern = f'{param_name}=([^,)]+)'
            match = re.search(pattern, func_call)
            if match:
                value = match.group(1).strip()
                # 移除引号
                if (value.startswith('"') and value.endswith('"')) or \
                   (value.startswith("'") and value.endswith("'")):
                    value = value[1:-1]
                return value if value else None
            return None
        except Exception as e:
            print(f"⚠️ 参数提取失败 {param_name}: {e}")
            return None
    
    def _json_serializer(self, obj):
        """自定义JSON序列化器 - 处理不可序列化的类型"""
        import numpy as np
        
        if isinstance(obj, np.bool_):
            return bool(obj)  # numpy bool转为Python bool
        elif isinstance(obj, np.integer):
            return int(obj)   # numpy int转为Python int
        elif isinstance(obj, np.floating):
            return float(obj) # numpy float转为Python float
        elif isinstance(obj, np.ndarray):
            return obj.tolist() # numpy数组转为列表
        elif hasattr(obj, '__dict__'):
            return str(obj)  # 对象转为字符串
        elif callable(obj):
            return str(obj)  # 函数转为字符串
        else:
            return str(obj)  # 其他类型转为字符串