import json

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
def load_kb():
    with open("knowledge_base.json", encoding="utf-8") as f:
        return json.load(f)


KB = load_kb()
STAINS = {s["id"]: s for s in KB["stains"]}

# シミの種類 → (見出し, 例, 当てはまる知識データのid, 基本の考え方)
STAIN_TYPES = {
    "water": (
        "水性(飲み物・調味料)",
        "コーヒー、紅茶、醤油、ソース、ワイン、ジュース、ケチャップ",
        ["coffee_tea", "soy_sauce", "wine", "ketchup"],
        [
            "水に溶ける汚れなので、**できるだけ早く、水で薄める・たたき出す**のが基本です。",
            "シミの**裏側にタオルを当て**、表から湿らせた布で軽くたたいて、汚れをタオル側へ移します(こすると広がります)。",
            "コーヒー・紅茶・ワイン・ジュースの色素(タンニン系)は、水で落としたあと、残った色を**酸素系漂白剤**で抜きます。",
            "**固形石けんは使わない**でください。色素が定着することがあります。",
        ],
    ),
    "water_ink": (
        "水性インク",
        "水性ボールペン、ゲルインクペン、水性マーカー",
        ["water_based_pen"],
        [
            "水に溶ける染料なので、早ければ水と中性洗剤でも落ちますが、**広がりやすい**ので注意します。",
            "インクが乾いていたり落ちにくいときは、**消毒用エタノール**で溶かして、当て布に移します。",
            "必ず**裏から当て布をして、たたくように**します。こすらないでください。",
        ],
    ),
    "oil_ink": (
        "油性インク",
        "油性ボールペン、油性マジック、朱肉",
        ["oil_based_pen", "oil_based_marker", "shuniku"],
        [
            "水では落ちません。**アルコール系の溶剤**(消毒用エタノールなど)でインクを溶かし、**下に敷いたタオルへ移す**のが基本です。",
            "シミの**裏側にタオルを敷き、表から溶剤を含ませた布でたたきます**。こすると広がります。",
            "落ちきるまで**乾燥機や高温は使わない**でください。熱で定着します。",
            "エタノールは引火性があります。**火気の近くで使わない**でください。絹・レーヨンなどのデリケートな生地は、色落ちや変質のおそれがあるため、まず目立たない所で試してください。",
        ],
    ),
    "oil": (
        "油性(油脂・化粧品)",
        "食用油、ドレッシング、口紅、ファンデーション、皮脂・襟汚れ",
        ["oil_food", "lipstick_makeup", "sebum_collar"],
        [
            "油は水をはじくため、**先に油分を溶かして落とす**のが基本です。台所用洗剤(中性)やクレンジングを直接なじませます。",
            "色素が残るときは、**油を落としたあとに**酸素系漂白剤を使います(油が残ったままだと漂白剤が効きにくくなります)。",
            "洗濯機に入れる前に処理してください。洗って乾かしたシミは、かなり落ちにくくなります。",
        ],
    ),
    "other": (
        "その他",
        "血液、泥",
        ["blood", "mud"],
        [
            "血液などの**タンパク質汚れはお湯で固まる**ので、必ず**水(冷水)**で処理します。",
            "泥は**完全に乾かしてから**ブラシで払い落とし、そのあと水洗いします。濡れたままこすると繊維に入り込みます。",
        ],
    ),
}

st.title("🧺 染み抜き方法")
st.caption("シミの種類をタップすると、使う薬品と落とし方が下に開きます。")

st.markdown(
    '<h3 translate="no" lang="ja">シミの種類は?</h3>',
    unsafe_allow_html=True,
)
def render_guide(key):
    title, examples, ids, principles = STAIN_TYPES[key]
    with st.container(border=True):
        st.markdown("##### 基本の考え方")
        for p in principles:
            st.markdown(f"- {p}")

        st.markdown("##### シミ別の薬品と手順")
        for sid in ids:
            c = STAINS[sid]
            st.markdown(f"**{c['name']}**")
            st.write("使う薬品: " + "、".join(c["chemicals"]))
            for i, step in enumerate(c["procedure"], 1):
                st.write(f"{i}. {step}")
            st.write("")

        st.error("※必ず生地の目立たない部分で試してから本番作業してください。")
        st.caption(
            "水洗い不可・ドライクリーニング表示の衣類、高価な衣類、落ちなかった場合は、"
            "無理をせずクリーニング店に相談してください。"
        )


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

st.caption("※ 水洗い不可の衣類や高価な衣類は、クリーニング店に相談してください。")

with st.expander("参考にした情報"):
    st.markdown(
        "- [Texas A&M AgriLife Extension: Quick Stain Removal Guide](https://agrilifeextension.tamu.edu/wp-content/uploads/2025/04/Quick-Stain-Removal-Guide.pdf)\n"
        "- [Michigan State University Extension: 家庭でのシミ抜きガイド(E1453)](https://archive.lib.msu.edu/DMC/extension_publications/E1453/e1453_82.pdf)\n"
        "- [Mississippi State University Extension: How to Remove Pesky Stains](https://extension.msstate.edu/blog/how-remove-pesky-stains)\n"
        "- [Illinois Extension: Stain Removal Guide](https://dev.web.extension.illinois.edu/stain/general_fabrics.cfm)\n"
        "- [Tide: How to Remove Ink Stains](https://tide.com/en-us/how-to-wash-clothes/how-to-remove-stains/ink-stains)\n"
        "- [macaro-ni: 自宅でできるシミ抜き](https://macaro-ni.jp/11715)\n"
        "- [All About: 油性汚れと漂白剤](https://news.allabout.co.jp/articles/o/tu/112259/)"
    )
