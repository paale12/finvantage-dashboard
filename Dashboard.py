import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import yfinance as yf
import time

# ==========================================
# PAGE CONFIG
# ==========================================
st.set_page_config(
    page_title="FinVantage AI Terminal",
    page_icon="📊",
    layout="wide"
)

# ==========================================
# UI STYLE
# ==========================================
st.markdown("""
<style>
div[data-testid="stMetric"] {
    background-color: rgba(28, 131, 225, 0.05);
    padding: 15px;
    border-radius: 10px;
}
</style>
""", unsafe_allow_html=True)

# ==========================================
# CLEAN FUNCTION
# ==========================================
def clean_dataframe(df):
    df = df.loc[:, ~df.columns.duplicated()]
    df = df.reset_index(drop=True)
    return df

# ==========================================
# FORMAT FUNCTION (₹ CRORES)
# ==========================================
def format_inr(value):
    try:
        return f"₹{value/1e7:,.2f} Cr"
    except:
        return value

# ==========================================
# LIVE PRICE
# ==========================================
def get_live_price(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        return {
            "price": info.get("currentPrice", 0),
            "prev": info.get("previousClose", 0),
            "name": info.get("longName", ticker),
            "symbol": info.get("symbol", ticker)
        }
    except:
        return {"price": 0, "prev": 0, "name": ticker, "symbol": ticker}

# ==========================================
# INCOME STATEMENT
# ==========================================
def get_income_statement(ticker):
    try:
        df = yf.Ticker(ticker).financials.T
        if df.empty:
            return None

        df["Year"] = df.index.year
        df = df.groupby("Year").first().reset_index()

        df = df.rename(columns={
            "Total Revenue": "Revenue",
            "Operating Income": "EBIT",
            "Net Income": "Net Profit"
        })

        df["Expenses"] = df["Revenue"] - df["Net Profit"]

        return clean_dataframe(df)
    except:
        return None

# ==========================================
# BALANCE SHEET
# ==========================================
def get_balance_sheet(ticker):
    try:
        df = yf.Ticker(ticker).balance_sheet.T
        if df.empty:
            return None

        df["Year"] = df.index.year
        df = df.groupby("Year").first().reset_index()

        return clean_dataframe(df)
    except:
        return None

# ==========================================
# CASH FLOW
# ==========================================
def get_cashflow(ticker):
    try:
        df = yf.Ticker(ticker).cashflow.T
        if df.empty:
            return None

        df["Year"] = df.index.year
        df = df.groupby("Year").first().reset_index()

        return clean_dataframe(df)
    except:
        return None

# ==========================================
# METRICS
# ==========================================
def process_metrics(df):
    df["Profit Margin (%)"] = (df["Net Profit"] / df["Revenue"]) * 100
    df["Expense Ratio (%)"] = (df["Expenses"] / df["Revenue"]) * 100
    df["YoY Growth (%)"] = df["Revenue"].pct_change() * 100
    return df

# ==========================================
# SIDEBAR
# ==========================================
with st.sidebar:
    st.title("📊 FinVantage Pro")
    ticker = st.text_input("🔍 Enter Ticker", "TCS.NS")

# ==========================================
# LOAD DATA
# ==========================================
with st.spinner("Fetching data..."):
    info = get_live_price(ticker)

    income_df = get_income_statement(ticker)
    balance_df = get_balance_sheet(ticker)
    cash_df = get_cashflow(ticker)

    if income_df is not None:
        income_df = process_metrics(income_df)

    time.sleep(0.5)

# ==========================================
# HEADER
# ==========================================
st.title(f"📈 {info['name']}")
st.caption(f"Ticker: {info['symbol']}")

# ==========================================
# METRICS
# ==========================================
c1, c2, c3, c4 = st.columns(4)

price_change = info["price"] - info["prev"]

c1.metric("Stock Price", f"₹{info['price']}", f"{price_change:.2f}")

if income_df is not None:
    latest = income_df.iloc[-1]

    c2.metric("Profit Margin", f"{latest['Profit Margin (%)']:.2f}%")
    c3.metric("Expense Ratio", f"{latest['Expense Ratio (%)']:.2f}%")
    c4.metric("YoY Growth", f"{latest['YoY Growth (%)']:.2f}%")
else:
    c2.metric("Profit Margin", "N/A")
    c3.metric("Expense Ratio", "N/A")
    c4.metric("YoY Growth", "N/A")

st.divider()

# ==========================================
# TABS
# ==========================================
tabs = st.tabs([
    "📊 Overview",
    "📈 Income Statement",
    "🏦 Balance Sheet",
    "💰 Cash Flow",
    "📉 Shareholding"
])

# ==========================================
# OVERVIEW (FIXED GRAPH)
# ==========================================
with tabs[0]:
    if income_df is not None:
        fig = go.Figure()

        fig.add_trace(go.Bar(
            x=income_df["Year"],
            y=income_df["Revenue"] / 1e7,
            name="Revenue"
        ))

        fig.add_trace(go.Bar(
            x=income_df["Year"],
            y=income_df["Net Profit"] / 1e7,
            name="Profit"
        ))

        fig.update_layout(yaxis_title="₹ Crores")

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No financial overview available")

# ==========================================
# INCOME TABLE (FORMATTED)
# ==========================================
with tabs[1]:
    st.subheader("Income Statement")
    if income_df is not None:
        df_display = income_df.copy()

        for col in df_display.columns:
            if col not in ["Year", "Profit Margin (%)", "Expense Ratio (%)", "YoY Growth (%)"]:
                df_display[col] = df_display[col].apply(format_inr)

        st.dataframe(df_display)
    else:
        st.warning("No Income Data")

# ==========================================
# BALANCE
# ==========================================
with tabs[2]:
    st.subheader("Balance Sheet")
    if balance_df is not None:
        df_display = balance_df.copy()

        for col in df_display.columns:
            if col != "Year":
                df_display[col] = df_display[col].apply(format_inr)

        st.dataframe(df_display)
    else:
        st.warning("No Balance Sheet Data")

# ==========================================
# CASH FLOW
# ==========================================
with tabs[3]:
    st.subheader("Cash Flow")
    if cash_df is not None:
        df_display = cash_df.copy()

        for col in df_display.columns:
            if col != "Year":
                df_display[col] = df_display[col].apply(format_inr)

        st.dataframe(df_display)
    else:
        st.warning("No Cash Flow Data")

# ==========================================
# SHAREHOLDING
# ==========================================
with tabs[4]:
    st.subheader("Shareholding Pattern")
    st.info("⚠️ Not available in free API")