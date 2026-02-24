import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

# ---------------------------------------------------------
# 1. ページ設定 & パスワード認証（運営者限定）
# ---------------------------------------------------------
st.set_page_config(page_title="運営用：集計ダッシュボード", layout="centered")

# サイドバーにパスワード入力欄を作る
password = st.sidebar.text_input("管理者パスワードを入力", type="password")

# Secretsに設定したパスワードと一致するかチェック
# （まだ入力していない、または間違っている場合はここでストップ）
if password != st.secrets["password"]:
    st.warning("⚠️ このページは運営スタッフ専用です。パスワードを入力してください。")
    st.stop()  # ここで処理を止める

# パスワードが合っていたら以下を表示
st.sidebar.success("認証成功！")
st.title("🎨 【運営用】リアルタイム集計結果")

if st.button("🔄 最新データに更新"):
    st.cache_data.clear()

# ---------------------------------------------------------
# 2. データの取得（クラウドのSecretsを使う）
# ---------------------------------------------------------
@st.cache_data(ttl=10)
def get_survey_data():
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    
    # ★ここが変わりました！ローカルファイルではなく、Secretsから鍵情報を読み込む
    creds_dict = st.secrets["gcp_service_account"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    
    # スプレッドシート名（※あなたのファイル名に合わせてください）
    sheet = client.open('フォームの回答 1').sheet1 
    return pd.DataFrame(sheet.get_all_records())

# ---------------------------------------------------------
# 3. 集計と表示（前回と同じロジック）
# ---------------------------------------------------------
try:
    df = get_survey_data()
    
    # 質問文（※あなたのフォームに合わせて正確に！）
    col_votes = '特に気になった作品・お気に入りの作品の番号を教えてください。（複数選択可）' 
    col_comments = '展覧会全体のご感想や、作品へのメッセージなどをご自由にお書きください。'
    
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
            
            st.metric("現在の総回答者数", f"{len(df)}人")
            st.bar_chart(data=vote_counts, x='作品番号', y='投票数')
            st.dataframe(vote_counts, use_container_width=True)
        else:
            st.info("まだ投票がありません")
            
        # 感想表示
        st.write("---")
        st.write("### 📝 新着の感想")
        if col_comments in df.columns:
            comments = df[col_comments].dropna().astype(str).str.strip()
            for comment in comments:
                if comment: st.info(comment)

except Exception as e:
    st.error(f"エラー: {e}")
