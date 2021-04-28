import time
import pyupbit
import datetime

access = "VaboE9FgOnkuxVEvZCgiMhKQ7gncWeqNiC9eS9Jx"
secret = "mE27o3lN9zaf3v1HKzG05c8awGBl0xIkgxY5A6xN"

def get_target_price(ticker, k):
    """변동성 돌파 전략으로 매수 목표가 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=2)
    target_price = df.iloc[0]['close'] + (df.iloc[0]['high'] - df.iloc[0]['low']) * k
    return target_price

def get_start_time(ticker,iv):
    """시작 시간 조회"""
    df = pyupbit.get_ohlcv(ticker, interval=iv, count=1)
    start_time = df.index[0]
    return start_time

# def get_MoveAverage(ticker,d):
#     """5,10 이동 평균선 조회"""
#     df = pyupbit.get_ohlcv(ticker, interval="minute240", count=d)
#     ma = df['open'].rolling(d).mean().iloc[-1]
#     return ma

def is_UpLine(ticker,d,iv):
    """5,10 이동 평균선 조회"""
    df = pyupbit.get_ohlcv(ticker, interval=iv, count=d)
    lastOpenPrice = df.iloc[d-1]['open']
    ma = df['open'].rolling(d).mean().iloc[-1]
    if lastOpenPrice > ma :
        return True
    else :
        return False
    
# def get_MaMid(ticker,d,iv):
#     """5,10 이동 평균선 조회. open,close의 중간을 이동평균 계산하자."""
#     df = pyupbit.get_ohlcv(ticker, interval=iv, count=d)
#     df['mid'] = (df['close'] + df['open']) / 2
#     ma = df['mid'].rolling(d).mean().iloc[-1]
#     return ma
    
def get_MaOpen(ticker,d,iv) :
    """open가 이평선"""
    df = pyupbit.get_ohlcv(ticker, interval=iv, count=d)    
    ma = df['open'].rolling(d).mean().iloc[-1]
    return ma


def get_balance(ticker):
    """잔고 조회"""
    balances = upbit.get_balances()
    for b in balances:
        if b['currency'] == ticker:
            if b['balance'] is not None:
                return float(b['balance'])
            else:
                return 0
            
def get_avg_buy_price(ticker):
    """매수평균가 조회"""
    balances = upbit.get_balances()
    for b in balances:
        #print(b)
        if b['currency'] == ticker:
            if b['avg_buy_price'] is not None:
                return float(b['avg_buy_price'])
            else:
                return 0

def get_current_price(ticker):
    """현재가 조회"""
    return pyupbit.get_orderbook(tickers=ticker)[0]["orderbook_units"][0]["ask_price"]

def check_DownUp(ticker):
    """최근 3분봉 3개를 가져와서 하락->상승 전환하는지 체크"""
    df = pyupbit.get_ohlcv(ticker, interval="minute3", count=3)
    gradient_price = df.iloc[1]['close'] - df.iloc[0]['close'] 
    if gradient_price > 0 :
        return True
    else :
        return False


def check_UpDown(ticker):
    """최근 3분봉 3개를 가져와서 상승->하락 전환하는지 체크"""
    df = pyupbit.get_ohlcv(ticker, interval="minute3", count=3)
    gradient_price = df.iloc[1]['close'] - df.iloc[0]['close'] 
    if gradient_price < 0 :
        return True
    else :
        return False

# def get_min_averagesize(ticker):
#     """최근 1분봉 60개를 가져와서 평균 변동폭계산"""
#     df = pyupbit.get_ohlcv(ticker, interval="minute1", count=60)
#     df['range'] = (df['high'] - df['low'])
#     return df['range'].mean()

def check_UpLine240():
    #240분봉 5,10 이동평균선 체크.
    isOkLine5 = is_UpLine(ticker,5,"minute240")
    isOkLine10 = is_UpLine(ticker,10,"minute240")
    if isOkLine5 and isOkLine10 :
        return True
    else :
        return False
    

    

#주요 로직
#상승장, 하락장 에서의 매수 기준을 달리한다.
#매수,매도
#  1분봉으로 매수,매도 조건에 돌입후 색깔이(방향이) 바뀌면 매수, 매도한다.
#  매수는 매수조건 돌입후 계속 하락하다가 1분봉 방향(색깔) 바뀌면 매수.
#  매도는 매도조건 돌입후 계속 상승하다가 1분봉 방향(색깔) 바뀌면 매도.
#상승장
#  상승장은 240분봉 5,10이평선보다 당일 시가가 위에 있는 경우로 판단. 
#  매수. 지속적으로 1분봉 10이평선계산하고 밑에서 매수, 이평선위에서 매도
#  매수추가. 동일
#  매도. 평균매수가 보다 0.1% 이상 상승하면 매도조건 돌입, 전체의 50% 매도. 계속반복.
#  일분봉 마감하고 나머지 잔액은 전량 매도한다
#하락장
#  하락장은 5일,10일선 보다 당일 시가가 하나라도 낮은 경우로 판단.
#  매수 안하는것을 원칙으로 하되, 과도한 일시적 하락 지점을 순간 매수
#  매수추가. 최종매수가보다 더 아래로 과도한 일시적 하락시.
#  매도. 최종매수가보다 높으면 매도조건 돌입. 전량 매도.
#  과도한 일시적 하락. 1분봉 60개의 평균 변동폭의 3배이상 1분만에 하락시

# 로그인
upbit = pyupbit.Upbit(access, secret)
print("autotrade start")
#upbitticker
ticker = "KRW-XRP"
ticker_balance = "XRP"
#1회 최대 매매금액
MaxBuyPrice = 100000
#최종매수가, 최종매도가 기억.
buyFinalPrice = 0
#sellFinalPrice = 0

#240분봉으로 5,10 이동평균보다 동시에 위에서 스타트하는지-> 상승곡선인지.
isUpLine240 = check_UpLine240()

#3봉의 OPEN이평선 가격을 기억한다.
MaOpen1 = get_MaOpen(ticker,10,"minute3")
#매수평균가를 기억한다.
avg_buy_price = get_avg_buy_price(ticker_balance)

print("240분 상승장??: " + str(isUpLine240))

print("3분봉 오픈이평선: " + str(MaOpen1))
krw = get_balance("KRW")
print("krw 잔고: " + str(krw))
mabalance = get_balance(ticker_balance)
print("mabalance 잔고: " + str(mabalance))
buyFinalPrice = get_MaOpen(ticker,5,"minute240")
print("매수 저지선: " + str(buyFinalPrice))

# 자동매매 시작
while True:
    try:
        print("3분봉 이평선: " + str(MaOpen1))
        
        now = datetime.datetime.now()
        start_time = get_start_time(ticker,"minute240")
        end_time = start_time + datetime.timedelta(hours=4)
        # start_time = get_start_time(ticker,"minute3")
        # end_time = start_time + datetime.timedelta(minutes=3)
        avg_buy_price = get_avg_buy_price(ticker_balance)
        #240분(4시간) 을 주기로 시작과 끝을 체크한다.
        if start_time < now < end_time - datetime.timedelta(seconds=10):
            #상승장에서만 매수한다.
            current_price = get_current_price(ticker)
            print("현재가:" + str(current_price))
            print("매수 저지선: " + str(buyFinalPrice))
            #1분봉 20이평선 아래에서 구매 AND 240분봉 MID이평선 아래에서 구매
            MaOpen1 = get_MaOpen(ticker,10,"minute3")
            if isUpLine240 and current_price < MaOpen1 and current_price < buyFinalPrice :
                krw = get_balance("KRW")
                if krw is not None :
                    #최대 1만원까지만 매수. 추후에 금액을 올리자
                    if krw > MaxBuyPrice :
                        krw = MaxBuyPrice    
                    #원화가 최소 5000원 이상 있으면 매수로직 시행
                    if krw > 6000 :
                        if check_DownUp(ticker) :
                            upbit.buy_market_order(ticker, krw*0.9995)
                            print(krw)
                            print("======================= 매수: " + str(krw*0.9995))
                            buyFinalPrice = current_price * 0.99
                            
               
            #매도는 상승장,하락장 상관없이. 시작가 밑에서 매수했으므로, 매수평균가보다 1% 이상에서 매도.
            if current_price > avg_buy_price * 1.01 :
                mabalance = get_balance(ticker_balance)
                print("mabalance 잔고: " + str(mabalance))
                if mabalance is not None :
                    if (MaOpen1 * mabalance) > 6000:
                        if check_UpDown(ticker) :
                            upbit.sell_market_order(ticker, mabalance*0.9995)
                            print("========================== 매도매도: " + str(mabalance*0.9995))
                            buyFinalPrice = get_MaOpen(ticker,5,"minute240")
                        
           
        else:
            #240분마다 실행. 상승장인지,시작가 재체크 기억
                        
            isUpLine240 = check_UpLine240()
            
            print("240분 상승장??: " + str(isUpLine240))
            buyFinalPrice = get_MaOpen(ticker,5,"minute240")
            #240분(4시간)중 시간이 아침 5시대 종료 9시이면 전량 매도
            #btc 잔액이 있으면 전량 시장가매도
            if start_time.hour == 9 :
                mabalance = get_balance(ticker_balance)
                if mabalance is not None :
                    if (MaOpen1 * mabalance) > 6000:
                        upbit.sell_market_order(ticker, mabalance*0.9995)
                        print("9시잔량매도: " + str(mabalance*0.9995))
           
        time.sleep(10)
    except Exception as e:
        print(e)
        time.sleep(10)
        
        
