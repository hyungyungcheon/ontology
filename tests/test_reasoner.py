import shutil

import pytest

from src.data import SUBSTITUTES
from src.reasoner import (
    build_and_classify,
    build_substitute_map,
    find_makeable_recipes,
    get_inferred_subsumptions,
    get_recipe_tags,
)

JAVA_AVAILABLE = shutil.which("java") is not None


def test_substitute_map_is_bidirectional():
    substitute_map = build_substitute_map({}, SUBSTITUTES)
    assert "soy_milk" in substitute_map["milk"]
    assert "milk" in substitute_map["soy_milk"]


def test_direct_makeable_recipe():
    recipes_data = {"r1": ("테스트요리", ["rice", "salt"])}
    substitute_map = build_substitute_map({}, [])
    result = find_makeable_recipes(["rice", "salt", "egg"], recipes_data, substitute_map)
    assert result["r1"]["status"] == "direct"


def test_substitute_makeable_recipe():
    recipes_data = {"r1": ("우유죽", ["rice", "milk", "salt"])}
    substitute_map = build_substitute_map({}, SUBSTITUTES)
    result = find_makeable_recipes(["rice", "salt", "soy_milk"], recipes_data, substitute_map)
    assert result["r1"]["status"] == "substitute"
    assert result["r1"]["substitutions"] == {"milk": "soy_milk"}


def test_missing_recipe():
    recipes_data = {"r1": ("치즈오믈렛", ["egg", "cheese", "butter", "salt"])}
    substitute_map = build_substitute_map({}, SUBSTITUTES)
    result = find_makeable_recipes(["salt"], recipes_data, substitute_map)
    assert result["r1"]["status"] == "missing"
    assert set(result["r1"]["missing"]) == {"egg", "cheese", "butter"}


def test_get_recipe_tags_vegan_and_dairy_free():
    assert set(get_recipe_tags(["tofu", "soy_sauce", "green_onion"])) == {"Vegan", "DairyFree"}


def test_get_recipe_tags_dairy_free_but_not_vegan():
    tags = set(get_recipe_tags(["shrimp", "onion", "soy_sauce"]))
    assert "DairyFree" in tags
    assert "Vegan" not in tags


def test_get_recipe_tags_neither():
    tags = set(get_recipe_tags(["egg", "cheese", "butter"]))
    assert "Vegan" not in tags
    assert "DairyFree" not in tags


@pytest.mark.skipif(not JAVA_AVAILABLE, reason="Java(JRE)가 없어 OWL reasoner를 실행할 수 없음")
def test_reasoner_infers_vegan_implies_dairy_free():
    onto, _, _ = build_and_classify()
    facts = get_inferred_subsumptions(onto)
    assert any("DairyFreeRecipe" in fact for fact in facts)
