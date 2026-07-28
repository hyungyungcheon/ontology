"""웹 앱 전체에서 공유하는 온톨로지 상태를 앱 시작 시 1회만 만든다.

sync_reasoner()는 매번 Java(HermiT)를 서브프로세스로 띄우기 때문에 요청마다 다시
실행하면 느리고 불필요하다. 반면 냉장고 재료 기반 판정(find_makeable_recipes,
get_recipe_tags)은 순수 Python이라 요청마다 빠르게 다시 계산해도 문제없다.
"""

from src.data import INGREDIENTS, RECIPES, SUBSTITUTES
from src.reasoner import (
    ReasonerUnavailableError,
    build_and_classify,
    build_substitute_map,
    get_inferred_subsumptions,
)

_state = None


def get_state():
    """(onto, ingredients, recipes, substitute_map, subsumption_facts, error)를 반환한다.

    reasoner를 못 돌리는 환경(Java 없음)이어도 앱 전체가 죽지 않도록, 실패 시
    onto=None과 error 메시지를 담아 반환한다. 이 경우에도 find_makeable_recipes/
    get_recipe_tags는 온톨로지 없이 data.py만으로 동작하므로 홈 화면은 계속 쓸 수 있다.
    """
    global _state
    if _state is None:
        substitute_map = build_substitute_map(INGREDIENTS, SUBSTITUTES)
        try:
            onto, ingredients, recipes = build_and_classify()
            subsumption_facts = get_inferred_subsumptions(onto)
            error = None
        except ReasonerUnavailableError as exc:
            onto, ingredients, recipes = None, None, None
            subsumption_facts = []
            error = str(exc)
        except Exception as exc:  # noqa: BLE001 - 캐시를 채워서 재시도 폭주를 막기 위한 방어
            onto, ingredients, recipes = None, None, None
            subsumption_facts = []
            error = f"온톨로지를 빌드하는 중 예상치 못한 오류: {exc}"
        _state = {
            "onto": onto,
            "ingredients": ingredients,
            "recipes": recipes,
            "substitute_map": substitute_map,
            "subsumption_facts": subsumption_facts,
            "error": error,
        }
    return _state
