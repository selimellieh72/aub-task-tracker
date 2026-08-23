// Task Tracker frontend logic (per ADR-001).
// Loads tasks from the FastAPI backend and renders them into the Kanban board.

const API_BASE = "http://localhost:8000";
const STATUSES = ["ToDo", "InProgress", "Done"];
const PRIORITY_ORDER = { High: 0, Medium: 1, Low: 2 };

// All tasks currently loaded from the server, in server order.
let tasks = [];

const banner = document.getElementById("status-banner");

// ---------------------------------------------------------------- helpers

function setBanner(message) {
  // An empty message hides the banner entirely.
  banner.textContent = message;
  banner.hidden = !message;
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
    const column = document.querySelector(`.column[data-status="${status}"] .cards`);
    column.replaceChildren(); // clear; the column itself stays visible

    taskList
      .filter((task) => task.status === status)
      .sort(comparePriorityThenId)
      .forEach((task) => column.append(createCard(task)));
  }
}

// ---------------------------------------------------------------- data

async function fetchTasks() {
  setBanner("Loading tasks…");
  try {
    const response = await fetch(`${API_BASE}/tasks`);
    if (!response.ok) {
      throw new Error(`Server responded with ${response.status}`);
    }
    tasks = await response.json();
    renderBoard(tasks);
    setBanner(tasks.length === 0 ? "No tasks yet." : "");
  } catch (error) {
    renderBoard([]);
    setBanner(`Could not load tasks: ${error.message}`);
  }
}

document.addEventListener("DOMContentLoaded", fetchTasks);
