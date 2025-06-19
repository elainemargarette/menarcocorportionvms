// static/script.js
document.addEventListener('DOMContentLoaded', () => {
    const sidebar = document.getElementById('sidebar');
    const toggleBtn = document.getElementById('menu-toggle');

    if (toggleBtn && sidebar) {
        toggleBtn.addEventListener('click', () => {
            sidebar.classList.toggle('open');
        });
    }

    // Optional: Form validation
    const form = document.querySelector('form');
    if (form) {
        form.addEventListener('submit', (e) => {
            const name = form.querySelector('input[name="name"]')?.value;
            const purpose = form.querySelector('input[name="purpose"]')?.value;
            const contact = form.querySelector('input[name="contact"]')?.value;

            if (!name || !purpose || !contact) {
                e.preventDefault();
                alert("Please fill in all fields!");
            }
        });
    }
});
