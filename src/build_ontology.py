"""owlready2로 냉장고/요리 온톨로지를 프로그래밍 방식으로 정의한다.

핵심 온톨로지 개념 시연:
- 클래스 계층 (Ingredient의 하위 클래스들)
- object property (requiresIngredient, substitutableWith)
- disjoint classes (한 재료는 동시에 두 카테고리에 속할 수 없음)
- equivalent class를 이용한 클래스 간 자동 추론 (VeganRecipe, DairyFreeRecipe)
  -> sync_reasoner()를 실행하면 HermiT이 "VeganRecipe는 항상 DairyFreeRecipe이기도
     하다" 같은, 우리가 직접 선언하지 않은 클래스 관계(subsumption)를 스스로
     찾아낸다 (src/reasoner.py의 get_inferred_subsumptions 참고).

     참고: 개별 요리 인스턴스를 이 클래스에 자동으로 편입시키는 것(ABox realize)은
     owlready2에 번들된 HermiT/Pellet CLI 조합에서는 신뢰성 있게 동작하지 않아
     (Pellet은 N-Triples/Jena 로더 경로에서 restriction이 유실되는 것으로 보임),
     레시피별 태그는 reasoner.get_recipe_tags()에서 같은 조건을 Python으로
     직접 평가한다.
"""

from owlready2 import (
    Thing,
    ObjectProperty,
    SymmetricProperty,
    AllDisjoint,
    Not,
    get_ontology,
)

from src.data import INGREDIENTS, RECIPES, SUBSTITUTES

ONTOLOGY_IRI = "http://example.org/fridge_ontology.owl"


def build_ontology():
    """온톨로지를 새로 빌드하고 (onto, ingredients, recipes) 를 반환한다.

    ingredients: ingredient_id -> owlready2 individual
    recipes: recipe_id -> owlready2 individual
    """
    onto = get_ontology(ONTOLOGY_IRI)

    with onto:
        class Ingredient(Thing):
            pass

        class Vegetable(Ingredient):
            pass

        class Legume(Ingredient):
            pass

        class Grain(Ingredient):
            pass

        class Seasoning(Ingredient):
            pass

        class Meat(Ingredient):
            pass

        class Seafood(Ingredient):
            pass

        class Dairy(Ingredient):
            pass

        class Egg(Ingredient):
            pass

        AllDisjoint([Vegetable, Legume, Grain, Seasoning, Meat, Seafood, Dairy, Egg])

        class Recipe(Thing):
            pass

        class requiresIngredient(Recipe >> Ingredient):
            pass

        class substitutableWith(Ingredient >> Ingredient, SymmetricProperty):
            pass

        # NOTE: "only"(allValuesFrom)를 쓰는 이유 - OWL은 open-world assumption이라
        # Not(requiresIngredient.some(Meat)) 같은 존재 한정 부정은 "고기 재료가 없다는 게
        # 증명된 적이 없을 뿐" 이라서 reasoner가 만족 여부를 확정할 수 없다. 반대로
        # requiresIngredient.only(...)는 "이미 선언된 모든 필요 재료 각각"에 대해서만
        # 조건을 검사하므로, 각 재료의 클래스가 알려져 있는 한 확정적으로 판정 가능하다.
        class VeganRecipe(Recipe):
            equivalent_to = [
                Recipe
                & requiresIngredient.only(Not(Meat) & Not(Seafood) & Not(Dairy) & Not(Egg))
            ]

        class DairyFreeRecipe(Recipe):
            equivalent_to = [Recipe & requiresIngredient.only(Not(Dairy))]

        ingredient_classes = {
            "Vegetable": Vegetable,
            "Legume": Legume,
            "Grain": Grain,
            "Seasoning": Seasoning,
            "Meat": Meat,
            "Seafood": Seafood,
            "Dairy": Dairy,
            "Egg": Egg,
        }

        ingredients = {}
        for ingredient_id, (class_name, korean_label) in INGREDIENTS.items():
            cls = ingredient_classes[class_name]
            individual = cls(ingredient_id)
            individual.label = [korean_label]
            ingredients[ingredient_id] = individual

        for a_id, b_id in SUBSTITUTES:
            ingredients[a_id].substitutableWith.append(ingredients[b_id])

        recipes = {}
        for recipe_id, (korean_label, required_ids) in RECIPES.items():
            individual = Recipe(recipe_id)
            individual.label = [korean_label]
            individual.requiresIngredient = [ingredients[i] for i in required_ids]
            recipes[recipe_id] = individual

    return onto, ingredients, recipes
