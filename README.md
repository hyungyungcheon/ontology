# 냉장고 재료 추천 (온톨로지 학습 프로젝트)

owlready2로 만든 작은 온톨로지 + OWL reasoner(HermiT)를 이용해, 냉장고에 있는 재료로
어떤 요리를 만들 수 있는지 추천하는 CLI 프로젝트. 온톨로지의 핵심 개념(클래스, 개체,
속성, 제약, 추론)을 실습으로 익히기 위해 만들었다.

## 실행 방법

CLI:
```bash
pip install -r requirements.txt
python main.py
```

웹 UI (같은 로직을 브라우저로):
```bash
pip install -r requirements.txt
python app.py
```
또는 Windows에서 `run.bat`을 더블클릭 (패키지 설치 확인 + 앱 실행을 한 번에 처리).
`http://127.0.0.1:8000`으로 접속하면 재료 추천 홈 화면, 온톨로지 클래스 계층/지식그래프
뷰어(`/graph`), 프로젝트 계획(`/plan`), 동작 원리 상세 설명(`/how-it-works`)을 볼 수 있다.
`/graph`에서 `.owl` 파일을 다운로드해 Protégé 같은 외부 온톨로지 편집기로 열어볼 수도 있다.

Java(JRE)가 설치되어 있어야 OWL reasoner(HermiT)가 동작한다. Java를 새로 설치한 직후라
PATH가 아직 안 잡혀 있어도, `src/reasoner.py`가 흔한 설치 위치(`C:\Program Files\Microsoft\jdk-*`)를
자동으로 찾아본다.

## 무엇을 배울 수 있는가

- **클래스 계층**: `Ingredient`의 하위 클래스로 `Vegetable`, `Meat`, `Dairy` 등을 정의 (`src/build_ontology.py`)
- **object property**: `requiresIngredient` (Recipe → Ingredient), `substitutableWith` (대칭 관계)
- **disjoint classes**: 한 재료가 동시에 두 카테고리에 속할 수 없다는 제약
- **equivalent class + open-world assumption**:

  ```python
  class VeganRecipe(Recipe):
      equivalent_to = [
          Recipe & requiresIngredient.only(Not(Meat) & Not(Seafood) & Not(Dairy) & Not(Egg))
      ]
  ```

  `sync_reasoner()`를 실행하면 HermiT reasoner가 **클래스 레벨(TBox)**에서 "VeganRecipe는
  항상 DairyFreeRecipe이기도 하다"는, 우리가 직접 선언한 적 없는 관계를 스스로 찾아낸다
  (`src/reasoner.py`의 `get_inferred_subsumptions()`). 이게 진짜 OWL reasoner가 계산한 결과다.

  다만 **개별 요리를 이 클래스의 인스턴스로 자동 편입시키는 것(ABox realize)은 이
  프로젝트에서 시도해봤지만 owlready2에 번들된 HermiT/Pellet 조합에서 신뢰성 있게
  동작하지 않았다** (HermiT CLI는 애초에 realize를 노출하지 않고, Pellet은 실행되지만
  restriction 기반 분류 결과가 항상 비어 있었다 — Jena 로더 경로의 한계로 보인다). 그래서
  "이 요리가 비건인가"는 `get_recipe_tags()`가 재료 클래스를 Python으로 직접 조회해서
  판정한다. 이 삽질 자체가 좋은 교훈이다: OWL 온톨로지 툴체인은 TBox(스키마) 추론은
  꽤 성숙했지만, ABox(개체) 추론은 reasoner/버전에 따라 지원 수준이 크게 다르다.

- **그래프 탐색 기반 추론**: 대체 재료(`substitutableWith`)를 고려해 "지금 있는 재료로
  만들 수 있는 요리"를 찾는 부분(`find_makeable_recipes`)도 순수 Python 그래프 순회로
  구현했다. 대체재 추론까지 OWL 레벨에서 하려면 SWRL 규칙이 필요한데, 난이도가 확
  올라가기 때문에 1차 버전에서는 의도적으로 분리했다.

## 테스트

```bash
pytest
```

Java가 없는 환경에서는 reasoner를 실제로 돌리는 테스트만 자동으로 스킵된다.

## 프로젝트 구조

```
src/
├── data.py               # 시드 데이터: 재료, 요리, 대체 관계
├── build_ontology.py     # 온톨로지 클래스/속성/개체 정의
├── reasoner.py            # reasoner 실행 + 추론 결과 질의
├── cli.py                 # 인터랙티브 CLI
├── ontology_service.py    # 웹 앱용: 온톨로지를 앱 시작 시 1회만 빌드해서 캐싱
└── graph_export.py        # 온톨로지를 클래스 트리 / 개체-그래프 JSON으로 변환
templates/, static/         # 웹 UI (Flask, app.py)
tests/test_reasoner.py     # 자동 분류 및 대체재 로직 검증
main.py                    # CLI 진입점
app.py                      # 웹 앱 진입점
```
