// 체크박스 <-> 쉼표 구분 텍스트 입력을 양방향으로 동기화한다.
// window.INGREDIENTS_DATA: { ingredient_id: [class_name, korean_label], ... } (index.html에서 주입)
(function () {
  const data = window.INGREDIENTS_DATA || {};
  const textInput = document.getElementById("fridge-text");
  const checkboxes = document.querySelectorAll('input[name="ingredients"]');
  if (!textInput || checkboxes.length === 0) return;

  const labelToId = {};
  Object.keys(data).forEach((id) => {
    const label = data[id][1];
    labelToId[label] = id;
  });

  let syncing = false;

  function syncTextFromCheckboxes() {
    if (syncing) return;
    syncing = true;
    const labels = Array.from(checkboxes)
      .filter((cb) => cb.checked)
      .map((cb) => data[cb.value][1]);
    textInput.value = labels.join(", ");
    syncing = false;
  }

  function syncCheckboxesFromText() {
    if (syncing) return;
    syncing = true;
    const labels = textInput.value
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean);
    const ids = new Set(labels.map((label) => labelToId[label]).filter(Boolean));
    checkboxes.forEach((cb) => {
      cb.checked = ids.has(cb.value);
    });
    syncing = false;
  }

  checkboxes.forEach((cb) => cb.addEventListener("change", syncTextFromCheckboxes));
  textInput.addEventListener("input", syncCheckboxesFromText);

  syncTextFromCheckboxes();
})();
