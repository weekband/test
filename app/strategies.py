import pandas as pd

def apply_strategy_moving_average(df: pd.DataFrame, short_window=5, long_window=15):
    """
    이동 평균 교차 전략 (단기/장기 이동 평균)
    :param df: OHLCV 데이터가 포함된 DataFrame
    :param short_window: 단기 이동 평균 기간
    :param long_window: 장기 이동 평균 기간
    :return: 매수/매도 신호와 포지션을 추가한 DataFrame
    """
    df["short_ma"] = df["close"].rolling(window=short_window).mean()
    df["long_ma"] = df["close"].rolling(window=long_window).mean()

    df["signal"] = 0
    df.loc[df["short_ma"] > df["long_ma"], "signal"] = 1  # 매수
    df.loc[df["short_ma"] <= df["long_ma"], "signal"] = -1  # 매도

    df["position"] = df["signal"].shift(1).fillna(0)
    return df

def apply_strategy_rsi_volatility(df: pd.DataFrame, rsi_period=14, volatility_threshold=0.02):
    """
    RSI와 변동성을 활용한 전략
    :param df: OHLCV 데이터가 포함된 DataFrame
    :param rsi_period: RSI 계산에 사용할 기간
    :param volatility_threshold: 변동성 임계값
    :return: 매수/매도 신호와 포지션을 추가한 DataFrame
    """
    try:
        # 데이터가 충분한지 확인
        if len(df) < rsi_period:
            raise ValueError("데이터가 RSI 계산에 필요한 기간보다 적습니다.")

        # RSI 계산
        delta = df["close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=rsi_period).mean()

        # division by zero 방지
        rs = gain / (loss.replace(0, 1))  # loss가 0일 경우 1로 대체
        df["rsi"] = 100 - (100 / (1 + rs))

        # 변동성 계산
        df["volatility"] = (df["high"] - df["low"]) / df["low"].replace(0, 1)  # low가 0일 경우 1로 대체

        # 매수/매도 신호 생성
        df["signal"] = 0
        df.loc[(df["rsi"] < 30) & (df["volatility"] > volatility_threshold), "signal"] = 1  # 매수
        df.loc[(df["rsi"] > 70), "signal"] = -1  # 매도

        # 이전 신호를 기반으로 포지션 설정 (1: 보유, 0: 미보유)
        df["position"] = df["signal"].shift(1).fillna(0)

    except Exception as e:
        print(f"Error in applying strategy: {e}")
        raise

    return df