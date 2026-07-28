"""냉장고 재료 추천 CLI."""

import sys

from src.data import INGREDIENTS, RECIPES, SUBSTITUTES
from src.reasoner import (
    ReasonerUnavailableError,
    build_and_classify,
    build_substitute_map,
    find_makeable_recipes,
    get_inferred_subsumptions,
    get_recipe_tags,
)


def _label_to_id_map():
    return {korean: ing_id for ing_id, (_, korean) in INGREDIENTS.items()}


def parse_fridge_input(raw_input, label_to_id):
    ids = []
    unknown = []
    for token in raw_input.split(","):
        name = token.strip()
        if not name:
            continue
        if name in label_to_id:
            ids.append(label_to_id[name])
        else:
            unknown.append(name)
    return ids, unknown


def print_report(onto, fridge_ids, substitute_map):
    print()
    print("=== OWL reasoner가 추론한 클래스 관계 (TBox) ===")
    subsumptions = get_inferred_subsumptions(onto)
    if subsumptions:
        for fact in subsumptions:
            print(f"  - {fact}")
    else:
        print("  (없음)")

    print()
    print("=== 요리별 분류 태그 ===")
    for recipe_id, (korean_label, required_ids) in RECIPES.items():
        tags = get_recipe_tags(required_ids)
        tag_str = f" [{', '.join(tags)}]" if tags else ""
        print(f"  - {korean_label}{tag_str}")

    makeable = find_makeable_recipes(fridge_ids, RECIPES, substitute_map)

    direct = [rid for rid, r in makeable.items() if r["status"] == "direct"]
    substitute = [rid for rid, r in makeable.items() if r["status"] == "substitute"]
    missing = [rid for rid, r in makeable.items() if r["status"] == "missing"]

    print()
    print("=== 바로 만들 수 있는 요리 ===")
    if direct:
        for rid in direct:
            print(f"  - {RECIPES[rid][0]}")
    else:
        print("  (없음)")

    print()
    print("=== 대체 재료로 만들 수 있는 요리 ===")
    if substitute:
        for rid in substitute:
            subs = makeable[rid]["substitutions"]
            sub_desc = ", ".join(
                f"{INGREDIENTS[orig][1]} -> {INGREDIENTS[sub][1]}"
                for orig, sub in subs.items()
            )
            print(f"  - {RECIPES[rid][0]} ({sub_desc})")
    else:
        print("  (없음)")

    print()
    print("=== 재료가 부족한 요리 ===")
    if missing:
        for rid in missing:
            missing_names = ", ".join(INGREDIENTS[m][1] for m in makeable[rid]["missing"])
            print(f"  - {RECIPES[rid][0]} (부족: {missing_names})")
    else:
        print("  (없음)")
    print()


def main():
    for stream in (sys.stdout, sys.stdin):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")

    print("냉장고 재료 추천 (온톨로지 + OWL reasoner 데모)")
    print("사용 가능한 재료:", ", ".join(korean for _, korean in INGREDIENTS.values()))

    raw_input = input("냉장고에 있는 재료를 쉼표로 구분해서 입력하세요: ")

    label_to_id = _label_to_id_map()
    fridge_ids, unknown = parse_fridge_input(raw_input, label_to_id)

    if unknown:
        print(f"알 수 없는 재료라 무시합니다: {', '.join(unknown)}")

    print("추론 중... (HermiT reasoner 실행, 처음 실행 시 몇 초 걸릴 수 있습니다)")
    try:
        onto, ingredients, _recipes = build_and_classify()
    except ReasonerUnavailableError as exc:
        print(f"오류: {exc}")
        return

    substitute_map = build_substitute_map(ingredients, SUBSTITUTES)
    print_report(onto, fridge_ids, substitute_map)


if __name__ == "__main__":
    main()
