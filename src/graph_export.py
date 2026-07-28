"""온톨로지를 화면에 그릴 수 있는 JSON 구조로 변환한다.

두 가지를 분리해서 만든다:
- build_class_tree(onto): 실제 owlready2 온톨로지를 introspect해서 클래스 계층을
  만든다 (TBox). reasoner가 실행된 onto를 넘기면 VeganRecipe가 DairyFreeRecipe
  아래로 reparenting된 구조까지 그대로 반영된다.
- build_instance_graph(): data.py의 시드 데이터를 그대로 사용해 개체-그래프(ABox)를
  만든다. reasoner 없이도(Java가 없는 환경이라도) 항상 그릴 수 있다.
"""

from owlready2 import Thing, ThingClass

from src.data import INGREDIENTS, RECIPES, SUBSTITUTES
from src.reasoner import get_recipe_tags

TAG_NODES = ("Vegan", "DairyFree")


def build_class_tree(onto):
    """onto.classes()를 순회해 {name, children:[...]} 형태의 트리 목록을 만든다."""
    children_map = {}
    roots = []

    for cls in onto.classes():
        parents = [p for p in cls.is_a if isinstance(p, ThingClass) and p is not Thing]
        if not parents:
            roots.append(cls.name)
        else:
            children_map.setdefault(parents[0].name, []).append(cls.name)

    def build(name):
        return {
            "name": name,
            "children": [build(child) for child in sorted(children_map.get(name, []))],
        }

    return [build(name) for name in sorted(roots)]


def build_instance_graph():
    """재료/요리 개체와 그 관계를 노드-엣지 JSON으로 만든다."""
    nodes = []
    edges = []

    for ingredient_id, (class_name, label) in INGREDIENTS.items():
        nodes.append(
            {"id": ingredient_id, "label": label, "kind": "ingredient", "type": class_name}
        )

    for recipe_id, (label, required_ids) in RECIPES.items():
        tags = get_recipe_tags(required_ids)
        nodes.append(
            {"id": recipe_id, "label": label, "kind": "recipe", "type": "Recipe", "tags": tags}
        )
        for ingredient_id in required_ids:
            edges.append(
                {"source": recipe_id, "target": ingredient_id, "relation": "requiresIngredient"}
            )
        for tag in tags:
            edges.append(
                {"source": recipe_id, "target": f"tag:{tag}", "relation": "classified_as"}
            )

    for a_id, b_id in SUBSTITUTES:
        edges.append({"source": a_id, "target": b_id, "relation": "substitutableWith"})

    for tag in TAG_NODES:
        nodes.append({"id": f"tag:{tag}", "label": tag, "kind": "tag", "type": tag})

    return {"nodes": nodes, "edges": edges}
