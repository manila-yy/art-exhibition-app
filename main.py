import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

# ==========================================
# 1. ページの設定
# ==========================================
st.set_page_config(page_title="アート展示会 リアルタイム集計", page_icon="🎨", layout="centered")
st.title("🎨 アート展示会：人気作品＆感想ダッシュボード")

# 手動更新ボタン
if st.button("🔄 最新の結果に更新する"):
    st.cache_data.clear()


# ==========================================
# 2. データの取得機能（API）
# ==========================================
# Google APIの制限を防ぐため、10秒間データを保持（キャッシュ）します
@st.cache_data(ttl=10)
def get_survey_data():
    scope = [
        'https://spreadsheets.google.com/feeds',
        'https://www.googleapis.com/auth/drive'
    ]

    # JSONキーを使って認証（※credentials.jsonを同じフォルダに置くこと）
    creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
    client = gspread.authorize(creds)

    # スプレッドシートを開く（※あなたのスプレッドシートの実際のシート名に変更してください）
    # デフォルトでは「フォームの回答 1」という名前になっていることが多いです
    sheet = client.open('夢想郷展　来場者アンケート').sheet1

    # データをすべて取得してデータフレーム（表形式）に変換
    data = sheet.get_all_records()
    return pd.DataFrame(data)


# ==========================================
# 3. データの集計と画面表示
# ==========================================
try:
    df = get_survey_data()

    # データが1件以上あるかチェック
    if not df.empty:

        # 【重要】Googleフォームの実際の質問文と一言一句「完全に」同じにしてください！
        col_votes = '気になった作品・お気に入りの作品の番号を教えてください(複数選択可)。'
        col_comments = '展覧会全体への感想や、作品へのメッセージなど自由にお書きください。'

        st.write(f"### 👥 アンケート回答者数: **{len(df)} 人**")

        # --------------------------------------
        # ① 投票データの集計とグラフ表示
        # --------------------------------------
        if col_votes in df.columns:
            # 1. 回答がない（空欄）の行を除外
            df_votes = df.dropna(subset=[col_votes])

            # 2. 「1, 3」のようなカンマ区切りの文字列を分割し、バラバラのデータにする
            votes = df_votes[col_votes].astype(str).str.split(',').explode()

            # 3. 分割した際に入ってしまう余白（スペース）を削除し、空欄を除外
            votes = votes.str.strip()
            votes = votes[votes != ""]

            if not votes.empty:
                # 4. 作品番号ごとの投票数をカウント
                vote_counts = votes.value_counts().reset_index()
                vote_counts.columns = ['作品番号', '投票数']

                # 5. 作品番号順に正しく並び替え（「10」が「2」より前に来ないように一旦数値として扱う）
                vote_counts['作品番号_数値'] = pd.to_numeric(vote_counts['作品番号'], errors='coerce')
                vote_counts = vote_counts.sort_values(by='作品番号_数値').drop(columns=['作品番号_数値'])

                # 棒グラフを表示
                st.bar_chart(data=vote_counts, x='作品番号', y='投票数')

                # 集計表をアコーディオン（折りたたみ）で表示
                with st.expander("📊 作品ごとの投票数（詳細データを見る）"):
                    st.dataframe(vote_counts, use_container_width=True)
            else:
                st.info("まだ作品への投票がありません。")
        else:
            st.warning(f"⚠️ スプレッドシートに「{col_votes}」という列が見つかりません。質問文を確認してください。")

        # --------------------------------------
        # ② 感想の表示
        # --------------------------------------
        st.write("---")
        st.write("### 💬 いただいたご感想")

        if col_comments in df.columns:
            # 空欄を除外して感想リストを取得
            comments = df[col_comments].dropna().astype(str).str.strip()
            comments = comments[comments != ""]

            if not comments.empty:
                # 感想を1つずつ枠で囲って表示
                for comment in comments:
                    st.info(comment)
            else:
                st.write("まだ感想は寄せられていません。")
        else:
            st.warning(f"⚠️ スプレッドシートに「{col_comments}」という列が見つかりません。質問文を確認してください。")

    else:
        st.info("まだ回答がありません。最初の投票をお待ちしています！")

# エラーが起きた場合の表示
except Exception as e:
    st.error("データの取得中にエラーが発生しました。")
    st.error(f"詳細: {e}")