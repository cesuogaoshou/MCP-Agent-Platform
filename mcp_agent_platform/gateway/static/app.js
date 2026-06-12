const state = {
  sessionId: null,
};

const nodes = {
  form: document.querySelector("#chat-form"),
  input: document.querySelector("#message-input"),
  messages: document.querySelector("#message-list"),
  events: document.querySelector("#event-list"),
  tools: document.querySelector("#tool-list"),
  refreshTools: document.querySelector("#refresh-tools"),
  sessionLabel: document.querySelector("#session-label"),
  serviceStatus: document.querySelector("#service-status"),
};

function renderTool(tool) {
  const item = document.createElement("div");
  item.className = "tool-item";
  item.innerHTML = `<strong>${escapeHtml(tool.name)}</strong><span>${escapeHtml(
    tool.description || "No description",
  )}</span>`;
  return item;
}

function renderMessage(message) {
  const item = document.createElement("div");
  item.className = `message ${message.role}`;
  item.textContent = message.content;
  return item;
}

function renderEvent(event) {
  const item = document.createElement("div");
  item.className = "event-item";
  item.dataset.type = event.type;
  item.innerHTML = `<strong>${escapeHtml(event.type)}</strong><span>${escapeHtml(
    event.message,
  )}</span>`;
  return item;
}

async function loadTools() {
  const response = await fetch("/tools");
  if (!response.ok) {
    nodes.tools.textContent = "Tool registry is not available.";
    return;
  }

  const payload = await response.json();
  nodes.tools.replaceChildren(...payload.tools.map(renderTool));
}

async function loadHealth() {
  const response = await fetch("/health");
  if (!response.ok) {
    nodes.serviceStatus.textContent = "Service unavailable";
    return;
  }

  const payload = await response.json();
  nodes.serviceStatus.textContent = `${payload.service} ${payload.version}`;
}

async function submitChat(event) {
  event.preventDefault();
  const message = nodes.input.value.trim();
  if (!message) {
    return;
  }

  const body = { message };
  if (state.sessionId) {
    body.session_id = state.sessionId;
  }

  const response = await fetch("/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    nodes.events.textContent = "Chat request failed.";
    return;
  }

  const payload = await response.json();
  state.sessionId = payload.session_id;
  nodes.sessionLabel.textContent = `Session ${state.sessionId.slice(0, 8)}`;
  nodes.messages.replaceChildren(...payload.messages.map(renderMessage));
  nodes.events.replaceChildren(...payload.events.map(renderEvent));
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

nodes.form.addEventListener("submit", submitChat);
nodes.refreshTools.addEventListener("click", loadTools);

loadHealth();
loadTools();
