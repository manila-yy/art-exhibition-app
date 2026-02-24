import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import json  # ★これが必要

# ==========================================
# 1. ページの設定
# ==========================================
st.set_page_config(page_title="アート展示会 集計結果", page_icon="🎨", layout="centered")
st.title("🎨 アート展示会：人気作品ランキング")

# 更新ボタン
if st.button("🔄 最新の結果に更新する"):
    st.cache_data.clear()

# ==========================================
# 2. データの取得（修正版）
# ==========================================
@st.cache_data(ttl=10)
def get_survey_data():
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    
    # ★ここが修正ポイント！
    # Secretsから「google_key」という名前のデータを取り出し、JSONとして読み込む
    try:
        json_str = st.secrets["google_key"]
        key_dict = json.loads(json_str)
    except Exception:
        st.error("Secretsの設定エラー：'google_key' が見つかりません。設定を確認してください。")
        return pd.DataFrame()

    creds = ServiceAccountCredentials.from_json_keyfile_dict(key_dict, scope)
    client = gspread.authorize(creds)
    
    # スプレッドシートを開く（※あなたのファイル名になっているか確認！）
    sheet = client.open('フォームの回答 1').sheet1 
    
    return pd.DataFrame(sheet.get_all_records())

# ==========================================
# 3. 集計と表示
# ==========================================
try:
    df = get_survey_data()
    
    # 質問文（※あなたのフォームと一言一句同じにすること！）
    col_votes = '特に気になった作品・お気に入りの作品の番号を教えてください。（複数選択可）' 
    col_comments = '展覧会全体のご感想や、作品へのメッセージなどをご自由にお書きください。'
    
    if not df.empty and col_votes in df.columns:
        # --- 集計処理 ---
        df_votes = df.dropna(subset=[col_votes])
        votes = df_votes[col_votes].astype(str).str.split(',').explode().str.strip()
        votes = votes[votes != ""]
        
        if not votes.empty:
            vote_counts = votes.value_counts().reset_index()
            vote_counts.columns = ['作品番号', '投票数']
            # 数値順に並び替え
            vote_counts['作品番号_数値'] = pd.to_numeric(vote_counts['作品番号'], errors='coerce')
            vote_counts = vote_counts.sort_values(by='作品番号_数値').drop(columns=['作品番号_数値'])
            
            # 結果表示
            st.write(f"### 👥 現在の回答者数: {len(df)} 人")
            st.bar_chart(data=vote_counts, x='作品番号', y='投票数')
            st.dataframe(vote_counts, use_container_width=True)
        else:
            st.info("まだ投票がありません。")

        # --- 感想表示 ---
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
    st.error(f"エラーが発生しました: {e}")
