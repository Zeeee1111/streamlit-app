import streamlit as st
import pandas as pd
from datetime import date
import io

st.set_page_config(page_title="TB 個案管理系統", layout="wide")
st.title("🏥 TB 個案管理與風險評估系統")

# --- 初始化資料庫 ---
if 'db' not in st.session_state:
    st.session_state.db = pd.DataFrame(columns=[
        "病歷號", "姓名", "開始治療日", "應完成天數", "已服藥天數", "漏服天數", "最近回診日", "是否缺診"
    ])

# --- 左側：資料輸入 ---
with st.sidebar:
    st.header("新增個案資料")
    with st.form("input_form", clear_on_submit=True):
        id_num = st.text_input("病歷號")
        name = st.text_input("姓名")
        start_date = st.date_input("開始治療日", value=date.today())
        total_days = st.number_input("應完成天數", min_value=1, value=180)
        taken_days = st.number_input("已服藥天數", min_value=0, value=0)
        missed_days = st.number_input("漏服天數", min_value=0, value=0)
        last_visit = st.date_input("最近回診日", value=date.today())
        is_absent = st.selectbox("是否缺診", options=[0, 1], format_func=lambda x: "是 (1)" if x==1 else "否 (0)")
        
        submitted = st.form_submit_button("➕ 新增至清單")
        
        if submitted and id_num and name:
            new_data = {
                "病歷號": id_num, "姓名": name, "開始治療日": start_date,
                "應完成天數": total_days, "已服藥天數": taken_days,
                "漏服天數": missed_days, "最近回診日": last_visit, "是否缺診": is_absent
            }
            st.session_state.db = pd.concat([st.session_state.db, pd.DataFrame([new_data])], ignore_index=True)
            st.success(f"已加入：{name}")
        elif submitted:
            st.error("請填寫病歷號與姓名")

# --- 右側：管理報表 ---
st.header("📊 個案風險報表")

if not st.session_state.db.empty:
    df_display = st.session_state.db.copy()

    # 計算邏輯
    df_display["完成率"] = (df_display["已服藥天數"] / df_display["應完成天數"]).map(lambda x: f"{x:.1%}")
    
    def calculate_risk(row):
        score = 0
        if row["是否缺診"] == 1: score += 2
        if row["漏服天數"] > 5: score += 2
        if row["已服藥天數"] < 30: score += 1
        return score

    df_display["風險分數"] = df_display.apply(calculate_risk, axis=1)
    df_display["風險等級"] = df_display["風險分數"].apply(lambda s: "🔴 高" if s>=4 else ("🟡 中" if s>=2 else "🟢 低"))

    # --- 顯示表格與刪除按鈕 ---
    # 我們用欄位來並排顯示資料與刪除按鈕
    for index, row in df_display.iterrows():
        # 重新分配比例：[序號, 姓名/病歷號, 風險, 完成率, 詳細數值區(最寬), 刪除按鈕]
        cols = st.columns([0.5, 1.5, 1, 1, 3.5, 1]) 
        
        cols[0].write(f"#{index+1}")
        cols[1].write(f"**{row['姓名']}** ({row['病歷號']})")
        cols[2].write(f"風險: {row['風險等級']}")
        cols[3].write(f"完成率: {row['完成率']}")
        
        # 處理缺診數值轉換為文字
        is_absent_str = "是" if row["是否缺診"] == 1 else "否"
        
        # 在右側輸出你指定的 6 個數值 (使用 caption 可以讓字體稍小，版面更乾淨)
        cols[4].caption(f"📅 開始: {row['開始治療日']} | 🏥 回診: {row['最近回診日']} | ⚠️ 缺診: {is_absent_str}")
        cols[4].caption(f"💊 應完: {row['應完成天數']}天 | ✅ 已服: {row['已服藥天數']}天 | ❌ 漏服: {row['漏服天數']}天")
        
        # 刪除單筆的按鈕
        if cols[5].button("🗑️ 刪除", key=f"del_{index}"):
            st.session_state.db = st.session_state.db.drop(index).reset_index(drop=True)
            st.rerun()
            
        st.divider()

    # --- 匯出功能 ---
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_display.to_excel(writer, index=False, sheet_name='Sheet1')
    
    st.download_button(
        label="📥 下載 Excel 報表",
        data=output.getvalue(),
        file_name=f"TB_Report_{date.today()}.xlsx",
        mime="application/vnd.ms-excel"
    )
else:
    st.info("目前尚無資料，請由左側手動輸入。")