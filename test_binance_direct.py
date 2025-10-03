# test_binance_direct.py - 测试币安USDT永续合约SDK

import logging
from binance_common.configuration import ConfigurationRestAPI
from binance_common.constants import DERIVATIVES_TRADING_USDS_FUTURES_REST_API_PROD_URL
from binance_sdk_derivatives_trading_usds_futures.derivatives_trading_usds_futures import DerivativesTradingUsdsFutures

# 你的API密钥（从.env读取）
API_KEY = "tRmMXUJiVY81MReL0XPZp2oXya8i7JG75bvpbVIRc5KN0R6ilpJh11F2QzL9rYob"
API_SECRET = "WeCzJyncm5RHueOWYUCNN3d4RRCcsc0ZU1LglkehuLH8RNVqmJT6pWNRJ9GPPk5z"

logging.basicConfig(level=logging.INFO)

def test_usdt_futures():
    """测试USDT永续合约SDK"""
    print("=" * 70)
    print("测试USDT永续合约SDK")
    print("=" * 70)

    try:
        # 创建配置
        configuration = ConfigurationRestAPI(
            api_key=API_KEY,
            api_secret=API_SECRET,
            base_path=DERIVATIVES_TRADING_USDS_FUTURES_REST_API_PROD_URL
        )

        # 创建客户端
        client = DerivativesTradingUsdsFutures(config_rest_api=configuration)

        print(f"\n[OK] USDT永续合约客户端初始化成功")
        print(f"API Key: {API_KEY[:30]}...")
        print(f"Base URL: {DERIVATIVES_TRADING_USDS_FUTURES_REST_API_PROD_URL}")

        # 测试1: 获取账户信息
        print("\n[测试1] 获取账户信息 - account_information_v3()")
        print("-" * 70)
        try:
            response = client.rest_api.account_information_v3()
            data = response.data()

            print(f"[SUCCESS] 账户信息获取成功!")
            print(f"\n完整响应数据:")
            print(data)

            print(f"\n  总余额: ${data.totalWalletBalance if hasattr(data, 'totalWalletBalance') else 'N/A'}")
            print(f"  可用余额: ${data.availableBalance if hasattr(data, 'availableBalance') else 'N/A'}")
            print(f"  未实现盈亏: ${data.totalUnrealizedProfit if hasattr(data, 'totalUnrealizedProfit') else 'N/A'}")

            # 显示资产
            if hasattr(data, 'assets'):
                print(f"\n  账户资产 (共{len(data.assets)}个):")
                for asset in data.assets:
                    print(f"    资产数据: {asset}")
                    if hasattr(asset, 'walletBalance'):
                        wb = float(asset.walletBalance)
                        if wb > 0:
                            print(f"    >> {asset.asset if hasattr(asset, 'asset') else 'N/A'}: "
                                  f"余额={asset.walletBalance}, "
                                  f"可用={asset.availableBalance if hasattr(asset, 'availableBalance') else 0}")

        except Exception as e:
            print(f"[FAILED] {e}")
            import traceback
            traceback.print_exc()

        # 测试1.5: 获取账户余额
        print("\n[测试1.5] 获取账户余额 - futures_account_balance_v3()")
        print("-" * 70)
        try:
            response = client.rest_api.futures_account_balance_v3()
            data = response.data()

            print(f"[SUCCESS] 账户余额获取成功!")
            print(f"\n完整响应数据:")
            print(data)

            if data:
                print(f"\n余额列表 (共{len(data)}个):")
                for balance in data:
                    print(f"  余额数据: {balance}")
                    if hasattr(balance, 'balance'):
                        bal = float(balance.balance)
                        if bal > 0:
                            print(f"  >> {balance.asset if hasattr(balance, 'asset') else 'N/A'}: "
                                  f"余额={balance.balance}, "
                                  f"可用={balance.availableBalance if hasattr(balance, 'availableBalance') else 'N/A'}")

        except Exception as e:
            print(f"[FAILED] {e}")
            import traceback
            traceback.print_exc()

        # 测试2: 获取持仓信息
        print("\n[测试2] 获取持仓信息 - position_information_v3()")
        print("-" * 70)
        try:
            response = client.rest_api.position_information_v3()
            data = response.data()

            print(f"[SUCCESS] 持仓信息获取成功!")
            print(f"\n完整响应数据 (共{len(data)}条):")

            # 显示所有持仓（包括0持仓）
            for i, pos in enumerate(data[:10], 1):  # 显示前10个
                print(f"\n  [{i}] 持仓数据: {pos}")

            # 筛选有持仓的
            active_positions = [pos for pos in data if hasattr(pos, 'positionAmt') and float(pos.positionAmt) != 0]

            if active_positions:
                print(f"\n  ===== 当前活跃持仓: {len(active_positions)}个 =====")
                for pos in active_positions:
                    print(f"\n  交易对: {pos.symbol if hasattr(pos, 'symbol') else 'N/A'}")
                    print(f"    持仓方向: {'多头' if float(pos.positionAmt) > 0 else '空头'}")
                    print(f"    持仓数量: {abs(float(pos.positionAmt)) if hasattr(pos, 'positionAmt') else 0}")
                    print(f"    开仓价格: ${pos.entryPrice if hasattr(pos, 'entryPrice') else 'N/A'}")
                    print(f"    标记价格: ${pos.markPrice if hasattr(pos, 'markPrice') else 'N/A'}")
                    print(f"    未实现盈亏: ${pos.unRealizedProfit if hasattr(pos, 'unRealizedProfit') else 'N/A'}")
            else:
                print("\n  当前无活跃持仓（所有positionAmt都是0）")

        except Exception as e:
            print(f"[FAILED] {e}")
            import traceback
            traceback.print_exc()

        # 测试3: 获取交易所信息
        print("\n[测试3] 获取交易所信息 - exchange_information()")
        print("-" * 70)
        try:
            response = client.rest_api.exchange_information()
            data = response.data()

            print(f"[SUCCESS] 交易所信息获取成功!")
            print(f"  时区: {data.timezone if hasattr(data, 'timezone') else 'N/A'}")
            print(f"  服务器时间: {data.serverTime if hasattr(data, 'serverTime') else 'N/A'}")

            if hasattr(data, 'symbols'):
                print(f"  可交易对数量: {len(data.symbols)}")

        except Exception as e:
            print(f"[FAILED] {e}")

    except Exception as e:
        print(f"\n[ERROR] 初始化失败: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 70)
    print("测试完成")
    print("=" * 70)

if __name__ == '__main__':
    test_usdt_futures()


def test_wallet_sdk():
    """测试币安钱包SDK"""
    print("=" * 70)
    print("测试币安钱包SDK")
    print("=" * 70)

    try:
        # 创建配置
        configuration = ConfigurationRestAPI(
            api_key=API_KEY,
            api_secret=API_SECRET,
            base_path=WALLET_REST_API_PROD_URL
        )

        # 创建钱包客户端
        client = Wallet(config_rest_api=configuration)

        print(f"\n[OK] 钱包客户端初始化成功")
        print(f"API Key: {API_KEY[:30]}...")
        print(f"Base URL: {WALLET_REST_API_PROD_URL}")

        # 测试1: 获取账户信息
        print("\n[测试1] 获取账户信息 - account_info()")
        print("-" * 70)
        try:
            response = client.rest_api.account_info()
            data: AccountInfoResponse = response.data()

            print(f"[SUCCESS] 账户信息获取成功!")
            print(f"  账户类型: {data.account_type if hasattr(data, 'account_type') else 'N/A'}")
            print(f"  可交易: {data.can_trade if hasattr(data, 'can_trade') else 'N/A'}")
            print(f"  响应数据: {data}")

        except Exception as e:
            print(f"[FAILED] {e}")
            import traceback
            traceback.print_exc()

        # 测试2: 获取系统状态
        print("\n[测试2] 获取系统状态 - system_status()")
        print("-" * 70)
        try:
            response = client.rest_api.system_status()
            data = response.data()

            print(f"[SUCCESS] 系统状态: {data}")

        except Exception as e:
            print(f"[FAILED] {e}")

        # 测试3: 获取账户快照
        print("\n[测试3] 获取账户快照 - account_snapshot()")
        print("-" * 70)
        try:
            response = client.rest_api.account_snapshot(type="SPOT")
            data = response.data()

            print(f"[SUCCESS] 快照数据: {data}")

        except Exception as e:
            print(f"[FAILED] {e}")

    except Exception as e:
        print(f"\n[ERROR] 初始化失败: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 70)
    print("测试完成")
    print("=" * 70)

if __name__ == '__main__':
    test_wallet_sdk()

