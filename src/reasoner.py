"""추론을 두 레이어로 나눈다.

1) OWL DL 추론 (owlready2 + HermiT, TBox/클래스 레벨): equivalent class로
   정의해 둔 VeganRecipe/DairyFreeRecipe 사이의 관계를 reasoner가 스스로
   찾아낸다 (get_inferred_subsumptions). 이건 진짜 HermiT reasoner가 계산한
   결과다.
2) 그래프 질의 (순수 Python, ABox/개체 레벨): 특정 요리가 비건인지, 지금 있는
   재료로 만들 수 있는지는 Python으로 직접 계산한다. owlready2에 번들된
   HermiT/Pellet은 개체(instance)를 equivalent class에 자동으로 편입시키는
   realize를 이 환경에서 신뢰성 있게 수행하지 못했기 때문이다 (직접 테스트해본
   결과, HermiT CLI는애초에 realize를 노출하지 않고, Pellet은 실행은 되지만
   restriction 기반 분류 결과가 항상 비어 있었다 - Jena 로더 경로의 알려진
   한계로 보인다). 그래서 "이 요리가 비건인가"는 재료 클래스를 직접 조회해서
   판정한다.
"""

import glob
import os
import shutil
from collections import defaultdict

import owlready2
from owlready2 import sync_reasoner, OwlReadyJavaError

from src.build_ontology import build_ontology
from src.data import INGREDIENTS

NON_VEGAN_CLASSES = {"Meat", "Seafood", "Dairy", "Egg"}
DAIRY_CLASSES = {"Dairy"}


class ReasonerUnavailableError(RuntimeError):
    """Java/HermiT reasoner를 실행할 수 없을 때 발생."""


def _ensure_java_findable():
    """PATH에 java가 없으면(예: JDK를 설치한 뒤 아직 새 터미널을 안 연 경우) 흔한
    설치 위치를 찾아 owlready2.JAVA_EXE를 절대경로로 바꿔준다."""
    if shutil.which(owlready2.JAVA_EXE):
        return
    if os.name != "nt":
        return
    candidates = sorted(
        glob.glob(r"C:\Program Files\Microsoft\jdk-*\bin\java.exe"), reverse=True
    )
    if candidates:
        owlready2.JAVA_EXE = candidates[0]


def build_and_classify():
    """온톨로지를 빌드하고 HermiT reasoner로 TBox 추론까지 마친 결과를 반환한다."""
    _ensure_java_findable()
    onto, ingredients, recipes = build_ontology()
    try:
        with onto:
            sync_reasoner()
    except OwlReadyJavaError as exc:
        raise ReasonerUnavailableError(
            "OWL reasoner(HermiT) 실행에 실패했습니다. Java(JRE)가 설치되어 있고 "
            "PATH에 잡혀 있는지 확인하세요."
        ) from exc
    return onto, ingredients, recipes


def get_inferred_subsumptions(onto):
    """reasoner가 스스로 찾아낸, 우리가 직접 선언하지 않은 클래스 관계를 반환한다."""
    facts = []
    if onto.DairyFreeRecipe in onto.VeganRecipe.is_a:
        facts.append(
            "VeganRecipe는 DairyFreeRecipe의 하위 클래스다 : 비건 요리는 항상 "
            "유제품-프리이기도 하다 (직접 선언한 적 없음, reasoner가 두 정의를 "
            "비교해서 추론함)"
        )
    return facts


def get_recipe_tags(required_ingredient_ids):
    """요리가 필요로 하는 재료의 클래스를 보고 Vegan/DairyFree 여부를 판정한다.

    build_ontology.py의 VeganRecipe/DairyFreeRecipe equivalent_to와 동일한 조건을
    Python으로 직접 평가한 것이다 (이유는 이 모듈 docstring 참고).
    """
    classes = {INGREDIENTS[i][0] for i in required_ingredient_ids}
    tags = []
    if not classes & NON_VEGAN_CLASSES:
        tags.append("Vegan")
    if not classes & DAIRY_CLASSES:
        tags.append("DairyFree")
    return tags


def build_substitute_map(ingredients, substitute_pairs):
    """ingredient_id -> {substitute ingredient_id, ...} 양방향 매핑을 만든다."""
    substitute_map = defaultdict(set)
    for a_id, b_id in substitute_pairs:
        substitute_map[a_id].add(b_id)
        substitute_map[b_id].add(a_id)
    return substitute_map


def find_makeable_recipes(fridge_ids, recipes_data, substitute_map):
    """냉장고에 있는 재료로 각 요리가 만들 수 있는지 판정한다.

    recipes_data: recipe_id -> (한글_이름, [필요한 ingredient_id, ...])
    반환: recipe_id -> dict(status, missing, substitutions)
      status: "direct" | "substitute" | "missing"
      substitutions: {대체된_재료_id: 사용한_대체재_id}
    """
    fridge = set(fridge_ids)
    result = {}
    for recipe_id, (_, required_ids) in recipes_data.items():
        missing = []
        substitutions = {}
        for ing_id in required_ids:
            if ing_id in fridge:
                continue
            available_subs = substitute_map.get(ing_id, set()) & fridge
            if available_subs:
                substitutions[ing_id] = sorted(available_subs)[0]
            else:
                missing.append(ing_id)

        if missing:
            status = "missing"
        elif substitutions:
            status = "substitute"
        else:
            status = "direct"

        result[recipe_id] = {
            "status": status,
            "missing": missing,
            "substitutions": substitutions,
        }
    return result
