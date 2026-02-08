import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta

# アプリの設定（スマホで見やすいよう中央寄せ）
st.set_page_config(page_title="適度な飲酒ログ", layout="centered")

st.title("🍹 飲酒ログ & 分解予測")

# Googleスプレッドシートへの接続
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(ttl="0s")
except:
    st.error("スプレッドシートへの接続設定が必要です。")
    df = pd.DataFrame(columns=["date", "drink_type", "amount", "alcohol_g"])

# --- 入力セクション ---
with st.container():
    st.subheader("📝 今日の記録")
    
    col1, col2 = st.columns(2)
    with col1:
        date_input = st.date_input("飲酒日", datetime.now())
    with col2:
        weight = st.number_input("体重 (kg)", min_value=30, value=65)

    drink_options = {
        "ビール (5%)": 5,
        "ワイン (12%)": 12,
        "泡盛 (30%)": 30,
        "ウイスキー (40%)": 40,
        "ウイスキー濃いめ (50%)": 50
    }
    drink_type = st.radio("お酒の種類", list(drink_options.keys()), horizontal=True)
    amount = st.select_slider("飲酒量 (ml)", options=[0, 100, 180, 350, 500, 750, 1000], value=350)

    # 計算ロジック
    abv = drink_options[drink_type]
    pure_alcohol = amount * (abv / 100) * 0.8
    decomp_time = pure_alcohol / (weight * 0.1)
    
    if st.button("🚀 データを保存する", use_container_width=True, type="primary"):
        new_data = pd.DataFrame([{
            "date": date_input.strftime('%Y-%m-%d'),
            "drink_type": drink_type,
            "amount": amount,
            "alcohol_g": pure_alcohol
        }])
        updated_df = pd.concat([df, new_data], ignore_index=True)
        conn.update(data=updated_df)
        st.success("スプレッドシートに保存しました！")
        st.balloons()

# --- 分析・分解時間表示 ---
st.divider()
st.subheader("⏱️ アルコール分解予測")
c1, c2 = st.columns(2)
c1.metric("純アルコール", f"{pure_alcohol:.1f} g")
c2.metric("分解時間", f"{decomp_time:.1f} h")

finish_time = (datetime.now() + timedelta(hours=decomp_time)).strftime('%H:%M')
st.info(f"💡 分解完了目安： **{finish_time}** 頃")

# --- 集計セクション ---
st.divider()
st.subheader("📊 飲酒ログ集計")

if not df.empty:
    df['date'] = pd.to_datetime(df['date'])
    tab1, tab2, tab3 = st.tabs(["日別", "週別", "月別"])
    
    with tab1:
        daily = df.groupby('date')['alcohol_g'].sum().reset_index()
        st.bar_chart(daily, x='date', y='alcohol_g')
    
    with tab2:
        df['week'] = df['date'].dt.to_period('W').apply(lambda r: r.start_time)
        weekly = df.groupby('week')['alcohol_g'].sum().reset_index()