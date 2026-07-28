"""냉장고 재료/요리 시드 데이터.

온톨로지 개체(individual)의 ID는 영문(IRI에 안전하게 쓰기 위함)으로 두고,
화면에 보여줄 한글 이름은 label로 따로 관리한다.
"""

# ingredient_id -> (class_name, 한글_이름)
INGREDIENTS = {
    "green_onion": ("Vegetable", "대파"),
    "onion": ("Vegetable", "양파"),
    "zucchini": ("Vegetable", "애호박"),
    "bean_sprout": ("Vegetable", "콩나물"),
    "tofu": ("Legume", "두부"),
    "soy_milk": ("Legume", "두유"),
    "flour": ("Grain", "밀가루"),
    "rice": ("Grain", "쌀"),
    "soy_sauce": ("Seasoning", "간장"),
    "salt": ("Seasoning", "소금"),
    "sesame_oil": ("Seasoning", "참기름"),
    "cooking_oil": ("Seasoning", "식용유"),
    "pork": ("Meat", "돼지고기"),
    "beef": ("Meat", "소고기"),
    "shrimp": ("Seafood", "새우"),
    "milk": ("Dairy", "우유"),
    "cheese": ("Dairy", "치즈"),
    "butter": ("Dairy", "버터"),
    "egg": ("Egg", "계란"),
}

# 대체 가능한 재료 쌍 (양방향으로 취급됨 - substitutableWith는 symmetric property)
SUBSTITUTES = [
    ("milk", "soy_milk"),
    ("butter", "cooking_oil"),
    ("egg", "tofu"),
]

# recipe_id -> (한글_이름, [필요한 ingredient_id, ...])
RECIPES = {
    "egg_fried_rice": ("계란볶음밥", ["rice", "egg", "green_onion", "soy_sauce", "cooking_oil"]),
    "braised_tofu": ("두부조림", ["tofu", "soy_sauce", "green_onion", "sesame_oil", "cooking_oil"]),
    "milk_porridge": ("우유죽", ["rice", "milk", "salt"]),
    "zucchini_soup": ("애호박국", ["zucchini", "onion", "soy_sauce", "salt"]),
    "bean_sprout_soup": ("콩나물국", ["bean_sprout", "green_onion", "salt", "soy_sauce"]),
    "shrimp_stir_fry": ("새우볶음", ["shrimp", "onion", "green_onion", "soy_sauce", "sesame_oil"]),
    "beef_radish_soup": ("소고기무국", ["beef", "green_onion", "sesame_oil", "soy_sauce"]),
    "cheese_omelette": ("치즈오믈렛", ["egg", "cheese", "butter", "salt"]),
}
