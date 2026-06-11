const toggleButton = document.getElementById("theme-toggle");
const rootElement = document.documentElement;

function applyTheme(theme) {
  if (theme === "dark") {
    document.body.classList.add("dark-mode");
    toggleButton.textContent = "Light Mode";
  } else {
    document.body.classList.remove("dark-mode");
    toggleButton.textContent = "Dark Mode";
  }
  localStorage.setItem("plannerTheme", theme);
}

function loadTheme() {
  const saved = localStorage.getItem("plannerTheme") || "light";
  applyTheme(saved);
}

function renderCalendar(events) {
  const container = document.getElementById("calendar-container");
  if (!container) return;
  container.innerHTML = "";

  if (!events.length) {
    container.innerHTML = '<p class="calendar-message">No deadline events yet. Add tasks with due dates to see them here.</p>';
    return;
  }

  const grouped = events.reduce((acc, event) => {
    acc[event.due_date] = acc[event.due_date] || [];
    acc[event.due_date].push(event);
    return acc;
  }, {});

  Object.keys(grouped)
    .sort()
    .forEach((date) => {
      const dateCard = document.createElement("div");
      dateCard.className = "calendar-date-card";
      dateCard.innerHTML = `<strong>${date}</strong>`;

      grouped[date].forEach((item) => {
        const badge = document.createElement("div");
        badge.className = "calendar-event";
        badge.innerHTML = `<span class="calendar-event-title">${item.title}</span><span>${item.priority} • ${item.status}</span>`;
        dateCard.appendChild(badge);
      });

      container.appendChild(dateCard);
    });
}

async function fetchCalendarEvents() {
  try {
    const response = await fetch("/calendar-events");
    if (!response.ok) {
      throw new Error("Unable to load calendar events.");
    }
    const events = await response.json();
    renderCalendar(events);
  } catch (error) {
    const container = document.getElementById("calendar-container");
    if (container) {
      container.innerHTML = `<p class="calendar-message">${error.message}</p>`;
    }
  }
}

if (toggleButton) {
  toggleButton.addEventListener("click", () => {
    const nextTheme = document.body.classList.contains("dark-mode") ? "light" : "dark";
    applyTheme(nextTheme);
  });
}

loadTheme();
fetchCalendarEvents();
