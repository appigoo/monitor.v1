import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

# 設定頁面佈局
st.set_page_config(page_title="GS Quant 實時市場監控", layout="wide")

st.title("高盛風格：量化交易實時市場監控終端")
st.markdown("---")

# 側邊欄：參數設定
st.sidebar.header("監控參數設定")
tickers_input = st.sidebar.text_input("輸入股票代碼 (以逗號分隔)", "AAPL, MSFT, GOOGL, NVDA, SPY")
tickers = [t.strip().upper() for t in tickers_input.split(",")]

timeframe = st.sidebar.selectbox("時間範圍", ["1個月", "3個月", "6個月", "1年"])
days_dict = {"1個月": 30, "3個月": 90, "6個月": 180, "1年": 365}
start_date = datetime.now() - timedelta(days=days_dict[timeframe])

# 抓取資料函數 (使用緩存優化效能)
@st.cache_data(ttl=300) # 每 5 分鐘刷新一次
def load_data(ticker, start, end):
    data = yf.download(ticker, start=start, end=end)
    return data

if not tickers_input:
    st.warning("請輸入至少一個股票代碼。")
else:
    # 建立多欄位佈局
    cols = st.columns(len(tickers) if len(tickers) <= 3 else 3)
    
    for i, ticker in enumerate(tickers):
        try:
            df = load_data(ticker, start_date, datetime.now())
            if df.empty:
                continue
                
            # 計算簡單移動平均
            df['SMA_20'] = df['Close'].rolling(window=20).mean()
            df['SMA_50'] = df['Close'].rolling(window=50).mean()
            
            # 獲取最新價格與變動
            current_price = float(df['Close'].iloc[-1])
            prev_price = float(df['Close'].iloc[-2])
            pct_change = ((current_price - prev_price) / prev_price) * 100
            
            # 在欄位中顯示指標
            col_idx = i % 3
            with cols[col_idx]:
                st.subheader(f"📈 {ticker}")
                st.metric(label="最新收盤價", value=f"${current_price:.2f}", delta=f"{pct_change:.2f}%")
                
                # 繪製 K 線圖 (Candlestick)
                fig = go.Figure(data=[go.Candlestick(x=df.index,
                                open=df['Open'],
                                high=df['High'],
                                low=df['Low'],
                                close=df['Close'],
                                name="K線")])
                
                # 加入移動平均線
                fig.add_trace(go.Scatter(x=df.index, y=df['SMA_20'], line=dict(color='orange', width=1), name='20日 SMA'))
                fig.add_trace(go.Scatter(x=df.index, y=df['SMA_50'], line=dict(color='blue', width=1), name='50日 SMA'))
                
                # 圖表美化 (高盛暗黑終端風格)
                fig.update_layout(
                    margin=dict(l=20, r=20, t=20, b=20),
                    height=300,
                    plot_bgcolor='rgba(17, 17, 17, 1)',
                    paper_bgcolor='rgba(17, 17, 17, 1)',
                    font=dict(color='white'),
                    xaxis_rangeslider_visible=False
                )
                st.plotly_chart(fig, use_container_width=True)
                
        except Exception as e:
            st.error(f"無法載入 {ticker} 的資料: {e}")

st.markdown("---")
st.caption("機密資料 (Confidential) - 僅供高盛內部量化團隊參考。市場數據延遲可能達 15 分鐘。")
