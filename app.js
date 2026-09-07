const SYNTHETIC_DOCUMENTS = [
  {
    doc_id: "SYN-PLAN-001",
    title: "Synthetic Plan Note: Advanced Manufacturing District",
    year: 2025,
    source_type: "demo_policy_note",
    text: "The district will establish a shared robotics testing lab and a procurement channel for small manufacturers. Grants will favor firms that document sensor integration, production data standards, and worker retraining plans. The note does not mention export rebates or preferential tax treatment."
  },
  {
    doc_id: "SYN-REPORT-002",
    title: "Synthetic City Report: Port Logistics Upgrade",
    year: 2025,
    source_type: "demo_city_report",
    text: "The city report prioritizes automated warehousing, port scheduling software, and unified cargo data interfaces. It links infrastructure investment with market access for local logistics providers. Environmental compliance is listed as a review condition rather than a subsidy target."
  },
  {
    doc_id: "SYN-FIRM-003",
    title: "Synthetic Firm Filing: Battery Materials Producer",
    year: 2025,
    source_type: "demo_firm_filing",
    text: "The company describes a pilot line for battery material recycling and an internal data governance board. It reports collaboration with a university lab but states that financing remains uncertain. No municipal talent program is cited."
  },
  {
    doc_id: "SYN-PLAN-004",
    title: "Synthetic Plan Note: Textile Cloud Platform",
    year: 2024,
    source_type: "demo_policy_note",
    text: "The plan supports a cloud platform for textile design orders, supplier matching, and quality traceability. It highlights training vouchers for digital operators and shared infrastructure for small workshops. Research grants are not a central instrument in this note."
  },
  {
    doc_id: "SYN-REPORT-005",
    title: "Synthetic City Report: Agricultural Sensor Network",
    year: 2024,
    source_type: "demo_city_report",
    text: "The report proposes soil sensors, irrigation dashboards, and cooperative data sharing for farms. Funding is assigned to rural broadband infrastructure and technical service teams. The report frames green transition as an expected outcome of water saving."
  },
  {
    doc_id: "SYN-AUDIT-006",
    title: "Synthetic Audit Memo: Evidence Quality Flags",
    year: 2025,
    source_type: "demo_audit_memo",
    text: "Auditors require every extracted claim to carry at least one chunk identifier. Findings with only generic digitalization language should be marked insufficient. Conflicting model labels should trigger manual review before downstream aggregation."
  }
];

const PUBLIC_SCHEMA = {
  answer_id: "string",
  query: "string",
  stance: ["support", "mixed", "insufficient"],
  policy_levers: [
    "finance",
    "talent",
    "infrastructure",
    "market_access",
    "research",
    "green_transition",
    "data_governance"
  ],
  entities: "string[]",
  confidence: "0..1",
  needs_review: "boolean",
  evidence: "[{ chunk_id, doc_id, title, score, snippet }]",
  aggregation: "{ models, agreement, vote_margin }"
};

const MODEL_PROFILES = {
  extractive: { label: "Extractive", weight: 0.38, threshold: 1.2, caution: 0.08 },
  semantic: { label: "Semantic", weight: 0.34, threshold: 0.75, caution: 0.03 },
  skeptical: { label: "Skeptical", weight: 0.28, threshold: 1.55, caution: 0.18 }
};

const LEVER_TERMS = {
  finance: ["grant", "grants", "funding", "financing", "subsidy", "tax"],
  talent: ["worker", "retraining", "training", "voucher", "talent", "operator"],
  infrastructure: ["infrastructure", "broadband", "platform", "lab", "testing", "network"],
  market_access: ["procurement", "market", "access", "supplier", "matching", "channel"],
  research: ["research", "university", "lab", "pilot", "collaboration"],
  green_transition: ["green", "environmental", "recycling", "water", "saving", "compliance"],
  data_governance: ["data", "standards", "interfaces", "governance", "traceability", "dashboard"]
};

const ENTITY_TERMS = [
  "robotics",
  "manufacturing",
  "warehousing",
  "logistics",
  "battery",
  "textile",
  "agricultural",
  "sensor",
  "port",
  "cloud"
];

const EVAL_CASES = [
  {
    id: "case-1",
    label: "Manufacturing levers",
    query: "Which policy levers support digital upgrading in manufacturing?",
    expectedStance: "support",
    expectedLevers: ["finance", "talent", "infrastructure", "data_governance"]
  },
  {
    id: "case-2",
    label: "Logistics access",
    query: "Is there evidence of market access support for logistics providers?",
    expectedStance: "support",
    expectedLevers: ["infrastructure", "market_access", "data_governance"]
  },
  {
    id: "case-3",
    label: "Battery finance",
    query: "Does the battery materials filing provide clear municipal finance support?",
    expectedStance: "mixed",
    expectedLevers: ["research", "green_transition", "data_governance"]
  },
  {
    id: "case-4",
    label: "Generic language",
    query: "Can generic digitalization language alone support a downstream policy label?",
    expectedStance: "insufficient",
    expectedLevers: []
  }
];

const state = {
  chunks: [],
  retrieved: [],
  modelOutputs: [],
  aggregate: null,
  activeStage: "chunks",
  activeCaseId: EVAL_CASES[0].id,
  ratings: {}
};

const $ = (id) => document.getElementById(id);

function tokenize(text) {
  return text
    .toLowerCase()
    .replace(/[^a-z0-9_ ]+/g, " ")
    .split(/\s+/)
    .filter((token) => token.length > 2);
}

function chunkDocuments(maxWords, overlapWords) {
  const chunks = [];
  SYNTHETIC_DOCUMENTS.forEach((doc) => {
    const sentences = doc.text.match(/[^.?!]+[.?!]/g) || [doc.text];
    const words = tokenize(doc.text);
    let index = 0;
    let chunkNo = 1;

    while (index < words.length) {
      const slice = words.slice(index, index + maxWords);
      const rawSnippet = sentences
        .filter((sentence) => slice.some((word) => tokenize(sentence).includes(word)))
        .join(" ")
        .trim();
      chunks.push({
        chunk_id: `${doc.doc_id}-C${String(chunkNo).padStart(2, "0")}`,
        doc_id: doc.doc_id,
        title: doc.title,
        year: doc.year,
        source_type: doc.source_type,
        text: rawSnippet || slice.join(" "),
        tokens: slice
      });
      chunkNo += 1;
      if (index + maxWords >= words.length) break;
      index += Math.max(1, maxWords - overlapWords);
    }
  });
  return chunks;
}

function scoreChunk(query, chunk) {
  const qTokens = new Set(tokenize(query));
  const cTokens = chunk.tokens;
  const text = chunk.text.toLowerCase();
  let overlapScore = 0;
  qTokens.forEach((token) => {
    overlapScore += cTokens.filter((word) => word === token).length;
  });

  let leverScore = 0;
  Object.entries(LEVER_TERMS).forEach(([lever, terms]) => {
    const queryMentionsLever = qTokens.has(lever) || terms.some((term) => qTokens.has(term));
    if (queryMentionsLever || qTokens.has("policy") || qTokens.has("support")) {
      leverScore += terms.filter((term) => text.includes(term)).length * 0.45;
    }
  });

  const recencyScore = chunk.year === 2025 ? 0.1 : 0;
  const auditBoost = qTokens.has("generic") || qTokens.has("evidence") ? (chunk.doc_id.includes("AUDIT") ? 1.4 : 0) : 0;
  return Number((overlapScore + leverScore + recencyScore + auditBoost).toFixed(3));
}

function retrieve(query, chunks, topK) {
  return chunks
    .map((chunk) => ({ ...chunk, score: scoreChunk(query, chunk) }))
    .sort((a, b) => b.score - a.score || a.chunk_id.localeCompare(b.chunk_id))
    .slice(0, topK);
}

function detectLevers(text, threshold = 1) {
  return Object.entries(LEVER_TERMS)
    .map(([lever, terms]) => ({
      lever,
      hits: terms.filter((term) => text.toLowerCase().includes(term)).length
    }))
    .filter((item) => item.hits >= threshold)
    .sort((a, b) => b.hits - a.hits)
    .map((item) => item.lever);
}

function detectEntities(text) {
  const lower = text.toLowerCase();
  return ENTITY_TERMS.filter((term) => lower.includes(term));
}

function inferStance(query, evidenceText, retrieved, profile) {
  const queryLower = query.toLowerCase();
  const negationSignals = ["does not mention", "remains uncertain", "not a central", "generic"];
  const negations = negationSignals.filter((signal) => evidenceText.toLowerCase().includes(signal)).length;
  const totalScore = retrieved.reduce((sum, item) => sum + item.score, 0);
  const hasGenericQuestion = queryLower.includes("generic") || queryLower.includes("alone");

  if (hasGenericQuestion || totalScore < profile.threshold) return "insufficient";
  if (negations > 0 && profile.label !== "Semantic") return "mixed";
  return "support";
}

function simulateModel(modelKey, query, retrieved) {
  const profile = MODEL_PROFILES[modelKey];
  const evidenceText = retrieved.map((item) => item.text).join(" ");
  const leverThreshold = modelKey === "semantic" ? 1 : 2;
  const levers = detectLevers(evidenceText, leverThreshold);
  const entities = detectEntities(evidenceText);
  const stance = inferStance(query, evidenceText, retrieved, profile);
  const rawConfidence = Math.min(0.94, 0.46 + retrieved[0].score / 6 + levers.length * 0.045 - profile.caution);
  const confidence = stance === "insufficient" ? Math.min(rawConfidence, 0.56) : rawConfidence;

  return {
    model: profile.label,
    model_key: modelKey,
    weight: profile.weight,
    stance,
    policy_levers: levers,
    entities,
    confidence: Number(confidence.toFixed(2)),
    evidence_ids: retrieved.slice(0, modelKey === "skeptical" ? 2 : 3).map((item) => item.chunk_id)
  };
}

function aggregateOutputs(query, outputs, retrieved) {
  const stanceWeights = outputs.reduce((acc, output) => {
    acc[output.stance] = (acc[output.stance] || 0) + output.weight;
    return acc;
  }, {});
  const sortedStances = Object.entries(stanceWeights).sort((a, b) => b[1] - a[1]);
  const stance = sortedStances[0]?.[0] || "insufficient";
  const voteMargin = sortedStances.length > 1 ? sortedStances[0][1] - sortedStances[1][1] : sortedStances[0]?.[1] || 0;
  const agreement = sortedStances[0]?.[1] || 0;
  const leverCounts = new Map();
  const entityCounts = new Map();

  outputs.forEach((output) => {
    output.policy_levers.forEach((lever) => leverCounts.set(lever, (leverCounts.get(lever) || 0) + output.weight));
    output.entities.forEach((entity) => entityCounts.set(entity, (entityCounts.get(entity) || 0) + output.weight));
  });

  const policy_levers = [...leverCounts.entries()]
    .filter(([, weight]) => weight >= 0.28 && stance !== "insufficient")
    .sort((a, b) => b[1] - a[1])
    .map(([lever]) => lever);
  const entities = [...entityCounts.entries()]
    .filter(([, weight]) => weight >= 0.28)
    .sort((a, b) => b[1] - a[1])
    .map(([entity]) => entity);
  const averageConfidence = outputs.reduce((sum, output) => sum + output.confidence * output.weight, 0);
  const disagreementPenalty = 1 - Math.min(0.34, Math.max(0, 0.7 - agreement));
  const confidence = Number(Math.max(0.05, Math.min(0.98, averageConfidence * disagreementPenalty)).toFixed(2));
  const needs_review = agreement < 0.67 || stance === "mixed" || retrieved.some((item) => item.doc_id.includes("AUDIT"));

  return {
    answer_id: `DEMO-${Date.now().toString(36).toUpperCase()}`,
    query,
    stance,
    policy_levers,
    entities,
    confidence,
    needs_review,
    evidence: retrieved.map((item) => ({
      chunk_id: item.chunk_id,
      doc_id: item.doc_id,
      title: item.title,
      score: item.score,
      snippet: item.text
    })),
    aggregation: {
      models: outputs.map((output) => output.model),
      agreement: Number(agreement.toFixed(2)),
      vote_margin: Number(voteMargin.toFixed(2))
    }
  };
}

function validateResult(result) {
  const allowedStances = new Set(PUBLIC_SCHEMA.stance);
  const allowedLevers = new Set(PUBLIC_SCHEMA.policy_levers);
  const errors = [];
  if (!allowedStances.has(result.stance)) errors.push("stance");
  if (!Array.isArray(result.policy_levers) || result.policy_levers.some((lever) => !allowedLevers.has(lever))) {
    errors.push("policy_levers");
  }
  if (typeof result.confidence !== "number" || result.confidence < 0 || result.confidence > 1) {
    errors.push("confidence");
  }
  if (!Array.isArray(result.evidence) || result.evidence.some((item) => !item.chunk_id || !item.snippet)) {
    errors.push("evidence");
  }
  return errors;
}

function runPipeline() {
  const query = $("queryInput").value.trim();
  const chunkWords = Number($("chunkSize").value);
  const overlapWords = Number($("overlapSize").value);
  const topK = Number($("topK").value);
  const selectedModels = [...document.querySelectorAll(".modelToggle:checked")].map((input) => input.value);
  const modelKeys = selectedModels.length ? selectedModels : ["extractive"];

  state.chunks = chunkDocuments(chunkWords, overlapWords);
  state.retrieved = retrieve(query, state.chunks, topK);
  state.modelOutputs = modelKeys.map((modelKey) => simulateModel(modelKey, query, state.retrieved));
  state.aggregate = aggregateOutputs(query, state.modelOutputs, state.retrieved);

  renderAll();
}

function renderAll() {
  $("docCount").textContent = `${SYNTHETIC_DOCUMENTS.length} docs`;
  $("chunkCount").textContent = `${state.chunks.length} chunks`;
  $("chunkSizeOut").textContent = $("chunkSize").value;
  $("overlapSizeOut").textContent = $("overlapSize").value;
  $("topKOut").textContent = $("topK").value;
  renderChunks();
  renderRetrieval();
  renderSchema();
  renderModels();
  renderTrace();
  renderEvaluation();
}

function renderChunks() {
  $("chunkStats").textContent = `${state.chunks.length} generated`;
  $("chunksView").innerHTML = state.chunks
    .map((chunk) => `
      <article class="chunk-card">
        <strong>${escapeHtml(chunk.chunk_id)}</strong>
        <p>${escapeHtml(chunk.text)}</p>
        <div class="meta-row">
          <span class="tag">${escapeHtml(chunk.doc_id)}</span>
          <span class="tag">${chunk.year}</span>
          <span class="tag">${escapeHtml(chunk.source_type)}</span>
        </div>
      </article>
    `)
    .join("");
}

function renderRetrieval() {
  $("retrievalStats").textContent = `top ${state.retrieved.length}`;
  $("retrievalView").innerHTML = state.retrieved
    .map((item, index) => `
      <article class="evidence-item">
        <strong>${index + 1}. ${escapeHtml(item.chunk_id)}</strong>
        <span class="score-pill">score ${item.score.toFixed(2)}</span>
        <p>${escapeHtml(item.text)}</p>
        <div class="meta-row">
          <span class="tag">${escapeHtml(item.title)}</span>
          <span class="tag">${escapeHtml(item.source_type)}</span>
        </div>
      </article>
    `)
    .join("");
}

function renderSchema() {
  const errors = state.aggregate ? validateResult(state.aggregate) : [];
  $("validationBadge").textContent = errors.length ? `invalid: ${errors.join(", ")}` : "valid";
  $("schemaStatus").textContent = errors.length ? "schema warning" : "schema ready";
  $("schemaView").textContent = JSON.stringify({ public_schema: PUBLIC_SCHEMA, current_output: state.aggregate }, null, 2);
}

function renderModels() {
  const agreement = state.aggregate?.aggregation.agreement || 0;
  $("agreementBadge").textContent = `agreement ${agreement.toFixed(2)}`;
  $("modelsView").innerHTML = state.modelOutputs
    .map((output) => `
      <article class="model-card">
        <strong>${escapeHtml(output.model)}</strong>
        <p>stance: <b>${escapeHtml(output.stance)}</b></p>
        <p>confidence: <b>${output.confidence.toFixed(2)}</b></p>
        <div class="meta-row">
          ${output.policy_levers.map((lever) => `<span class="tag">${escapeHtml(lever)}</span>`).join("") || '<span class="tag">no lever</span>'}
        </div>
        <div class="meta-row">
          ${output.evidence_ids.map((id) => `<span class="tag">${escapeHtml(id)}</span>`).join("")}
        </div>
      </article>
    `)
    .join("");
}

function renderTrace() {
  const evidence = state.aggregate?.evidence || [];
  $("traceBadge").textContent = `${evidence.length} evidence links`;
  $("traceView").innerHTML = evidence
    .map((item) => `
      <article class="trace-card">
        <strong>${escapeHtml(item.chunk_id)}</strong>
        <p>${highlightTerms(item.snippet, [...(state.aggregate?.policy_levers || []), ...(state.aggregate?.entities || [])])}</p>
        <div class="meta-row">
          <span class="tag">${escapeHtml(item.doc_id)}</span>
          <span class="tag">${escapeHtml(item.title)}</span>
          <span class="score-pill">${item.score.toFixed(2)}</span>
        </div>
      </article>
    `)
    .join("");
}

function renderEvaluation() {
  const activeCase = EVAL_CASES.find((item) => item.id === state.activeCaseId);
  const reviewed = Object.keys(state.ratings).length;
  $("evalSummary").textContent = `${reviewed} reviewed`;
  $("caseButtons").innerHTML = EVAL_CASES.map((item) => `
    <button type="button" class="${item.id === state.activeCaseId ? "active" : ""}" data-case-id="${item.id}">
      ${escapeHtml(item.label)}
    </button>
  `).join("");

  const auto = scoreAgainstGold(state.aggregate, activeCase);
  const ratings = Object.values(state.ratings);
  const accurate = ratings.filter((item) => item.rating === "accurate").length;
  const partial = ratings.filter((item) => item.rating === "partial").length;
  const miss = ratings.filter((item) => item.rating === "miss").length;
  $("metricBadge").textContent = reviewed ? `${accurate} accurate, ${partial} partial, ${miss} miss` : "no ratings";
  $("evalView").innerHTML = `
    <article class="eval-card">
      <strong>Current case</strong>
      <p>${escapeHtml(activeCase.query)}</p>
      <div class="meta-row">
        <span class="tag">expected ${escapeHtml(activeCase.expectedStance)}</span>
        ${activeCase.expectedLevers.map((lever) => `<span class="tag">${escapeHtml(lever)}</span>`).join("") || '<span class="tag">no expected lever</span>'}
      </div>
    </article>
    <article class="eval-card">
      <strong>Automatic check</strong>
      <div class="metric-row">
        <div class="metric"><span>Stance</span><strong>${auto.stanceMatch ? "1" : "0"}</strong></div>
        <div class="metric"><span>Lever F1</span><strong>${auto.leverF1.toFixed(2)}</strong></div>
        <div class="metric"><span>Evidence</span><strong>${auto.hasEvidence ? "1" : "0"}</strong></div>
      </div>
    </article>
    <article class="eval-card">
      <strong>Reviewer log</strong>
      <pre class="code-pane">${escapeHtml(JSON.stringify(state.ratings, null, 2))}</pre>
    </article>
  `;

  document.querySelectorAll(".case-buttons button").forEach((button) => {
    button.addEventListener("click", () => {
      const nextCase = EVAL_CASES.find((item) => item.id === button.dataset.caseId);
      state.activeCaseId = nextCase.id;
      $("queryInput").value = nextCase.query;
      $("reviewNote").value = state.ratings[nextCase.id]?.note || "";
      runPipeline();
      setStage("eval");
    });
  });

  document.querySelectorAll(".rating-buttons button").forEach((button) => {
    button.classList.toggle("selected", state.ratings[state.activeCaseId]?.rating === button.dataset.rating);
  });
}

function scoreAgainstGold(result, gold) {
  if (!result || !gold) return { stanceMatch: false, leverF1: 0, hasEvidence: false };
  const predicted = new Set(result.policy_levers);
  const expected = new Set(gold.expectedLevers);
  const truePositive = [...predicted].filter((lever) => expected.has(lever)).length;
  const precision = predicted.size ? truePositive / predicted.size : expected.size ? 0 : 1;
  const recall = expected.size ? truePositive / expected.size : predicted.size ? 0 : 1;
  const leverF1 = precision + recall ? (2 * precision * recall) / (precision + recall) : 0;
  return {
    stanceMatch: result.stance === gold.expectedStance,
    leverF1,
    hasEvidence: result.evidence.length > 0
  };
}

function setStage(stage) {
  state.activeStage = stage;
  document.querySelectorAll(".stage").forEach((button) => {
    button.classList.toggle("active", button.dataset.stage === stage);
  });
  ["chunks", "retrieval", "schema", "models", "trace", "eval"].forEach((name) => {
    $(`${name}Panel`).classList.toggle("hidden", name !== stage);
  });
}

function highlightTerms(text, terms) {
  const expanded = new Set();
  terms.forEach((term) => {
    expanded.add(term.replace("_", " "));
    (LEVER_TERMS[term] || []).forEach((word) => expanded.add(word));
  });
  const needles = [...expanded].filter(Boolean).sort((a, b) => b.length - a.length);
  let escaped = escapeHtml(text);
  needles.forEach((term) => {
    const pattern = new RegExp(`\\b(${escapeRegex(escapeHtml(term))})\\b`, "gi");
    escaped = escaped.replace(pattern, "<mark>$1</mark>");
  });
  return escaped;
}

function escapeHtml(value) {
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function escapeRegex(value) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function bindEvents() {
  $("runBtn").addEventListener("click", runPipeline);
  $("copyBtn").addEventListener("click", async () => {
    const payload = JSON.stringify(state.aggregate, null, 2);
    try {
      await navigator.clipboard.writeText(payload);
      $("copyBtn").textContent = "Copied";
      window.setTimeout(() => ($("copyBtn").textContent = "Copy JSON"), 1200);
    } catch {
      $("schemaView").textContent = payload;
      setStage("schema");
    }
  });

  ["chunkSize", "overlapSize", "topK"].forEach((id) => {
    $(id).addEventListener("input", runPipeline);
  });

  document.querySelectorAll(".modelToggle").forEach((input) => {
    input.addEventListener("change", runPipeline);
  });

  document.querySelectorAll(".stage").forEach((button) => {
    button.addEventListener("click", () => setStage(button.dataset.stage));
  });

  document.querySelectorAll(".rating-buttons button").forEach((button) => {
    button.addEventListener("click", () => {
      state.ratings[state.activeCaseId] = {
        rating: button.dataset.rating,
        note: $("reviewNote").value.trim(),
        output_id: state.aggregate.answer_id,
        reviewed_at: new Date().toISOString()
      };
      renderEvaluation();
    });
  });

  $("reviewNote").addEventListener("change", () => {
    if (!state.ratings[state.activeCaseId]) return;
    state.ratings[state.activeCaseId].note = $("reviewNote").value.trim();
    renderEvaluation();
  });
}

bindEvents();
runPipeline();
