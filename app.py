"""냉장고 재료 추천 웹 앱 (Flask).

python app.py로 실행하면 http://127.0.0.1:5000 에서 확인할 수 있다.
온톨로지 빌드 + HermiT reasoner 실행은 ontology_service에서 앱 시작 시 1회만 하고,
요청마다는 그 결과를 재사용한다.
"""

from collections import defaultdict
from io import BytesIO

from flask import Flask, Response, render_template, request

from src.data import INGREDIENTS, RECIPES
from src.graph_export import build_class_tree, build_instance_graph
from src.ontology_service import get_state
from src.reasoner import find_makeable_recipes, get_recipe_tags

app = Flask(__name__)


def _ingredients_by_category():
    groups = defaultdict(list)
    for ingredient_id, (class_name, label) in INGREDIENTS.items():
        groups[class_name].append((ingredient_id, label))
    return dict(sorted(groups.items()))


@app.route("/", methods=["GET", "POST"])
def index():
    state = get_state()
    selected_ids = set(request.form.getlist("ingredients")) if request.method == "POST" else set()

    recipe_tags = {recipe_id: get_recipe_tags(required_ids) for recipe_id, (_, required_ids) in RECIPES.items()}

    results = None
    if request.method == "POST":
        makeable = find_makeable_recipes(selected_ids, RECIPES, state["substitute_map"])
        results = {
            "direct": [rid for rid, r in makeable.items() if r["status"] == "direct"],
            "substitute": [(rid, makeable[rid]["substitutions"]) for rid in makeable if makeable[rid]["status"] == "substitute"],
            "missing": [(rid, makeable[rid]["missing"]) for rid in makeable if makeable[rid]["status"] == "missing"],
        }

    return render_template(
        "index.html",
        ingredient_groups=_ingredients_by_category(),
        ingredients=INGREDIENTS,
        recipes=RECIPES,
        recipe_tags=recipe_tags,
        selected_ids=selected_ids,
        results=results,
        subsumption_facts=state["subsumption_facts"],
        reasoner_error=state["error"],
    )


@app.route("/graph")
def graph():
    state = get_state()
    class_tree = build_class_tree(state["onto"]) if state["onto"] is not None else None
    return render_template("graph.html", class_tree=class_tree, reasoner_error=state["error"])


@app.route("/api/graph")
def api_graph():
    return build_instance_graph()


@app.route("/ontology.owl")
def ontology_owl():
    state = get_state()
    if state["onto"] is None:
        return Response(
            "온톨로지를 빌드하지 못했습니다: " + (state["error"] or ""),
            status=503,
            mimetype="text/plain",
        )
    buffer = BytesIO()
    state["onto"].save(file=buffer, format="rdfxml")
    return Response(
        buffer.getvalue(),
        mimetype="application/rdf+xml",
        headers={"Content-Disposition": "attachment; filename=fridge_ontology.owl"},
    )


@app.route("/plan")
def plan():
    return render_template("plan.html")


@app.route("/how-it-works")
def how_it_works():
    return render_template("how_it_works.html")


if __name__ == "__main__":
    # 요청이 들어오기 전에 미리 한 번 빌드해둔다. 지연 빌드로 두면 거의 동시에
    # 들어온 첫 몇 개 요청이 동시에 build_and_classify()를 호출해 owlready2의
    # 공유 SQLite 저장소에 경쟁 상태를 일으킬 수 있다 (실제로 겪은 문제).
    get_state()
    app.run(debug=True, use_reloader=False, port=8000)
