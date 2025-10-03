# -*- coding: utf-8 -*-
"""
交易员
专注于交易决策和仓位管理
"""

from typing import Dict, Any, Optional
from analysis.base_analyst import BaseAnalyst
from analysis.prompt_manager import PromptManager
from config import Settings


class TraderAnalyst(BaseAnalyst):
    """交易员 - 负责交易决策和仓位管理"""

    def __init__(self, settings: Settings, llm_client, trading_client):
        """
        初始化交易员

        Args:
            settings: 系统配置
            llm_client: LLM客户端
            trading_client: 交易客户端
        """
        super().__init__(
            name="永续交易员",
            model_config=settings.api.perpetual_trader,
            settings=settings
        )
        self.llm_client = llm_client
        self.trading_client = trading_client
        self.prompt_manager = PromptManager()

    def get_prompt_template(self) -> str:
        """
        获取交易员的提示模板

        Returns:
            str: 提示模板
        """
        return self.prompt_manager.get_trader_prompt()

    def analyze_trading_decision(
        self,
        symbol: str,
        technical_analysis: str,
        account_balance: Dict[str, Any] = None,
        current_positions: Dict[str, Any] = None
    ) -> str:
        """
        交易决策分析

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
                    # 兼容旧接口
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
