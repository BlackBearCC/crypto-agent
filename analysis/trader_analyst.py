# -*- coding: utf-8 -*-
"""
交易员
专注于交易决策和仓位管理
"""

import json
from typing import Dict, Any, Optional, List
from analysis.base_analyst import BaseAnalyst
from analysis.prompt_manager import PromptManager
from config import Settings
from database import DatabaseManager


class TraderAnalyst(BaseAnalyst):
    """交易员 - 负责交易决策和仓位管理"""

    def __init__(self, settings: Settings, llm_client, trading_client, db_manager: DatabaseManager):
        """
        初始化交易员

        Args:
            settings: 系统配置
            llm_client: LLM客户端
            trading_client: 交易客户端
            db_manager: 数据库管理器
        """
        super().__init__(
            name="永续交易员",
            model_config=settings.api.perpetual_trader,
            settings=settings
        )
        self.llm_client = llm_client
        self.trading_client = trading_client
        self.db_manager = db_manager
        self.prompt_manager = PromptManager()

    def get_prompt_template(self) -> str:
        """
        获取交易员的提示模板

        Returns:
            str: 提示模板
        """
        return self.prompt_manager.get_trader_prompt()

    def analyze(self, context: Dict[str, Any]) -> str:
        """
        执行交易分析 - 实现抽象方法
        
        Args:
            context: 分析上下文数据
            
        Returns:
            str: 分析结果
        """
        try:
            # 从上下文中提取必要信息
            symbol = context.get('symbol', 'BTCUSDT')
            research_results = context.get('research_results', {})
            question = context.get('question', '请提供交易建议')
            
            # 调用交易分析方法
            return self.conduct_trading_analysis(research_results, question)
            
        except Exception as e:
            return f"❌ 交易分析失败: {str(e)}"

    def conduct_trading_analysis(self, research_results: Dict[str, Any], question: str) -> str:
        """
        交易部门：投资组合决策

        Args:
            research_results: 研究部门的综合分析结果
            question: 用户问题

        Returns:
            str: 交易分析报告
        """
        print("💼 [交易部门] 制定投资组合策略...", flush=True)

        # 获取当前账户状态
        print("📊 获取账户信息...", flush=True)
        account_balance = self.trading_client.get_account_balance()
        current_positions = self.trading_client.get_current_positions()

        # 打印账户信息
        self._print_account_info(account_balance, current_positions)

        # 获取历史交易参考
        recent_research = self._get_recent_chief_analysis(10)

        # 交易决策分析
        symbols_analyzed = list(research_results['symbol_analyses'].keys())
        primary_symbol = symbols_analyzed[0] if symbols_analyzed else 'BTCUSDT'

        trading_analysis = self._generate_trading_analysis(
            research_results, question, account_balance, current_positions,
            recent_research, primary_symbol
        )

        return trading_analysis

    def _print_account_info(self, account_balance: Dict[str, Any], current_positions: Dict[str, Any]):
        """打印账户信息"""
        print("💰 当前账户余额:")
        if account_balance.get('success'):
            print(f"  账户类型: {account_balance.get('account_type', 'N/A')}")
            print(f"  总余额: ${account_balance.get('total_wallet_balance', 0):.2f} USDT")
            print(f"  可用余额: ${account_balance.get('available_balance', 0):.2f} USDT")
            print(f"  未实现盈亏: ${account_balance.get('total_unrealized_profit', 0):.2f} USDT")
        else:
            print(f"  ❌ {account_balance.get('error', '未知错误')}")

        print("📈 当前持仓:")
        if current_positions.get('success') and current_positions.get('positions'):
            for pos in current_positions['positions']:
                direction = "多头" if pos['position_amt'] > 0 else "空头"
                symbol_name = pos['symbol'].replace('USDT', '')
                print(f"  {symbol_name} {direction}: 数量={abs(pos['position_amt']):.4f}, 盈亏=${pos['unrealized_profit']:.2f}")
        else:
            if current_positions.get('error'):
                print(f"  ❌ {current_positions['error']}")
            else:
                print("  ✅ 无持仓")

    def _get_recent_chief_analysis(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取最近的首席分析师概要"""
        try:
            records = self.db_manager.get_analysis_records(
                data_type='chief_analysis',
                agent_name='首席分析师',
                limit=limit
            )

            results = []
            for record in records:
                results.append({
                    'timestamp': record.timestamp.isoformat() if record.timestamp else None,
                    'symbol': record.symbol,
                    'summary': record.summary,
                    'content_preview': record.content[:200] if record.content else None
                })

            return results

        except Exception as e:
            print(f"❌ 获取首席分析历史失败: {e}")
            return []

    def _generate_trading_analysis(self, research_results: Dict[str, Any], question: str,
                                 account_balance: Dict[str, Any], current_positions: Dict[str, Any],
                                 recent_research: List[Dict[str, Any]], primary_symbol: str) -> str:
        """生成交易分析"""
        try:
            primary_symbol_name = primary_symbol.replace('USDT', '')

            # 获取可用交易工具描述
            trading_tools_desc = self._get_trading_tools_description()

            trading_prompt = f"""你是专业的期货交易员，基于研究部门的多币种分析报告，重点针对 {primary_symbol} 制定合约交易策略：

=== 研究部门综合报告 ===
{research_results['research_summary']}

=== 可用交易工具 ===
{trading_tools_desc}

=== 当前账户状态 ===
余额信息: {json.dumps(account_balance, indent=2, ensure_ascii=False)}
当前持仓: {json.dumps(current_positions, indent=2, ensure_ascii=False)}

=== 历史交易参考 ===
{json.dumps(recent_research, indent=2, ensure_ascii=False)}

=== 用户问题 ===
{question}

=== 专业交易原则 ===
1. **严格风险控制**：只在有明确优势的情况下交易
2. **宁缺毋滥**：没有把握不如观望等待更好机会
3. **趋势确认**：技术面、基本面、宏观面至少2个维度一致才考虑交易
4. **合理仓位**：根据置信度和风险调整仓位大小
5. **观望策略**：以下情况应选择HOLD观望：
   - 各维度分析出现明显分歧
   - 市场处于震荡整理阶段，方向不明
   - 技术指标处于中性区间
   - 宏观面存在重大不确定性
   - 当前已有足够仓位，不宜加仓
6. **止盈止损**：每笔交易都要设置明确的止盈止损点位

=== 交易决策要求 ===
请基于以上信息提供具体的交易建议：

1. **交易方向建议**：
   - LONG {primary_symbol_name}：看多，建议开多单
   - SHORT {primary_symbol_name}：看空，建议开空单
   - HOLD：观望，暂不交易

2. **具体交易参数**（如果建议交易）：
   - 建议仓位大小（占总资金百分比）
   - 建议杠杆倍数
   - 入场点位
   - 止损点位
   - 止盈点位

3. **风险提示**：
   - 主要风险因素
   - 需要关注的市场变化

4. **执行建议**：
   - 是否需要立即执行
   - 还是等待更好的入场时机

请提供专业、具体、可执行的交易建议。"""

            # 调用LLM进行交易分析
            if not self.llm_client:
                return "❌ LLM客户端未初始化，无法进行交易分析"

            if hasattr(self.llm_client, 'call'):
                response = self.llm_client.call(trading_prompt, agent_name='永续交易员')
            else:
                response = self.llm_client(trading_prompt)

            return f"💼 永续交易员分析报告\n\n{response}"

        except Exception as e:
            return f"❌ 交易分析生成失败: {str(e)}"

    def _get_trading_tools_description(self) -> str:
        """获取交易工具描述"""
        return """
**币安USDT永续合约交易工具**

1. **账户余额查询** (get_account_balance)
   - 总钱包余额
   - 可用余额
   - 未实现盈亏
   - 保证金余额

2. **持仓信息查询** (get_current_positions)
   - 持仓币种和方向
   - 持仓数量和入场价
   - 当前标记价格
   - 未实现盈亏
   - 杠杆倍数
   - 强平价格

3. **市价开仓/平仓**
   - 支持做多(LONG)和做空(SHORT)
   - 支持市价单和限价单
   - 自动计算仓位大小
   - 支持设置杠杆倍数

4. **风险管理**
   - 止损单(Stop Loss)
   - 止盈单(Take Profit)
   - 仓位大小控制
   - 杠杆倍数调整
"""

    def analyze_trading_decision(
        self,
        symbol: str,
        technical_analysis: str,
        account_balance: Dict[str, Any] = None,
        current_positions: Dict[str, Any] = None
    ) -> str:
        """
        交易决策分析（旧版接口，保持兼容性）

        Args:
            symbol: 币种符号
            technical_analysis: 技术分析结果
            account_balance: 账户余额信息
            current_positions: 当前持仓信息

        Returns:
            str: 交易决策分析结果
        """
        try:
            # 1. 获取系统提示词
            system_prompt = self.get_prompt_template()

            # 2. 获取账户信息
            if account_balance is None:
                account_balance = self.trading_client.get_account_balance()

            if current_positions is None:
                current_positions = self.trading_client.get_current_positions()

            # 3. 构建用户消息
            user_message = self._format_trading_decision_message(
                symbol, technical_analysis, account_balance, current_positions
            )

            # 4. 调用LLM
            if self.llm_client:
                if hasattr(self.llm_client, 'call'):
                    response = self.llm_client.call(
                        system_prompt,
                        user_message=user_message,
                        agent_name='永续交易员'
                    )
                else:
                    full_prompt = f"{system_prompt}\n\n{user_message}"
                    response = self.llm_client(full_prompt)

                return response
            else:
                return "❌ 交易员: LLM客户端未初始化"

        except Exception as e:
            return f"❌ 交易决策分析失败: {str(e)}"

    def _format_trading_decision_message(
        self,
        symbol: str,
        technical_analysis: str,
        account_balance: Dict[str, Any],
        current_positions: Dict[str, Any]
    ) -> str:
        """
        格式化交易决策消息

        Args:
            symbol: 币种符号
            technical_analysis: 技术分析结果
            account_balance: 账户余额
            current_positions: 当前持仓

        Returns:
            str: 格式化后的消息
        """
        symbol_name = symbol.replace('USDT', '')

        message = f"""=== 币种信息 ===
交易对: {symbol}

=== 技术分析报告 ===
{technical_analysis}

=== 账户状态 ===
"""

        # 格式化账户余额
        if account_balance and 'error' not in account_balance:
            if account_balance.get('success'):
                message += f"""账户类型: {account_balance.get('account_type', 'N/A')}
总余额: ${account_balance.get('total_wallet_balance', 0):.2f} USDT
可用余额: ${account_balance.get('available_balance', 0):.2f} USDT
未实现盈亏: ${account_balance.get('total_unrealized_profit', 0):.2f} USDT
"""
            else:
                message += "账户信息获取失败\n"
        else:
            message += f"账户信息错误: {account_balance.get('error', '未知错误')}\n"

        message += "\n=== 当前持仓 ===\n"

        # 格式化持仓信息
        if current_positions and 'error' not in current_positions:
            if current_positions.get('success') and current_positions.get('positions'):
                positions = current_positions['positions']
                # 筛选当前币种的持仓
                symbol_positions = [p for p in positions if p['symbol'] == symbol]

                if symbol_positions:
                    for pos in symbol_positions:
                        direction = "多头" if pos['position_amt'] > 0 else "空头"
                        message += f"""{symbol_name} {direction}持仓:
  数量: {abs(pos['position_amt']):.4f}
  开仓价: ${pos['entry_price']:.4f}
  标记价: ${pos['mark_price']:.4f}
  未实现盈亏: ${pos['unrealized_profit']:.2f}
  杠杆: {pos['leverage']}x
"""
                else:
                    message += f"无 {symbol_name} 持仓\n"
            else:
                message += "无持仓\n"
        else:
            message += f"持仓信息错误: {current_positions.get('error', '未知错误')}\n"

        message += f"""
=== 交易决策要求 ===
请基于以上技术分析和账户状态，为 {symbol_name} 提供具体的交易决策：

1. **交易方向**：
   - LONG: 看多，建议开多单或加多仓
   - SHORT: 看空，建议开空单或加空仓
   - CLOSE_LONG: 平多仓
   - CLOSE_SHORT: 平空仓
   - HOLD: 观望，暂不交易

2. **仓位管理**（如果建议交易）：
   - 建议仓位大小（USDT金额）
   - 建议杠杆倍数
   - 入场点位
   - 止损点位
   - 止盈点位

3. **风险评估**：
   - 主要风险因素
   - 风险等级（低/中/高）
   - 止损幅度建议

4. **执行建议**：
   - 是否立即执行还是等待更好时机
   - 分批建仓还是一次性建仓

请提供专业、具体、可执行的交易建议。"""

        return message

    def get_account_info(self) -> Dict[str, Any]:
        """获取账户信息"""
        return {
            'balance': self.trading_client.get_account_balance(),
            'positions': self.trading_client.get_current_positions(),
            'trading_available': self.trading_client.is_available()
        }

    def get_positions(self) -> Dict[str, Any]:
        """获取当前持仓信息"""
        return self.trading_client.get_current_positions()

    def execute_trade(self, symbol: str, side: str, quantity: float,
                     order_type: str = "MARKET", price: Optional[float] = None) -> Dict[str, Any]:
        """执行交易"""
        if not self.trading_client.is_available():
            return {"error": "交易功能不可用"}

        return self.trading_client.place_futures_order(symbol, side, quantity, order_type, price)
