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
  card.draggable = true;
  card.addEventListener("dragstart", (event) => {
    event.dataTransfer.setData("text/plain", String(task.id));
    event.dataTransfer.effectAllowed = "move";
    card.classList.add("dragging");
  });
  card.addEventListener("dragend", () => card.classList.remove("dragging"));

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
  editButton.addEventListener("click", () => openModal(task));
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

// ---------------------------------------------------------------- drag & drop

// Columns are the drop targets. Registered once; cards are re-created on
// every render, so their listeners live in createCard().
function enableDragAndDrop() {
  for (const column of document.querySelectorAll(".column")) {
    column.addEventListener("dragover", (event) => {
      event.preventDefault(); // required to allow dropping
      event.dataTransfer.dropEffect = "move";
      column.classList.add("drop-target");
    });
    column.addEventListener("dragleave", (event) => {
      if (!column.contains(event.relatedTarget)) {
        column.classList.remove("drop-target");
      }
    });
    column.addEventListener("drop", (event) => {
      event.preventDefault();
      column.classList.remove("drop-target");
      const id = Number(event.dataTransfer.getData("text/plain"));
      moveTask(id, column.dataset.status);
    });
  }
}

// Optimistic status change: move locally, PATCH, revert on any failure.
async function moveTask(id, targetStatus) {
  const task = tasks.find((t) => t.id === id);
  if (!task || task.status === targetStatus) return; // same column: no request

  const previousStatus = task.status;
  task.status = targetStatus;
  renderBoard(tasks);

  try {
    const response = await fetch(`${API_BASE}/tasks/${id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status: targetStatus }),
    });

    if (response.ok) {
      const updated = await response.json();
      tasks = tasks.map((t) => (t.id === id ? updated : t));
      renderBoard(tasks);
      setState("ready");
      return;
    }

    task.status = previousStatus;
    renderBoard(tasks);
    setState("error", `Move failed: ${await readErrorDetail(response)}`);
  } catch (_networkError) {
    task.status = previousStatus;
    renderBoard(tasks);
    setState("error", "Move failed: could not reach the server. Check that the backend is running.");
  }
}

// Pulls a readable message out of a FastAPI error body.
// `detail` is a string for our own HTTPExceptions and a list for Pydantic 422s.
async function readErrorDetail(response) {
  const fallback = `server responded with ${response.status}`;
  try {
    const body = await response.json();
    if (typeof body.detail === "string") return body.detail;
    if (Array.isArray(body.detail)) {
      return body.detail
        .map((e) => (e.loc?.length ? `${e.loc[e.loc.length - 1]}: ${e.msg}` : e.msg))
        .join("; ");
    }
  } catch (_notJson) {
    // fall through
  }
  return fallback;
}

// ---------------------------------------------------------------- modal

const dialog = document.getElementById("task-dialog");
const form = document.getElementById("task-form");
const formError = document.getElementById("form-error");
const saveButton = document.getElementById("save-button");

// The task being edited, or null in create mode. Used to PATCH only what changed.
let editingTask = null;

function showFormError(message) {
  formError.textContent = message;
  formError.hidden = !message;
}

// Opens the modal. With a task, the form is pre-filled for editing;
// without one, it is reset for creating.
function openModal(task = null) {
  editingTask = task;
  form.reset();
  showFormError("");
  dialog.classList.toggle("editing", task !== null);
  document.getElementById("task-form-title").textContent = task ? "Edit task" : "New task";

  if (task) {
    form.elements.id.value = String(task.id);
    form.elements.title.value = task.title;
    form.elements.description.value = task.description;
    form.elements.assignee.value = task.assignee ?? "";
    form.elements.priority.value = task.priority;
    form.elements.status.value = task.status;
  }

  dialog.showModal();
  form.elements.title.focus();
}

function closeModal() {
  dialog.close();
}

// Reads the form into an API payload. Empty description -> "", empty assignee -> null.
function readForm() {
  const fields = form.elements;
  return {
    title: fields.title.value.trim(),
    description: fields.description.value.trim(),
    assignee: fields.assignee.value.trim() || null,
    priority: fields.priority.value,
    status: fields.status.value,
  };
}

async function submitForm(event) {
  event.preventDefault();
  const values = readForm();

  if (values.title === "") {
    showFormError("Title is required");
    form.elements.title.focus();
    return; // no request
  }

  let method;
  let url;
  let payload;
  if (editingTask === null) {
    method = "POST";
    url = `${API_BASE}/tasks`;
    const { status: _ignored, ...createFields } = values; // new tasks start as ToDo
    payload = createFields;
  } else {
    method = "PATCH";
    url = `${API_BASE}/tasks/${editingTask.id}`;
    // Send only changed fields so an untouched status never triggers a same->same 422.
    payload = Object.fromEntries(
      Object.entries(values).filter(([key, value]) => value !== editingTask[key])
    );
    if (Object.keys(payload).length === 0) {
      closeModal();
      return;
    }
  }

  saveButton.disabled = true;
  try {
    const response = await fetch(url, {
      method,
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!response.ok) {
      showFormError(await readErrorDetail(response)); // modal stays open
      return;
    }
    closeModal();
    fetchTasks();
  } catch (_networkError) {
    showFormError("Could not reach the server. Check that the backend is running.");
  } finally {
    saveButton.disabled = false;
  }
}

function enableModal() {
  document.getElementById("new-task-button").addEventListener("click", () => openModal());
  document.getElementById("cancel-button").addEventListener("click", closeModal);
  document.getElementById("close-button").addEventListener("click", closeModal);
  // Click on the backdrop (outside the form) closes; clicks inside don't bubble to the dialog itself.
  dialog.addEventListener("click", (event) => {
    if (event.target === dialog) closeModal();
  });
  // Fires for every close path, including Escape (native <dialog> behavior).
  dialog.addEventListener("close", () => {
    editingTask = null;
    form.reset();
    showFormError("");
  });
  form.addEventListener("submit", submitForm);
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

document.addEventListener("DOMContentLoaded", () => {
  enableDragAndDrop();
  enableModal();
  fetchTasks();
});
