export const BACKEND_URL = import.meta.env.VITE_BACKEND_URL;
export const SELECTED_THREAD_ID_KEY = "madagents_selected_thread_id";

// Theme tokens are shared across components to allow strict equality checks.
export const lightTheme = {
  appBg: "#f3f4f6",
  cardBg: "#ffffff",
  text: "#111827",
  userBubbleBg: "#2563eb",
  userBubbleText: "#ffffff",
  botBubbleBg: "#e5e7eb",
  botBubbleText: "#111827",
  headerBorder: "#e5e7eb",
  inputBg: "#f9fafb",
  border: "#d1d5db",
  errorText: "#b91c1c",
  interruptBg: "#dc2626",
  disabledBg: "#6b7280",
  accentDark: "#1d4ed8",
};

export const darkTheme = {
  appBg: "#020617",
  cardBg: "#020617",
  text: "#e5e7eb",
  userBubbleBg: "#2563eb",
  userBubbleText: "#ffffff",
  botBubbleBg: "#111827",
  botBubbleText: "#e5e7eb",
  headerBorder: "#1f2937",
  inputBg: "#020617",
  border: "#374151",
  errorText: "#fca5a5",
  interruptBg: "#dc2626",
  disabledBg: "#6b7280",
  accentDark: "#1d4ed8",
};

export const SUPPORTED_MODELS = [
  "gpt-5.4-nano",
  "gpt-5.4-mini",
  "gpt-5-nano",
  "gpt-5-mini",
  "gpt-5.1",
  "gpt-5.2",
  "gpt-5.4",
  "claude-opus-4-7",
  "claude-opus-4-6",
  "claude-sonnet-4-6",
  "claude-haiku-4-5",
];

export const MODEL_PROVIDER_PREFIXES = {
  OpenAI: ["gpt-"],
  Anthropic: ["claude-"],
};

export const MODEL_PROVIDER_ORDER = ["OpenAI", "Anthropic", "Other"];

export function inferProviderFromModel(model) {
  const normalized = String(model || "").toLowerCase();
  for (const [provider, prefixes] of Object.entries(MODEL_PROVIDER_PREFIXES)) {
    const lowerPrefixes = prefixes.map((p) => p.toLowerCase());
    if (lowerPrefixes.some((prefix) => normalized.startsWith(prefix))) {
      return provider.toLowerCase();
    }
  }
  return null;
}

export function groupModelsByProvider(models) {
  const groups = new Map();
  const other = [];

  const entries = Object.entries(MODEL_PROVIDER_PREFIXES);
  const normalizedEntries = entries.map(([label, prefixes]) => [
    label,
    Array.isArray(prefixes) ? prefixes.map((p) => p.toLowerCase()) : [],
  ]);

  models.forEach((model) => {
    const normalized = String(model || "").toLowerCase();
    let matched = false;
    for (const [label, prefixes] of normalizedEntries) {
      if (prefixes.some((prefix) => normalized.startsWith(prefix))) {
        const list = groups.get(label) || [];
        list.push(model);
        groups.set(label, list);
        matched = true;
        break;
      }
    }
    if (!matched) {
      other.push(model);
    }
  });

  const openAiList = groups.get("OpenAI");
  if (openAiList && openAiList.length) {
    groups.set("OpenAI", [...openAiList].reverse());
  }

  const ordered = [];
  MODEL_PROVIDER_ORDER.forEach((label) => {
    if (label === "Other") {
      if (other.length) {
        ordered.push({ label, models: other });
      }
      return;
    }
    const list = groups.get(label);
    if (list && list.length) {
      ordered.push({ label, models: list });
    }
  });

  for (const [label, list] of groups.entries()) {
    if (MODEL_PROVIDER_ORDER.includes(label)) {
      continue;
    }
    ordered.push({ label, models: list });
  }

  if (!MODEL_PROVIDER_ORDER.includes("Other") && other.length) {
    ordered.push({ label: "Other", models: other });
  }

  return ordered;
}

/**
 * Model capability tiers — mirrors config.py OPENAI_MODEL_TIERS / ANTHROPIC_MODEL_TIERS.
 */
const MODEL_TIERS = {
  "gpt-5.4": "strongest",
  "gpt-5.2": "strongest",
  "gpt-5.1": "strongest",
  "gpt-5.4-mini": "mid-tier",
  "gpt-5-mini": "mid-tier",
  "gpt-5.4-nano": "lightest",
  "gpt-5-nano": "lightest",
  "claude-opus-4-7": "strongest",
  "claude-opus-4-6": "strongest",
  "claude-sonnet-4-6": "mid-tier",
  "claude-haiku-4-5": "lightest",
};

/**
 * Pick one model per capability tier for routing display.
 * Mirrors backend models_for_routing(): strongestModel is the
 * "strongest" representative; other tiers keep the first match in list order.
 */
export function modelsForRouting(providerModels, strongestModel) {
  const strongestTier = MODEL_TIERS[strongestModel] || "unknown";
  const tierRep = { [strongestTier]: strongestModel };
  for (const m of providerModels) {
    const tier = MODEL_TIERS[m] || "unknown";
    if (!(tier in tierRep)) tierRep[tier] = m;
  }
  return providerModels.filter(
    (m) => tierRep[MODEL_TIERS[m] || "unknown"] === m
  );
}

/**
 * Mirrors backend _strongest_model_for_provider: use orchestrator model if
 * it's in the "strongest" tier, otherwise fall back to a default.
 */
export function strongestModelForProvider(orchestratorModel, provider) {
  const tier = MODEL_TIERS[orchestratorModel] || "unknown";
  if (tier === "strongest") return orchestratorModel;
  return provider === "anthropic" ? "claude-opus-4-7" : "gpt-5.2";
}

export const VERBOSITY_LEVELS = ["low", "medium", "high"];
export const REASONING_EFFORT_LEVELS = ["minimal", "low", "medium", "high"];

export const REVIEWER_AGENTS = [
  "plan_reviewer",
  "verification_reviewer",
  "presentation_reviewer",
];

export const WORKER_AGENTS = [
  "madgraph_operator",
  "script_operator",
  "plotter",
  "user_cli_operator",
  "pdf_reader",
  "researcher",
  "physics_expert",
];

export const AGENT_ORDER = [
  "orchestrator",
  "planner",
  "plan_updater",
  "summarizer",
  ...REVIEWER_AGENTS,
  ...WORKER_AGENTS,
];

export const CONTROL_CHAR_REGEX =
  /[\u0000-\u0008\u000B\u000C\u000E-\u001F\u007F-\u009F]/g;

