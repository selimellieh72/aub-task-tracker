// Task Tracker frontend logic (per ADR-001).
// Loads tasks from the FastAPI backend and renders them into the Kanban board.

const API_BASE = "http://localhost:8000";
const STATUSES = ["ToDo", "InProgress", "Done"];
const PRIORITY_ORDER = { High: 0, Medium: 1, Low: 2 };

// All tasks currently loaded from the server, in server order.
let tasks = [];

const banner = document.getElementById("status-banner");

// ---------------------------------------------------------------- helpers

// UI state: "loading" | "ready" | "empty" | "error".
// The board itself is always rendered; the state only drives the banner
// (and a body[data-state] hook for CSS).
function setState(state, message = "") {
  document.body.dataset.state = state;
  banner.replaceChildren();
  banner.hidden = !message;
  if (!message) return;

  banner.append(message);
  if (state === "error") {
    const retry = document.createElement("button");
    retry.type = "button";
    retry.className = "button button-small";
    retry.textContent = "Retry";
    retry.addEventListener("click", fetchTasks);
    banner.append(" ", retry);
  }
}

function comparePriorityThenId(a, b) {
  const byPriority = PRIORITY_ORDER[a.priority] - PRIORITY_ORDER[b.priority];
  return byPriority !== 0 ? byPriority : a.id - b.id;
}

// Builds one <li class="card"> using the same structure as the static markup.
// Every piece of task text goes through textContent, so it is escaped by the
// DOM and never interpreted as HTML.
function createCard(task) {
  const card = document.createElement("li");
  card.className = "card";
  card.dataset.id = String(task.id);
  card.dataset.priority = task.priority;

  const title = document.createElement("h3");
  title.className = "card-title";
  title.textContent = task.title;
  card.append(title);

  if (task.description) {
    const description = document.createElement("p");
    description.className = "card-description";
    description.textContent = task.description;
    card.append(description);
  }

  const meta = document.createElement("div");
  meta.className = "card-meta";

  const priority = document.createElement("span");
  priority.className = "priority";
  priority.dataset.priority = task.priority;
  priority.textContent = task.priority;

  const assignee = document.createElement("span");
  assignee.className = "assignee";
  assignee.textContent = task.assignee || "Unassigned";

  meta.append(priority, assignee);
  card.append(meta);

  const editButton = document.createElement("button");
  editButton.type = "button";
  editButton.className = "button button-small edit-button";
  editButton.textContent = "Edit";
  card.append(editButton);

  return card;
}

// ---------------------------------------------------------------- rendering

function renderBoard(taskList) {
  for (const status of STATUSES) {
    const section = document.querySelector(`.column[data-status="${status}"]`);
    const list = section.querySelector(".cards");
    const inColumn = taskList
      .filter((task) => task.status === status)
      .sort(comparePriorityThenId);

    // Clear and rebuild. An empty <ul> stays in the DOM (the placeholder text
    // is CSS-only), so the column remains a valid drop target later.
    list.replaceChildren(...inColumn.map(createCard));
    section.querySelector(".column-count").textContent = String(inColumn.length);
  }
}

// ---------------------------------------------------------------- data

async function fetchTasks() {
  setState("loading", "Loading tasks…");
  try {
    const response = await fetch(`${API_BASE}/tasks`);
    if (!response.ok) {
      throw new Error(`Server responded with ${response.status}`);
    }
    tasks = await response.json();
    renderBoard(tasks);
    if (tasks.length === 0) {
      setState("empty", "No tasks yet. Create one to get started.");
    } else {
      setState("ready");
    }
  } catch (error) {
    renderBoard([]);
    setState("error", `Could not load tasks: ${error.message}`);
  }
}

document.addEventListener("DOMContentLoaded", fetchTasks);
