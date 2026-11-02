document.querySelectorAll(".mobile-menu nav a").forEach(link => {
  link.addEventListener("click", () => {
    const menu = link.closest("details");
    if (menu) menu.open = false;
  });
});
