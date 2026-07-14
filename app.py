import streamlit as st
import pandas as pd
import io
import matplotlib.pyplot as plt
import platform

# --- 0. グラフの日本語フォント設定（文字化け対策） ---
system_name = platform.system()
if system_name == "Windows":
    plt.rcParams['font.family'] = ['Meiryo', 'Yu Gothic', 'MS Gothic']
elif system_name == "Darwin": # Mac
    plt.rcParams['font.family'] = ['Hiragino Sans', 'Hiragino Kaku Gothic ProN']
else: # Linux/Cloud
    plt.rcParams['font.family'] = ['sans-serif']
# マイナス記号が文字化けするのを防ぐ設定
plt.rcParams['axes.unicode_minus'] = False

# --- 1. ページの設定 ---
st.set_page_config(
    page_title="OpenFDTD S11 & Absorption Viewer",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. カスタムCSS（シンプル＆モダンなUIデザイン） ---
st.markdown("""
    <style>
    .block-container {
        padding-top: 2.0rem;
        padding-bottom: 3.0rem;
        max-width: 1060px !important;
    }
    h1 {
        font-size: 1.8rem !important;
        font-weight: 700 !important;
        color: #1E293B !important;
        margin-bottom: 0.2rem !important;
        letter-spacing: -0.02em;
    }
    p, .streamlit-expanderHeader {
        color: #475569 !important;
        font-size: 0.95rem !important;
    }
    [data-testid="stFileUploadDropzone"] {
        border: 1.5px dashed #CBD5E1 !important;
        border-radius: 12px !important;
        background-color: #F8FAFC !important;
        transition: all 0.2s ease-in-out;
    }
    [data-testid="stFileUploadDropzone"]:hover {
        border-color: #3B82F6 !important;
        background-color: #F1F5F9 !important;
    }
    .stDownloadButton > button, .stDownloadButton > button * {
        width: 100%;
        border-radius: 8px !important;
        background-color: #2563EB !important;
        color: #FFFFFF !important;
        font-size: 1.0rem !important;
        font-weight: 700 !important;
        border: none !important;
        padding: 0.65rem 1rem !important;
        box-shadow: 0 4px 10px rgba(37, 99, 235, 0.25) !important;
        transition: all 0.2s ease-in-out !important;
    }
    .stDownloadButton > button:hover {
        background-color: #1D4ED8 !important;
        box-shadow: 0 6px 14px rgba(37, 99, 235, 0.35) !important;
        transform: translateY(-1px);
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. ヘッダーセクション ---
st.title("S11 & 電波吸収率 ビューア")
st.write("解析結果のテキストファイル（`.txt`）を読み込み、S11および電波吸収率の同時グラフ化とExcel出力を行います。")

st.write("") # スペーサー

# --- 4. ファイルアップロード（カードレイアウト） ---
with st.container(border=True):
    uploaded_file = st.file_uploader("S11のテキストファイルを選択してください", type=["txt", "csv", "dat"], label_visibility="collapsed")

if uploaded_file is not None:
    try:
        # --- 5. データの読み込み＆吸収率計算 ---
        content = uploaded_file.getvalue().decode("utf-8")
        lines = content.split('\n')
        
        start_idx = 0
        for i, line in enumerate(lines):
            if "frequency[Hz]" in line:
                start_idx = i
                break
                
        clean_lines = [line.strip() for line in lines[start_idx:] if line.strip()]
        data_str = '\n'.join(clean_lines)
        
        df_raw = pd.read_csv(io.StringIO(data_str), sep=r'\s+')
        
        df = pd.DataFrame()
        df["周波数 [GHz]"] = pd.to_numeric(df_raw["frequency[Hz]"] / 1e9, errors='coerce')
        df["S11 [dB]"] = pd.to_numeric(df_raw["S11[dB]"], errors='coerce')
        
        # S11[dB] から吸収率[%]を自動計算
        df["吸収率 [%]"] = (1.0 - 10.0 ** (df["S11 [dB]"] / 10.0)) * 100.0
        
        # --- 6. 結果サマリー ---
        min_idx = df["S11 [dB]"].idxmin()
        min_freq = df.loc[min_idx, "周波数 [GHz]"]
        min_s11 = df.loc[min_idx, "S11 [dB]"]
        max_abs = df.loc[min_idx, "吸収率 [%]"]
        
        st.write("") # スペーサー
        
        col1, col2, col3 = st.columns(3)
        with col1:
            with st.container(border=True):
                st.metric(label="最深共振周波数", value=f"{min_freq:.3f} GHz")
        with col2:
            with st.container(border=True):
                st.metric(label="最小反射係数", value=f"{min_s11:.3f} dB")
        with col3:
            with st.container(border=True):
                st.metric(label="最大電波吸収率", value=f"{max_abs:.1f} %")
        
        # --- 7. グラフセクション（左右2軸の重ね合わせ・日本語表記対応） ---
        with st.container(border=True):
            st.markdown("### 📈 S11 & 吸収率 周波数特性 (2軸重ね合わせ表示)")
            
            # 1つのキャンバスを用意
            fig, ax1 = plt.subplots(figsize=(10, 5.0), dpi=150)
            fig.patch.set_facecolor('#FFFFFF')
            ax1.set_facecolor('#FFFFFF')
            
            # 横軸を共有した右側の2つ目のY軸を作成
            ax2 = ax1.twinx()
            
            # 【左軸】S11 [dB] グラフ (青色)
            line1 = ax1.plot(df["周波数 [GHz]"], df["S11 [dB]"], color="#1E3A8A", linewidth=2.2, alpha=0.95, label="反射係数 S11")
            ax1.set_xlim(1.0, 10.0)
            ax1.set_ylim(-30.0, 0.0)
            
            # 【変更点】日本語の軸ラベルに変更
            ax1.set_xlabel("周波数 [GHz]", fontsize=11, fontweight="600", color="#334155", labelpad=8)
            ax1.set_ylabel("反射係数 S11 [dB]", fontsize=11, fontweight="600", color="#1E3A8A", labelpad=8)
            ax1.tick_params(axis='y', colors="#1E3A8A", labelsize=10)
            ax1.tick_params(axis='x', colors="#64748B", labelsize=10)
            
            # 【右軸】吸収率 [%] グラフ (緑色)
            line2 = ax2.plot(df["周波数 [GHz]"], df["吸収率 [%]"], color="#059669", linewidth=2.2, alpha=0.95, label="電波吸収率")
            ax2.set_ylim(0.0, 100.0)
            
            # 【変更点】日本語の軸ラベルに変更
            ax2.set_ylabel("電波吸収率 [%]", fontsize=11, fontweight="600", color="#059669", labelpad=8)
            ax2.tick_params(axis='y', colors="#059669", labelsize=10)
            
            # グリッド（左軸基準で上品に表示）
            ax1.grid(True, linestyle=":", color="#CBD5E1", linewidth=1.0)
            
            # 枠線のスタイリング
            ax1.spines['top'].set_visible(False)
            ax2.spines['top'].set_visible(False)
            ax1.spines['left'].set_color('#1E3A8A')
            ax1.spines['left'].set_linewidth(1.5)
            ax2.spines['right'].set_color('#059669')
            ax2.spines['right'].set_linewidth(1.5)
            ax1.spines['bottom'].set_color('#94A3B8')
            ax2.spines['bottom'].set_color('#94A3B8')
            
            # 2つのグラフの凡例を1つにまとめて右下に配置 (日本語表記)
            lines = line1 + line2
            labels = [l.get_label() for l in lines]
            ax1.legend(lines, labels, loc="lower right", frameon=True, facecolor="#F8FAFC", edgecolor="none", fontsize=10)
            
            plt.tight_layout()
            st.pyplot(fig)
        
        # --- 8. データプレビュー & Excelダウンロード ---
        with st.expander("📊 読み込んだ表データを確認する（全行表示・ソート可能）"):
            st.dataframe(df, height=400, use_container_width=True)
            
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name="S11_吸収率データ")
            df_raw.to_excel(writer, index=False, sheet_name="解析生データ(全項目)")
            
        excel_data = output.getvalue()
        
        st.write("") # スペーサー
        st.download_button(
            label="📥 Excelファイル (.xlsx) をダウンロード",
            data=excel_data,
            file_name="S11_Absorption_Data.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
    except Exception as e:
        st.error(f"エラーが発生しました。テキストファイルの中身が正しいか確認してください。\n詳細: {e}")