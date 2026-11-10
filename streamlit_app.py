import json
import os

import streamlit as st
import streamlit.components.v1 as components

from image_analysis import COLOR_BUCKETS
from matcher import rank_candidates
from learning import make_bonus_fn
import db
from db import init_db, save_record, save_feedback

UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

st.set_page_config(page_title="シミ抜き分析", page_icon="🧺", layout="centered")

# ブラウザの自動翻訳による誤訳を防ぐ(日本語ページとして宣言し、翻訳を無効化)
components.html(
    """
    <script>
    try {
      const d = window.parent.document;
      d.documentElement.lang = "ja";
      d.documentElement.setAttribute("translate", "no");
      d.body.setAttribute("translate", "no");
      if (!d.querySelector('meta[name="google"]')) {
        const m = d.createElement("meta");
        m.name = "google"; m.content = "notranslate";
        d.head.appendChild(m);
      }
    } catch (e) {}
    </script>
    """,
    height=0,
)


@st.cache_resource
def load_kb():
    with open("knowledge_base.json", encoding="utf-8") as f:
        return json.load(f)


@st.cache_resource
def setup_db():
    init_db()
    return True


KB = load_kb()
setup_db()

SPREAD = ["広がる", "変化なし"]
TEXTURE = ["ベタベタ・油っぽい", "サラサラ", "硬い・カピカピ"]
SMELL = [
    "無臭",
    "食品っぽい・酸っぱいにおい",
    "生臭い(鉄っぽいにおい)",
    "油っぽいにおい",
    "インク・薬品のようなにおい",
    "汗・皮脂のようなにおい",
]
AGE = ["すぐ(まだ湿っている)", "数時間〜1日", "数日以上(乾いて古い)"]

UNKNOWN = "わからない"

# シミの種類(油性・水性など)。選ぶと、その種類に当てはまる候補だけで判定する
STAIN_TYPES = {
    "水性(飲み物・調味料)\n例: コーヒー、紅茶、醤油、ソース、ワイン、ジュース、ケチャップ": [
        "coffee_tea", "soy_sauce", "wine", "ketchup",
    ],
    "水性インク\n例: 水性ボールペン、ゲルインクペン、水性マーカー": [
        "water_based_pen",
    ],
    "油性インク\n例: 油性ボールペン、油性マジック、朱肉": [
        "oil_based_pen", "oil_based_marker", "shuniku",
    ],
    "油性(油脂・化粧品)\n例: 食用油、ドレッシング、口紅、ファンデーション、皮脂・襟汚れ": [
        "oil_food", "lipstick_makeup", "sebum_collar",
    ],
    "その他\n例: 血液、泥": ["blood", "mud"],
}
TYPE_OPTIONS = [UNKNOWN] + list(STAIN_TYPES.keys())
COLORS = [UNKNOWN] + list(COLOR_BUCKETS.keys())

st.title("🧺 シミ抜き分析")

# ---------- 入力 ----------
# 「状態」がブラウザ翻訳で「州」になるため、翻訳しない指定つきの見出しにする
st.markdown(
    '<h3 translate="no" lang="ja">状態を教えてください</h3>',
    unsafe_allow_html=True,
)
st.caption("「わからない」を選んだ項目は無視して判定します。答えるほど精度が上がります。")

stain_type = st.radio(
    "シミの種類は?(油性・水性のどれに近いですか)",
    TYPE_OPTIONS,
    format_func=lambda t: t if t == UNKNOWN else t.replace("\n", "\n\n"),
)
manual_color = st.selectbox("シミの色", COLORS)

spread = st.selectbox("水で濡らすと、シミは?", [UNKNOWN] + SPREAD)
texture = st.selectbox("シミの手触りは?", [UNKNOWN] + TEXTURE)
smell = st.selectbox("におい", [UNKNOWN] + SMELL)
age = st.selectbox("シミが付いてからの経過時間", [UNKNOWN] + AGE)


def none_if_unknown(v):
    return None if v == UNKNOWN else v


if st.button("判定する", type="primary", use_container_width=True):
    filepath = ""
    color_name = none_if_unknown(manual_color)

    s_spread = none_if_unknown(spread)
    s_texture = none_if_unknown(texture)
    s_smell = none_if_unknown(smell)

    answered = sum(x is not None for x in (color_name, s_spread, s_texture, s_smell))
    if answered == 0:
        st.warning("種類のほか、色や下の質問のいずれか1つ以上にも答えてください。")
    else:
        bonus_fn, n_learned = make_bonus_fn(KB)
        if stain_type == UNKNOWN:
            kb_used = KB
        else:
            allowed = STAIN_TYPES[stain_type]
            kb_used = {"stains": [x for x in KB["stains"] if x["id"] in allowed]}
        ranked = rank_candidates(
            kb_used, color_name, s_spread, s_texture, s_smell, bonus_fn=bonus_fn
        )
        candidates = [r[0] for r in ranked]
        max_score = (
            (3 if color_name else 0)
            + (2 if s_spread else 0)
            + (2 if s_texture else 0)
            + (2 if s_smell else 0)
        )
        scores = {r[0]["id"]: r[1] for r in ranked}
        learned = {r[0]["id"]: (r[2], r[3]) for r in ranked}
        predicted = ", ".join(c["name"] for c in candidates)
        record_id = save_record(
            filepath, color_name or UNKNOWN, spread, texture, predicted, smell
        )

        st.session_state["result"] = {
            "record_id": record_id,
            "image_path": filepath,
            "color_name": color_name or UNKNOWN,
            "candidates": candidates,
            "scores": scores,
            "learned": learned,
            "n_learned": n_learned,
            "max_score": max_score,
            "answered": answered,
            "age": age,
            "feedback_done": False,
        }

# ---------- 結果 ----------
res = st.session_state.get("result")
if res:
    st.divider()
    st.header("判定結果")
    st.write(f"シミの色: **{res['color_name']}**")
    st.caption(f"🧠 学習データ: {res['n_learned']}件の記録を参考にしました")
    if db.last_error:
        st.warning(db.last_error)
    if res["answered"] <= 2:
        st.caption("回答が少ないため、候補は目安です。わかる項目を追加すると絞り込めます。")

    if res["age"] == "数日以上(乾いて古い)":
        st.warning(
            "時間が経ったシミは色素が繊維の奥に定着している場合があります。"
            "1回で落ちなければ、酸素系漂白剤でのつけ置き時間を長めに取ることを検討してください。"
        )

    if not res["candidates"]:
        st.info("該当する候補が見つかりませんでした。項目を見直してください。")
    for c in res["candidates"]:
        with st.container(border=True):
            pct = round(100 * res["scores"][c["id"]] / res["max_score"])
            st.subheader(f"{c['name']}({c['category']})")
            st.progress(pct / 100, text=f"一致度 {pct}%")
            bonus, support = res["learned"][c["id"]]
            if bonus > 0:
                st.caption(f"🧠 過去の記録で裏付けあり(似た事例 {support}件)。順位を上げています")
            elif bonus < 0:
                st.caption("🧠 似た条件で外れた記録があるため、順位を下げています")
            st.write("**使う薬品:** " + ", ".join(c["chemicals"]))
            for i, step in enumerate(c["procedure"], 1):
                st.write(f"{i}. {step}")

    st.error("※必ず生地の目立たない部分で試してから本番作業してください。")

    # ---------- フィードバック ----------
    st.divider()
    st.subheader("この判定は合っていましたか?")
    if res["feedback_done"]:
        st.success("ご協力ありがとうございました。記録しました。")
    else:
        with st.form("feedback"):
            is_correct = st.radio("結果", ["合っていた", "違っていた"], horizontal=True)
            actual_stain = st.text_input("実際のシミの種類(わかれば)", placeholder="例: コーヒー")
            actual_chemical = st.text_input("実際に使った薬品(わかれば)", placeholder="例: 中性洗剤")
            if st.form_submit_button("記録する"):
                save_feedback(
                    res["record_id"], is_correct == "合っていた", actual_stain, actual_chemical
                )
                res["feedback_done"] = True
                if db.last_error:
                    st.warning(db.last_error)
                else:
                    st.rerun()
