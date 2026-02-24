import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import json

# ==========================================
# 1. ページの設定
# ==========================================
st.set_page_config(page_title="アート展示会 集計結果", page_icon="🎨", layout="centered")
st.title("🎨 アート展示会：人気作品ランキング")

if st.button("🔄 最新の結果に更新する"):
    st.cache_data.clear()

# ==========================================
# 2. データの取得（自動判別・最強版）
# ==========================================
@st.cache_data(ttl=10)
def get_survey_data():
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    
    # --- ここから修正：どんな書き方でも対応させる処理 ---
    
    # 1. まず 'google_key' があるか確認
    if "google_key" not in st.secrets:
        st.error("🚨 エラー：Secretsに 'google_key' が見つかりません！")
        st.info("ヒント：Streamlitの設定画面で、変数名を 'google_key' にしているか確認してください。")
        st.stop()

    # 2. 中身を取り出す
    secret_value = st.secrets["google_key"]

    # 3. 中身が「辞書(dict)」か「文字(str)」かで処理を分ける
    if isinstance(secret_value, dict):
        # 辞書形式（[google_key]）で保存されていた場合
        key_dict = secret_value
    else:
        # 文字列形式（google_key = """..."""）で保存されていた場合
        try:
            key_dict = json.loads(secret_value)
        except json.JSONDecodeError:
            st.error("🚨 エラー：Secretsの中身が正しいJSON形式ではありません。")
            st.info("ヒント：コピーした貼り付けたJSONの末尾が切れていないか、余計な文字が入っていないか確認してください。")
            st.stop()

    # --- 修正ここまで ---

    creds = ServiceAccountCredentials.from_json_keyfile_dict(key_dict, scope)
    client = gspread.authorize(creds)
    
    # スプレッドシート名を確認！（あなたのファイル名に合わせてください）
    sheet_name = '夢想郷展　来場者アンケート'
    
    try:
        sheet = client.open(sheet_name).sheet1
    except gspread.SpreadsheetNotFound:
        st.error(f"🚨 エラー：スプレッドシート '{sheet_name}' が見つかりません。")
        st.info("ヒント：Googleスプレッドシートの名前が合っているか、共有設定ができているか確認してください。")
        st.stop()
        
    return pd.DataFrame(sheet.get_all_records())

# ==========================================
# 3. 集計と表示
# ==========================================
try:
    df = get_survey_data()
    
    # 質問文（※一言一句合わせる！）
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
            
            st.write(f"### 👥 現在の回答者数: {len(df)} 人")
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
            if not comments.empty:
                for comment in comments:
                    st.info(comment)
            else:
                st.write("感想はまだありません。")

    else:
        st.info("まだ回答がありません。")

except Exception as e:
    st.error(f"予期せぬエラーが発生しました: {e}")

