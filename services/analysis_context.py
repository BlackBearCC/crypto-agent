# -*- coding: utf-8 -*-
"""
分析上下文
统一管理所有分析所需的数据，避免参数传递混乱
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional


@dataclass
class AnalysisContext:
    """统一的分析上下文，包含所有分析所需数据"""

    # 目标币种
    target_symbol: str

    # 市场情绪数据（市场分析师使用）
    global_market_data: Optional[Dict[str, Any]] = None
    fear_greed_index: Optional[Dict[str, Any]] = None
    trending_coins: Optional[List[Dict[str, Any]]] = None
    major_coins_performance: Optional[List[Dict[str, Any]]] = None

    # K线数据（技术分析师使用）
    kline_data: Dict[str, List[Dict[str, Any]]] = field(default_factory=dict)

    # 宏观数据（宏观分析师使用）
    macro_data: Optional[Dict[str, Any]] = None

    # 其他分析结果（首席分析师整合使用）
    technical_analysis: Optional[str] = None
    sentiment_analysis: Optional[str] = None
    fundamental_analysis_result: Optional[str] = None
    macro_analysis_result: Optional[str] = None

    def has_kline_data(self) -> bool:
        """检查是否有指定币种的K线数据"""
        return self.target_symbol in self.kline_data and bool(self.kline_data[self.target_symbol])

    def has_market_data(self) -> bool:
        """检查是否有市场数据"""
        return self.global_market_data is not None

    def has_macro_data(self) -> bool:
        """检查是否有宏观数据"""
        return self.macro_data is not None

    def get_kline_data(self) -> List[Dict[str, Any]]:
        """获取目标币种的K线数据"""
        return self.kline_data.get(self.target_symbol, [])
