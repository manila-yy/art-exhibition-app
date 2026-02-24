import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import json

# ==========================================
# 1. ページ設定 & パスワード認証ブロック
# ==========================================
st.set_page_config(page_title="運営用：集計ダッシュボード", page_icon="🔒", layout="centered")

# サイドバーにパスワード入力欄を表示
input_pass = st.sidebar.text_input("管理者パスワードを入力", type="password")

# --- パスワードチェック処理 ---
# Secretsに保存したパスワードと一致するか確認
if "password" in st.secrets:
    correct_password = st.secrets["password"]
else:
    st.error("Secretsに 'password' が設定されていません。")
    st.stop()

if input_pass != correct_password:
    st.sidebar.warning("パスワードを入力してください")
    st.title("🔒 認証が必要です")
    st.write("このページは関係者専用です。サイドバーにパスワードを入力してください。")
    st.stop()  # ここでプログラムを強制停止（これより下のグラフなどは表示されません）

# ==========================================
# 2. ここから先は「認証成功」した人だけが見れる
# ==========================================
st.sidebar.success("認証成功！")
st.title("🎨 【運営用】リアルタイム集計結果")

if st.button("🔄 最新の結果に更新する"):
    st.cache_data.clear()

# ==========================================
# 3. データの取得（さっき直した最強版）
# ==========================================
@st.cache_data(ttl=10)
def get_survey_data():
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    
    # Secretsから鍵を取り出す
    if "google_key" not in st.secrets:
        st.error("Secretsに 'google_key' がありません。")
        st.stop()

    secret_value = st.secrets["google_key"]

    if isinstance(secret_value, dict):
        key_dict = secret_value
    else:
        try:
            key_dict = json.loads(secret_value)
        except json.JSONDecodeError:
            st.error("SecretsのJSON形式エラー。")
            st.stop()

    creds = ServiceAccountCredentials.from_json_keyfile_dict(key_dict, scope)
    client = gspread.authorize(creds)
    
    # スプレッドシート名（あなたのファイル名）
    sheet_name = '夢想郷展　来場者アンケート'
    
    try:
        sheet = client.open(sheet_name).sheet1
        return pd.DataFrame(sheet.get_all_records())
    except Exception as e:
        st.error(f"スプレッドシートエラー: {e}")
        return pd.DataFrame()

# ==========================================
# 4. 集計と表示
# ==========================================
try:
    df = get_survey_data()
    
    col_votes = '気になった作品・お気に入りの作品の番号を教えてください(複数選択可)。' 
    col_comments = '展覧会全体への感想や、作品へのメッセージなど自由にお書きください。'
    
    if not df.empty and col_votes in df.columns:
        # 集計処理
        df_votes = df.dropna(subset=[col_votes])
        votes = df_votes[col_votes].astype(str).str.split(',').explode().str.strip()
        votes = votes[votes != ""]
        
        if not votes.empty:
            vote_counts = votes.value_counts().reset_index()
            vote_counts.columns = ['作品番号', '投票数']
            vote_counts['作品番号_数値'] = pd.to_numeric(vote_counts['作品番号'], errors='coerce')
            vote_counts = vote_counts.sort_values(by='作品番号_数値').drop(columns=['作品番号_数値'])
            
            st.metric("総回答者数", f"{len(df)}人")
            st.bar_chart(data=vote_counts, x='作品番号', y='投票数')
            st.dataframe(vote_counts, use_container_width=True)
        else:
            st.info("まだ投票がありません。")

        # 感想表示
        st.write("---")
        st.write("### 💬 いただいたご感想")
        if col_comments in df.columns:
            comments = df[col_comments].dropna().astype(str).str.strip()
            comments = comments[comments != ""]
            for comment in comments:
                st.info(comment)

    else:
        st.info("まだ回答がありません。")

except Exception as e:
    st.error(f"予期せぬエラー: {e}")
