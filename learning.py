"""フィードバック記録から、候補の順位を補正するための仕組み。

考え方(単純で説明できるルール):
- 「合っていた」→ 当時の第1候補が正解だったとみなす
- 「違っていた」+ 実際のシミ名がナレッジベースにある → そのシミが正解、第1候補は外れ
- 今回の回答と過去の記録が似ているほど、そのシミのスコアを加点(外れなら減点)
- 補正は最大 ±BONUS_CAP 点。ルール本体(最大9点)を覆さない範囲にとどめる
"""
import re

import db

UNKNOWN = "わからない"
WEIGHT = 0.5      # 完全一致の記録1件あたりの加点
BONUS_CAP = 2.0   # 補正の上限(±)


def _norm(s):
    return re.sub(r"\s", "", s or "")


def _clean(v):
    return None if v in (None, "", UNKNOWN) else v


def _name_parts(name):
    return [p for p in re.split("[・()（）]", name) if len(p) >= 2] + [name]


def resolve_id(text, kb):
    """入力されたシミ名をナレッジベースのIDに対応づける(見つからなければNone)"""
    a = _norm(text)
    if len(a) < 2:
        return None
    for stain in kb["stains"]:
        for part in _name_parts(stain["name"]):
            p = _norm(part)
            if a == p or a in p or p in a:
                return stain["id"]
    return None


def load_observations(kb):
    """フィードバック済み記録を、学習に使う形に直す"""
    id_by_name = {s["name"]: s["id"] for s in kb["stains"]}
    obs = []
    for r in db.get_feedback_rows():
        predicted = [n.strip() for n in (r.get("predicted_stain") or "").split(",") if n.strip()]
        top1 = id_by_name.get(predicted[0]) if predicted else None
        actual = resolve_id(r.get("actual_stain"), kb)
        if r.get("is_correct") == 1:
            pos, neg = (actual or top1), None
        else:
            pos, neg = actual, (top1 if top1 != actual else None)
        if not pos and not neg:
            continue
        obs.append({
            "pos": pos,
            "neg": neg,
            "color": _clean(r.get("detected_color")),
            "spread": _clean(r.get("spread_answer")),
            "texture": _clean(r.get("texture_answer")),
            "smell": _clean(r.get("smell_answer")),
        })
    return obs


def _similarity(query, o):
    """両方が答えている項目のうち、一致した割合(比較できる項目がなければNone)"""
    compared = matched = 0
    for k in ("color", "spread", "texture", "smell"):
        if query[k] is not None and o[k] is not None:
            compared += 1
            matched += query[k] == o[k]
    return matched / compared if compared else None


def make_bonus_fn(kb):
    """(stain, query) -> (補正点, 裏付けとなった過去記録の件数)"""
    observations = load_observations(kb)

    def bonus_fn(stain, color, spread, texture, smell):
        query = {"color": _clean(color), "spread": _clean(spread),
                 "texture": _clean(texture), "smell": _clean(smell)}
        total, support = 0.0, 0
        for o in observations:
            sim = _similarity(query, o)
            if sim is None:
                continue
            if o["pos"] == stain["id"]:
                total += WEIGHT * sim
                support += sim >= 0.75
            elif o["neg"] == stain["id"]:
                total -= WEIGHT * sim
        return max(-BONUS_CAP, min(BONUS_CAP, total)), support

    return bonus_fn, len(observations)
