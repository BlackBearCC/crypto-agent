# -*- coding: utf-8 -*-
"""
基本面分析师
专注于项目基础和长期价值分析
"""

from typing import Dict, Any
from analysis.base_analyst import BaseAnalyst
from analysis.prompt_manager import PromptManager
from config import Settings


class FundamentalAnalyst(BaseAnalyst):
    """基本面分析师"""

    def __init__(self, settings: Settings, llm_client):
        """
        初始化基本面分析师

        Args:
            settings: 系统配置
            llm_client: LLM客户端
        """
        super().__init__(
            name="基本面分析师",
            model_config=settings.api.fundamental_analyst,
            settings=settings
        )
        self.llm_client = llm_client
        self.prompt_manager = PromptManager()

    def get_prompt_template(self) -> str:
        """
        获取基本面分析师的提示模板

        Returns:
            str: 提示模板
        """
        return self.prompt_manager.get_fundamental_analysis_prompt()

    def analyze(self, context: 'AnalysisContext') -> str:
        """
        执行基本面分析 - 从context获取数据

        Args:
            context: 分析上下文

        Returns:
            str: 基本面分析结果
        """
        try:
            # 1. 获取系统提示词
            system_prompt = self.get_prompt_template()

            # 2. 构建用户消息（基本面数据较少，主要是价格和市场统计）
            user_message = f"请分析{context.target_symbol}的基本面情况：\n"
            user_message += "基于当前价格表现、成交量和市场地位进行分析。\n"
            user_message += f"\n币种: {context.target_symbol}"

            # 3. 调用LLM（分离模式）
            if self.llm_client:
                if hasattr(self.llm_client, 'call'):
                    return self.llm_client.call(system_prompt, user_message=user_message, agent_name='基本面分析师')
                else:
                    full_prompt = f"{system_prompt}\n\n{user_message}"
                    return self.llm_client(full_prompt)
            else:
                return "❌ 基本面分析师: LLM客户端未初始化"

        except Exception as e:
            import traceback
            traceback.print_exc()
            return f"❌ 基本面分析失败: {str(e)}"
