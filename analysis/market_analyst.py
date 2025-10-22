# -*- coding: utf-8 -*-
"""
市场分析师
专注于市场情绪和整体趋势分析
"""

from typing import Dict, Any
from analysis.base_analyst import BaseAnalyst
from analysis.prompt_manager import PromptManager
from config import Settings


class MarketAnalyst(BaseAnalyst):
    """市场分析师"""

    def __init__(self, settings: Settings, llm_client):
        """
        初始化市场分析师

        Args:
            settings: 系统配置
            llm_client: LLM客户端
        """
        super().__init__(
            name="市场分析师",
            model_config=settings.api.market_analyst,
            settings=settings
        )
        self.llm_client = llm_client
        self.prompt_manager = PromptManager()

    def get_prompt_template(self) -> str:
        """
        获取市场分析师的提示模板

        Returns:
            str: 提示模板
        """
        return self.prompt_manager.get_market_sentiment_prompt()

    def analyze(self, context: 'AnalysisContext') -> str:
        """
        执行市场情绪分析 - 从context获取数据

        Args:
            context: 分析上下文

        Returns:
            str: 市场情绪分析结果
        """
        try:
            # 获取系统提示词
            system_prompt = self.get_prompt_template()

            # 构建用户消息
            user_message = self._format_market_sentiment_message(
                context.global_market_data,
                context.fear_greed_index,
                context.trending_coins,
                context.major_coins_performance
            )

            # 调用LLM（分离模式）
            if self.llm_client:
                if hasattr(self.llm_client, 'call'):
                    return self.llm_client.call(system_prompt, user_message=user_message, agent_name='市场分析师')
                else:
                    full_prompt = f"{system_prompt}\n\n{user_message}"
                    return self.llm_client(full_prompt)
            else:
                return "❌ 市场分析师: LLM客户端未初始化"

        except Exception as e:
            import traceback
            traceback.print_exc()
            return f"❌ 市场情绪分析失败: {str(e)}"

    def _format_market_sentiment_message(self, global_data: Dict[str, Any], fear_greed_index: Dict[str, Any],
                                        trending_data: list, major_coins: list) -> str:
        """
        格式化市场情绪分析数据为用户消息

        Args:
            global_data: 全球市场数据
            fear_greed_index: 恐贪指数数据
            trending_data: 热门币种数据
            major_coins: 主流币种表现数据
        """
        message_parts = ["请基于以下多维度数据分析当前加密货币市场情绪：\n"]

        # 全球市场数据
        message_parts.append("=== 全球市场数据 ===")
        message_parts.append(self._format_global_data(global_data))
        message_parts.append("")

        # 恐贪指数数据
        message_parts.append("=== 恐贪指数 ===")
        if fear_greed_index:
            message_parts.append(f"当前指数: {fear_greed_index.get('value', 0)} ({fear_greed_index.get('classification', '未知')})")
            message_parts.append(f"数据源: {fear_greed_index.get('source', '未知')}")
            timestamp = fear_greed_index.get('timestamp', '未知')
            message_parts.append(f"更新时间: {timestamp}")
        else:
            message_parts.append("❌ 恐贪指数数据暂时不可用")
        message_parts.append("")

        # BTC/ETH主导率
        message_parts.append("=== BTC/ETH主导率 ===")
        if global_data and 'market_cap_percentage' in global_data:
            market_cap_pct = global_data['market_cap_percentage']
            btc_dom = market_cap_pct.get('btc', 0)
            eth_dom = market_cap_pct.get('eth', 0)
            message_parts.append(f"BTC主导率: {btc_dom:.2f}%")
            message_parts.append(f"ETH主导率: {eth_dom:.2f}%")

            if btc_dom > 50:
                message_parts.append("分析：BTC主导地位强势，市场相对保守")
            elif btc_dom < 40:
                message_parts.append("分析：山寨币活跃，市场风险偏好上升")
        else:
            message_parts.append("❌ 主导率数据暂时不可用")
        message_parts.append("")

        # 热门搜索趋势
        message_parts.append("=== 热门搜索趋势 ===")
        message_parts.append(self._format_trending_data(trending_data))
        message_parts.append("")

        # 主流币种表现
        message_parts.append("=== 主流币种表现 ===")
        message_parts.append(self._format_major_coins_performance_data(major_coins))
        message_parts.append("")

        message_parts.append("请提供客观专业的市场情绪评估，重点关注多个指标之间的相互验证。")

        return "\n".join(message_parts)

    def assess_market_sentiment(self, indicators: Dict[str, Any], global_data: Dict[str, Any]) -> str:
        """
        评估市场情绪

        Args:
            indicators: 技术指标
            global_data: 全球数据

        Returns:
            str: 市场情绪评估
        """
        sentiments = []

        try:
            # 基于RSI的情绪
            rsi_data = indicators.get('rsi', {})
            rsi_value = rsi_data.get('value')
            if rsi_value is not None:
                if rsi_value > 80:
                    sentiments.append("极度贪婪")
                elif rsi_value > 70:
                    sentiments.append("贪婪")
                elif rsi_value < 20:
                    sentiments.append("极度恐慌")
                elif rsi_value < 30:
                    sentiments.append("恐慌")
                else:
                    sentiments.append("中性")

            # 基于市值变化的情绪
            if global_data:
                market_change = global_data.get('market_cap_change_percentage_24h_usd', 0)
                if market_change > 5:
                    sentiments.append("市场乐观")
                elif market_change < -5:
                    sentiments.append("市场悲观")

            return " & ".join(sentiments) if sentiments else "情绪不明"

        except Exception as e:
            return f"情绪评估异常: {e}"

    def _format_global_data(self, global_data: Dict[str, Any]) -> str:
        """格式化全球市场数据"""
        if not global_data:
            return "❌ 暂无全球市场数据"

        lines = [
            f"总市值: ${global_data.get('total_market_cap_usd', 0):,.0f}",
            f"24H成交量: ${global_data.get('total_volume_24h_usd', 0):,.0f}",
            f"24H市值变化: {global_data.get('market_cap_change_percentage_24h_usd', 0):.2f}%",
            f"活跃加密货币: {global_data.get('active_cryptocurrencies', 0)}"
        ]
        return '\n'.join(lines)

    def _format_trending_data(self, trending_data: list) -> str:
        """格式化热门币种数据"""
        if not trending_data:
            return "❌ 暂无热门币种数据"

        trending_info = []
        for coin in trending_data[:5]:
            name = coin.get('name', coin.get('symbol', 'Unknown'))
            symbol = coin.get('symbol', '').upper()
            rank = coin.get('market_cap_rank', '?')
            trending_info.append(f"{name} ({symbol}) [排名#{rank}]")

        return '\n'.join(trending_info)

    def _format_major_coins_performance_data(self, major_coins: list) -> str:
        """格式化主流币种表现数据"""
        if not major_coins:
            return "❌ 暂无主流币种数据"

        lines = []
        for coin in major_coins:
            symbol = coin.get('symbol', '').upper()
            name = coin.get('name', 'Unknown')
            price = coin.get('current_price', 0)
            change_24h = coin.get('price_change_24h', 0)
            volume = coin.get('total_volume', 0)

            lines.append(f"{name} ({symbol}): ${price:.2f} ({change_24h:+.2f}%) 成交量:${volume:,.0f}")

        return '\n'.join(lines)
