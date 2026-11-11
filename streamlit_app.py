import json
import os

import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="染み抜き方法", page_icon="🧺", layout="centered")

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
def load_kb(mtime):
    # mtime を引数にして、ファイルを書き換えたら読み直す(古い内容が残らないように)
    with open("knowledge_base.json", encoding="utf-8") as f:
        return json.load(f)


KB = load_kb(os.path.getmtime("knowledge_base.json"))
STAINS = {s["id"]: s for s in KB["stains"]}
CHEMICALS = {c["name"]: c for c in KB.get("chemicals", [])}


def render_chemical(ch):
    st.markdown(f"**{ch['name']}**({ch['kind']})")
    if ch.get("maker"):
        st.write(f"- 製造・販売: {ch['maker']}")
    st.write(f"- 対象: {ch['targets']}")
    if ch.get("how_to"):
        st.write(f"- 使い方: {ch['how_to']}")
    if ch.get("caution"):
        st.write(f"- 注意: {ch['caution']}")

# シミの種類 → (見出し, 例, 当てはまる知識データのid, 基本の考え方)
STAIN_TYPES = {
    "water": (
        "水性(飲み物・調味料)",
        "コーヒー、紅茶、醤油、ソース、ワイン、ジュース、ケチャップ",
        ["coffee_tea", "soy_sauce", "wine", "ketchup"],
        [
            "水溶性の汚れです。**発見後はできるだけ早く、水で希釈し、たたき出しで除去**するのが基本です。",
            "タンパク系(牛乳・血液・汗など)は**スティンブルー(No.2)**、タンニン系(果汁・お茶・コーヒー)は**イエロータン(No.3)**、スティンブルーで落ちないときはイエロータン、その後は漂白処理の順に進めます。",
            "シミの**裏側に吸水性のある当て布を置き**、表から湿らせたブラシや布で軽くたたいて、汚れを当て布側へ移します(こすると広がるため厳禁)。",
            "コーヒー・紅茶・ワイン・ジュースの色素(タンニン系)は、水で処理したあと、残った色素を**酸素系漂白剤(ブリーチスター M5)**で漂白します。",
            "**固形石けんは使用しない**こと。色素が定着することがあります。",
        ],
    ),
    "water_ink": (
        "水性インク",
        "水性ボールペン、ゲルインクペン、水性マーカー",
        ["water_based_pen"],
        [
            "水溶性の染料のため、初期であれば水と中性洗剤でも除去できますが、**にじんで広がりやすい**ので注意してください。",
            "乾燥している、または落ちにくい場合は、**消毒用エタノール**で溶解し、当て布に移します。",
            "必ず**裏から当て布をして、たたいて**処理します。こすらないでください。",
        ],
    ),
    "oil_ink": (
        "油性インク",
        "油性ボールペン、油性マジック、朱肉",
        ["oil_based_pen", "oil_based_marker", "shuniku"],
        [
            "水では落ちません。**アルコール系の溶剤**(消毒用エタノールなど)でインクを溶解し、**下に敷いた当て布へ移す**のが基本です。",
            "シミの**裏側に当て布を敷き、表から溶剤を含ませた布でたたきます**。こすると広がります。",
            "除去しきるまで**乾燥機や高温処理は行わない**こと。熱で定着します。",
            "エタノールは引火性があります。**火気の近くでは使用しない**こと。絹・レーヨンなどのデリケートな素材は、色落ちや変質のおそれがあるため、必ず目立たない箇所でテストしてください。",
        ],
    ),
    "oil": (
        "油性(油脂・化粧品)",
        "食用油、ドレッシング、口紅、ファンデーション、皮脂・襟汚れ",
        ["oil_food", "lipstick_makeup", "sebum_collar"],
        [
            "油性の汚れは水をはじくため、**先に油分を溶解して除去**するのが基本です。**オイルレッド**で溶解し、スチームで濯ぎ出します。",
            "色素が残る場合は、**油分を除去したあとに**酸素系漂白剤(ブリーチスター M5)で漂白します(油分が残ったままだと漂白剤の効果が出にくくなります)。",
            "洗浄・乾燥の前に処理すること。洗浄・乾燥を経たシミは、除去が著しく困難になります。",
        ],
    ),
    "other": (
        "その他",
        "血液、泥",
        ["blood", "mud"],
        [
            "血液などの**タンパク質汚れは熱で凝固する**ため、必ず**水(冷水)**で処理します。",
            "泥は**完全に乾燥させてから**ブラシで払い落とし、そのあと水洗いします。濡れたままこすると繊維の奥に入り込みます。",
        ],
    ),
}

# シミの種類 → 「この薬剤を使う」(薬品ラベル・薬品表に書いてある効果のみ)
TYPE_CHEMS = {
    "water": [
        "**タンパク系**(牛乳・血液・汗・酒・ビール・卵など)→ **スティンブルー(No.2)**",
        "**タンニン系**(果汁・コーヒー・紅茶・お茶・ジュース)→ **イエロータン(No.3)**",
        "**食べこぼし・醤油・ケチャップ・カレーなど**→ **ラッキー103**",
        "順番は、スティンブルー → 落ちなければイエロータン → それでも残れば漂白(ブリーチスター M5)",
    ],
    "water_ink": [
        "水性インク専用の薬剤は、まだ確認できていません(いまは消毒用エタノール、仕上げにスティンブルー)。",
    ],
    "oil_ink": [
        "**油性ボールペン・油性マジック・朱肉**→ **オイルレッド**",
        "オイルレッドは、ボールペン・マジック・サインペン・朱肉・スタンプインクがラベルの対象です。",
        "赤みなど色が残る場合は、油性処理のあとに漂白(ブリーチスター M5)",
    ],
    "oil": [
        "**油性のシミはすべて → オイルレッド**(食用油・口紅・グリース・ワックス・タールなど。原因不明のシミにも使う)",
        "**ペンキ・マニキュア・ガム**→ **シンナー**(引火性。シルク・テンセル・ナイロン・コーティング商品は不可、アセテートは溶ける)",
        "油性処理を終えてから水性処理に進む(油性が不十分なまま水性処理すると、あとで漂白しても落ちない)",
    ],
    "other": [
        "**血液**→ **スティンブルー**、古いものは **ラッキー103**",
        "**泥はね**→ **ラッキー103**(乾かしてブラシで払ってから)",
        "**移染**→ **プロクリーンスーパー**(塗布後、弱スチームで洗い流す)",
        "**サビ**→ **サビクリーン**(使用後はスティンブルーで中和)",
    ],
}

st.title("🧺 染み抜き方法")
st.caption("新人スタッフ向けの染み抜きガイドです。シミの種類を選ぶと、使用する薬品と処理手順が表示されます。")
st.caption("これから当社が使用している薬品名を追加していきます。")

st.markdown(
    '<h3 translate="no" lang="ja">シミの種類は?</h3>',
    unsafe_allow_html=True,
)
def render_guide(key):
    title, examples, ids, principles = STAIN_TYPES[key]
    with st.container(border=True):
        st.info("**このシミに使う薬剤**\n\n" + "\n".join(f"- {t}" for t in TYPE_CHEMS[key]))
        sid = st.selectbox(
            "どのシミですか?",
            ids,
            index=None,
            format_func=lambda i: STAINS[i]["name"],
            placeholder="選んでください",
            key=f"stain_{key}",
        )
        if sid is None:
            st.caption("上のプルダウンから、近いものを選んでください。")
            return

        c = STAINS[sid]
        st.markdown(f"#### {c['name']}の落とし方")
        st.success(f"**使う薬品: {c['chemicals'][0]}**")
        if len(c["chemicals"]) > 1:
            st.write("落ちない・色が残る場合は、続けて: " + "、".join(c["chemicals"][1:]))
        st.markdown("**手順**")
        for i, step in enumerate(c["procedure"], 1):
            st.write(f"{i}. {step}")

        used = [CHEMICALS[n] for n in c["chemicals"] if n in CHEMICALS]
        if used:
            with st.expander("使う薬品の詳細(ラベルより)"):
                for ch in used:
                    render_chemical(ch)

        with st.expander(f"{title}の基本の考え方"):
            for p in principles:
                st.markdown(f"- {p}")

        st.error("※作業前に必ず取扱絵表示と素材を確認し、目立たない箇所でテストしてから処理してください。")


if "selected" not in st.session_state:
    st.session_state["selected"] = None

# 1列のカード(スマホで押しやすい)。選ぶと、そのカードのすぐ下に説明が開く。
# 開いているカードをもう一度押すと閉じる。
for k in STAIN_TYPES:
    is_sel = st.session_state["selected"] == k
    label = ("▼ " if is_sel else "") + f"**{STAIN_TYPES[k][0]}**\n\n例: {STAIN_TYPES[k][1]}"
    if st.button(
        label,
        key=f"btn_{k}",
        type="primary" if is_sel else "secondary",
        use_container_width=True,
    ):
        st.session_state["selected"] = None if is_sel else k
        st.rerun()
    if is_sel:
        render_guide(k)

# いまは非表示(情報がそろったら、コメントを外して表示する)
# with st.expander("当社の機械"):
#     for eq in KB.get("equipment", []):
#         st.markdown(f"**{eq['name']}**")
#         st.write(f"- 製造: {eq['maker']}")
#         st.write(f"- {eq['note']}")
#     st.caption("ガン類などの名称・使い方は、確認できしだい追加します。")
#
# with st.expander("当社の薬品一覧"):
#     for ch in CHEMICALS.values():
#         render_chemical(ch)
#         st.divider()
