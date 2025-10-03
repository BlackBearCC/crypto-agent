# -*- coding: utf-8 -*-
"""
交易客户端 - 使用币安官方SDK
负责与币安API交互，执行交易操作
"""

import os
from typing import Dict, Any, Optional, List
from config import Settings

try:
    from binance_common.configuration import ConfigurationRestAPI
    from binance_common.constants import DERIVATIVES_TRADING_USDS_FUTURES_REST_API_PROD_URL
    from binance_sdk_derivatives_trading_usds_futures.derivatives_trading_usds_futures import DerivativesTradingUsdsFutures
    BINANCE_SDK_AVAILABLE = True
except ImportError:
    BINANCE_SDK_AVAILABLE = False
    DerivativesTradingUsdsFutures = None


class TradingClient:
    """币安交易客户端 - 使用USDT永续合约SDK"""

    def __init__(self, settings: Settings):
        """
        初始化交易客户端

        Args:
            settings: 系统配置对象
        """
        self.settings = settings
        self.futures_client = None

        if BINANCE_SDK_AVAILABLE:
            self._init_binance_futures()
        else:
            print("⚠️ 未安装binance-sdk-derivatives-trading-usds-futures，交易功能将不可用")
            print("   运行: pip install binance-sdk-derivatives-trading-usds-futures")

    def _init_binance_futures(self):
        """初始化币安USDT永续合约客户端"""
        try:
            # 从环境变量读取API密钥
            api_key = os.getenv('BINANCE_API_KEY', '').strip()
            api_secret = os.getenv('BINANCE_API_SECRET', '').strip()

            if not api_key or not api_secret:
                print("⚠️ 未配置币安API密钥，交易功能将不可用")
                return

            # 创建配置
            configuration = ConfigurationRestAPI(
                api_key=api_key,
                api_secret=api_secret,
                base_path=DERIVATIVES_TRADING_USDS_FUTURES_REST_API_PROD_URL
            )

            # 创建USDT永续合约客户端
            self.futures_client = DerivativesTradingUsdsFutures(config_rest_api=configuration)

            print("✅ 币安USDT永续合约客户端初始化成功")

        except Exception as e:
            print(f"❌ 初始化币安USDT永续合约客户端失败: {e}")
            self.futures_client = None

    def get_account_balance(self) -> Dict[str, Any]:
        """获取账户余额 - 使用USDT永续合约SDK"""
        try:
            if not self.futures_client:
                return {"error": "合约客户端未初始化"}

            # 获取账户信息
            response = self.futures_client.rest_api.account_information_v3()
            data = response.data()

            # 获取余额列表
            balance_response = self.futures_client.rest_api.futures_account_balance_v3()
            balance_data = balance_response.data()

            # 提取USDT余额
            usdt_balance = None
            if balance_data:
                for balance in balance_data:
                    if hasattr(balance, 'asset') and balance.asset == 'USDT':
                        usdt_balance = {
                            'balance': float(balance.balance) if hasattr(balance, 'balance') else 0,
                            'available_balance': float(balance.available_balance) if hasattr(balance, 'available_balance') else 0
                        }
                        break

            return {
                "success": True,
                "account_type": "USDT永续合约",
                "total_wallet_balance": float(data.total_wallet_balance) if hasattr(data, 'total_wallet_balance') else 0,
                "available_balance": float(data.available_balance) if hasattr(data, 'available_balance') else 0,
                "total_unrealized_profit": float(data.total_unrealized_profit) if hasattr(data, 'total_unrealized_profit') else 0,
                "total_margin_balance": float(data.total_margin_balance) if hasattr(data, 'total_margin_balance') else 0,
                "usdt_balance": usdt_balance
            }

        except Exception as e:
            return {"error": f"获取余额失败: {str(e)}"}

    def get_current_positions(self) -> Dict[str, Any]:
        """获取当前持仓 - 使用USDT永续合约SDK"""
        try:
            if not self.futures_client:
                return {"error": "合约客户端未初始化"}

            # 获取持仓信息
            response = self.futures_client.rest_api.position_information_v3()
            data = response.data()

            # 筛选活跃持仓 (positionAmt != 0)
            active_positions = []
            if data:
                for pos in data:
                    if hasattr(pos, 'position_amt') and float(pos.position_amt) != 0:
                        position_info = {
                            'symbol': pos.symbol if hasattr(pos, 'symbol') else 'N/A',
                            'position_side': pos.position_side if hasattr(pos, 'position_side') else 'N/A',
                            'position_amt': float(pos.position_amt) if hasattr(pos, 'position_amt') else 0,
                            'entry_price': float(pos.entry_price) if hasattr(pos, 'entry_price') else 0,
                            'mark_price': float(pos.mark_price) if hasattr(pos, 'mark_price') else 0,
                            'unrealized_profit': float(pos.un_realized_profit) if hasattr(pos, 'un_realized_profit') else 0,
                            'leverage': int(pos.leverage) if hasattr(pos, 'leverage') else 1,
                            'liquidation_price': float(pos.liquidation_price) if hasattr(pos, 'liquidation_price') else 0
                        }
                        active_positions.append(position_info)

            return {
                "success": True,
                "positions": active_positions,
                "position_count": len(active_positions)
            }

        except Exception as e:
            return {"error": f"获取持仓失败: {str(e)}"}

    def test_connectivity(self) -> bool:
        """测试连接"""
        try:
            if not self.futures_client:
                return False

            # 使用交易所信息API测试连接
            response = self.futures_client.rest_api.exchange_information()
            return response is not None

        except Exception:
            return False

    def is_available(self) -> bool:
        """检查交易客户端是否可用"""
        return self.futures_client is not None and self.test_connectivity()
