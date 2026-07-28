// /api/graph에서 받은 노드/엣지 JSON을 순수 SVG로 그린다.
// 외부 라이브러리(D3 등) 없이 고정된 2~3열 레이아웃만으로 충분히 읽기 좋다는 판단.
(async function () {
  const svg = document.getElementById("graph-svg");
  if (!svg) return;

  const svgns = "http://www.w3.org/2000/svg";
  function el(tag, attrs) {
    const e = document.createElementNS(svgns, tag);
    for (const key in attrs) e.setAttribute(key, attrs[key]);
    return e;
  }

  const res = await fetch("/api/graph");
  const data = await res.json();

  const width = 760;
  const colX = { ingredient: 110, recipe: 400, tag: 660 };
  const rowGap = 24;
  const groupGap = 16;
  const marginY = 20;

  const ingredientNodes = data.nodes.filter((n) => n.kind === "ingredient");
  const recipeNodes = data.nodes.filter((n) => n.kind === "recipe");
  const tagNodes = data.nodes.filter((n) => n.kind === "tag");

  const byType = {};
  ingredientNodes.forEach((n) => {
    (byType[n.type] = byType[n.type] || []).push(n);
  });
  const types = Object.keys(byType).sort();

  const positions = {};

  let y = marginY;
  types.forEach((type) => {
    byType[type].forEach((n) => {
      positions[n.id] = { x: colX.ingredient, y };
      y += rowGap;
    });
    y += groupGap;
  });
  const ingredientsHeight = y;

  let ry = Math.max(marginY, (ingredientsHeight - recipeNodes.length * rowGap) / 2);
  recipeNodes.forEach((n) => {
    positions[n.id] = { x: colX.recipe, y: ry };
    ry += rowGap;
  });

  let ty = Math.max(marginY, (ingredientsHeight - tagNodes.length * rowGap) / 2);
  tagNodes.forEach((n) => {
    positions[n.id] = { x: colX.tag, y: ty };
    ty += rowGap;
  });

  const totalHeight = Math.max(ingredientsHeight, ry, ty) + marginY;
  svg.setAttribute("viewBox", `0 0 ${width} ${totalHeight}`);
  svg.setAttribute("height", Math.min(totalHeight, 900));

  const palette = ["#2f6f4f", "#b45309", "#1d4ed8", "#be123c", "#0f766e", "#7c3aed", "#ca8a04", "#334155"];
  const typeColors = {};
  types.forEach((t, i) => (typeColors[t] = palette[i % palette.length]));
  typeColors["Recipe"] = "#111827";
  typeColors["Vegan"] = "#2f6f4f";
  typeColors["DairyFree"] = "#b45309";

  const relationColor = {
    requiresIngredient: "#2f6f4f",
    substitutableWith: "#b45309",
    classified_as: "#6d28d9",
  };
  const relationDash = {
    requiresIngredient: "none",
    substitutableWith: "4,3",
    classified_as: "1,3",
  };

  const edgeGroup = el("g", {});
  const nodeGroup = el("g", {});
  svg.appendChild(edgeGroup);
  svg.appendChild(nodeGroup);

  const nodesById = {};
  data.nodes.forEach((n) => (nodesById[n.id] = n));

  const edgeEls = [];
  data.edges.forEach((edge) => {
    const s = positions[edge.source];
    const t = positions[edge.target];
    if (!s || !t) return;

    let d;
    if (s.x === t.x) {
      const midY = (s.y + t.y) / 2;
      const bulge = s.x - 34;
      d = `M ${s.x} ${s.y} Q ${bulge} ${midY} ${t.x} ${t.y}`;
    } else {
      d = `M ${s.x} ${s.y} L ${t.x} ${t.y}`;
    }

    const path = el("path", {
      d,
      class: "graph-edge",
      stroke: relationColor[edge.relation] || "#999",
      "stroke-dasharray": relationDash[edge.relation] || "none",
    });
    path.dataset.source = edge.source;
    path.dataset.target = edge.target;
    edgeGroup.appendChild(path);
    edgeEls.push(path);
  });

  const nodeEls = [];
  Object.keys(positions).forEach((id) => {
    const pos = positions[id];
    const node = nodesById[id];
    const g = el("g", { class: "graph-node", transform: `translate(${pos.x},${pos.y})` });
    const color = typeColors[node.type] || "#555";
    g.appendChild(el("circle", { r: node.kind === "tag" ? 8 : 6, fill: color }));

    const label = el("text", {
      class: "graph-node-label",
      x: node.kind === "ingredient" ? -10 : 10,
      y: 4,
      "text-anchor": node.kind === "ingredient" ? "end" : "start",
    });
    label.textContent = node.label;
    g.appendChild(label);

    g.dataset.id = id;
    g.addEventListener("mouseenter", () => highlight(id));
    g.addEventListener("mouseleave", clearHighlight);

    nodeGroup.appendChild(g);
    nodeEls.push(g);
  });

  function highlight(id) {
    edgeEls.forEach((p) => {
      if (p.dataset.source === id || p.dataset.target === id) {
        p.classList.add("highlight");
      } else {
        p.classList.add("dim");
      }
    });
    nodeEls.forEach((g) => {
      const nid = g.dataset.id;
      const connected =
        nid === id ||
        data.edges.some(
          (e) => (e.source === id && e.target === nid) || (e.target === id && e.source === nid)
        );
      if (!connected) g.classList.add("dim");
    });
  }

  function clearHighlight() {
    edgeEls.forEach((p) => {
      p.classList.remove("highlight");
      p.classList.remove("dim");
    });
    nodeEls.forEach((g) => g.classList.remove("dim"));
  }
})();
