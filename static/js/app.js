// Shared frontend behavior. Bootstrap handles navigation and dismissible alerts.
// Add page-specific fetch/AJAX behavior here as the project grows.
document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll("[data-confirm]").forEach((el) => {
    el.addEventListener("click", (event) => {
      if (!confirm(el.dataset.confirm || "Are you sure?")) event.preventDefault();
    });
  });
});
