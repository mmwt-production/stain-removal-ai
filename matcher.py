def score_stain(stain, color, spread_answer, texture_answer, smell_answer):
    score = 0
    if color in stain["colors"]:
        score += 3
    if spread_answer and spread_answer == stain["spread_in_water"]:
        score += 2
    if texture_answer and texture_answer == stain["texture"]:
        score += 2
    if smell_answer and smell_answer == stain.get("smell"):
        score += 2
    return score

def rank_candidates(knowledge_base, color, spread_answer, texture_answer, smell_answer,
                    top_n=3, bonus_fn=None):
    """[(stain, 基本スコア, 学習補正, 裏付け件数)] を順位順に返す。
    bonus_fn があれば、過去の記録による補正を順位に反映する。"""
    ranked = []
    for stain in knowledge_base["stains"]:
        base = score_stain(stain, color, spread_answer, texture_answer, smell_answer)
        if base <= 0:
            continue
        bonus, support = (0.0, 0)
        if bonus_fn:
            bonus, support = bonus_fn(stain, color, spread_answer, texture_answer, smell_answer)
        ranked.append((stain, base, bonus, support))
    ranked.sort(key=lambda x: x[1] + x[2], reverse=True)
    return ranked[:top_n]

def find_candidates(knowledge_base, color, spread_answer, texture_answer, smell_answer, top_n=3):
    ranked = rank_candidates(knowledge_base, color, spread_answer, texture_answer, smell_answer, top_n)
    return [stain for stain, _, _, _ in ranked]