from logging_manager import logger
from fastapi import FastAPI


import ccxt
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# 로깅 설정 초기화


app = FastAPI()



@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    logger.debug("who name is %s", name)
    return {"message": f"Hello {name}"}


def fetch_all_historical_data(exchange, symbol="KRW-DOGE", timeframe="1m", total_limit=1000, start_time=None):
    """
    업비트에서 반복 요청으로 많은 과거 데이터를 가져오는 함수 (요청 시점 포함)
    :param exchange: CCXT 거래소 객체
    :param symbol: 거래할 코인 (기본값: KRW-DOGE)
    :param timeframe: 시간 간격 (기본값: 1분봉)
    :param total_limit: 가져올 총 데이터 개수
    :param start_time: 가져올 데이터의 시작 시점 (ISO 8601 형식, UTC 기준)
    :return: OHLCV 데이터를 담은 Pandas DataFrame
    """
    limit_per_request = 200  # 업비트 API의 단일 요청 최대 제한
    data = []
    to_time = pd.Timestamp(start_time).tz_convert('UTC').strftime('%Y-%m-%dT%H:%M:%SZ') if start_time else None

    while total_limit > 0:
        # 한 번에 가져올 데이터 개수 설정 (최대 limit_per_request까지)
        limit = min(limit_per_request, total_limit)

        # API 요청
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit, params={"to": to_time})

        if not ohlcv:  # 데이터가 없으면 중단
            break

        # 데이터 저장
        data.extend(ohlcv)

        # `to` 파라미터 갱신 (가장 오래된 데이터 이전으로 요청)
        to_time = pd.Timestamp(ohlcv[0][0], unit='ms').strftime('%Y-%m-%dT%H:%M:%SZ')

        # 남은 데이터 양 감소
        total_limit -= len(ohlcv)

    # DataFrame으로 변환
    df = pd.DataFrame(data, columns=["timestamp", "open", "high", "low", "close", "volume"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    df.set_index("timestamp", inplace=True)

    return df


def apply_strategy(df, short_window=5, long_window=15):
    """
    이동 평균 교차 전략 적용 (단기/장기 이동 평균)
    :param df: OHLCV 데이터가 포함된 DataFrame
    :param short_window: 단기 이동 평균 계산을 위한 기간
    :param long_window: 장기 이동 평균 계산을 위한 기간
    :return: 매수/매도 신호와 포지션을 추가한 DataFrame
    """
    # 단기 이동 평균 계산
    df["short_ma"] = df["close"].rolling(window=short_window).mean()
    # 장기 이동 평균 계산
    df["long_ma"] = df["close"].rolling(window=long_window).mean()

    # 매수/매도 신호 생성 (1: 매수, -1: 매도)
    df["signal"] = 0
    df.loc[df["short_ma"] > df["long_ma"], "signal"] = 1
    df.loc[df["short_ma"] <= df["long_ma"], "signal"] = -1

    # 이전 신호를 기반으로 포지션 설정 (1: 보유, 0: 미보유)
    df["position"] = df["signal"].shift(1).fillna(0)
    return df


def backtest(df, initial_balance=1_000_000):
    """
    전략에 따른 백테스팅 수행
    :param df: 매수/매도 신호와 포지션 데이터가 포함된 DataFrame
    :param initial_balance: 초기 자본금 (기본값: 1,000,000원)
    :return: 포트폴리오 가치가 추가된 DataFrame
    """
    balance = initial_balance  # 초기 자본금
    position = 0  # 초기 포지션 (코인 보유량)
    df["portfolio"] = balance  # 초기 포트폴리오 가치 설정

    logger.info("백테스팅 시작: 초기 자본금 = %s KRW", initial_balance)

    for i in range(1, len(df)):
        current_price = df.iloc[i]["close"]  # 현재 가격
        signal = df.iloc[i]["signal"]  # 현재 매수/매도 신호

        # 매수 신호
        if signal == 1 and position == 0:
            position = balance / current_price  # 잔고로 코인 구매
            balance = 0  # 현금 잔고 소진
            logger.info(
                "[%s] 매수: 가격 = %.2f KRW, 보유량 = %.6f 코인",
                df.index[i],
                current_price,
                position,
            )

        # 매도 신호
        elif signal == -1 and position > 0:
            balance = position * current_price  # 코인 매도 후 현금 확보
            logger.info(
                "[%s] 매도: 가격 = %.2f KRW, 잔고 = %.2f KRW",
                df.index[i],
                current_price,
                balance,
            )
            position = 0  # 코인 포지션 초기화

        # 포트폴리오 가치 업데이트
        df.iloc[i, df.columns.get_loc("portfolio")] = balance + (position * current_price)

    # 최종 상태 로그
    final_value = balance + (position * df.iloc[-1]["close"])
    logger.info("백테스팅 완료: 최종 포트폴리오 가치 = %.2f KRW", final_value)
    return df

@app.get("/backtest")
async def run_backtest():
    # CCXT를 이용한 거래소 초기화
    exchange = ccxt.upbit()

    # 현재 시간 기준으로 데이터 가져오기
    current_time = datetime.utcnow()  # UTC 시간
    to_time = current_time.isoformat() + "Z"  # ISO 8601 형식

    # 과거 데이터 가져오기
    df = fetch_all_historical_data(
        exchange,
        symbol="KRW-DOGE",
        timeframe="1m",
        total_limit=1000,
        start_time="2024-12-01T00:00:00Z"  # 요청 시작 시점
    )

    # 로그로 출력
    logger.info("Fetched Historical Data:")
    logger.info(df.head(10))  # 상위 10개 데이터 출력
    logger.info(f"Total rows fetched: {len(df)}")

    # 이동 평균 전략 적용
    df = apply_strategy(df, short_window=5, long_window=15)

    # 백테스팅 수행
    df = backtest(df)

    # 최종 포트폴리오 결과 반환
    initial_value = df["portfolio"].iloc[0]
    final_value = df["portfolio"].iloc[-1]
    returns = (final_value - initial_value) / initial_value * 100

    return {
        "initial_portfolio_value": f"{initial_value:.2f} KRW",
        "final_portfolio_value": f"{final_value:.2f} KRW",
        "total_returns": f"{returns:.2f}%"
    }