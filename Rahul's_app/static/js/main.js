document.addEventListener("DOMContentLoaded", () => {
    // Sidebar toggle
    const sidebar = document.getElementById('sidebar');
    const hamburger = document.querySelector('#sidebar .hamburger');
    if (hamburger && sidebar) {
        hamburger.addEventListener('click', () => sidebar.classList.toggle('collapsed'));
    }

    // Comment section toggle
    document.querySelectorAll(".comment-toggle").forEach(btn => {
        btn.addEventListener("click", () => {
            const postId = btn.dataset.postId;
            const section = document.getElementById(`comments-${postId}`);
            if (section.style.display === "none" || section.style.display === "") {
                section.style.display = "block";
                section.scrollIntoView({ behavior: "smooth", block: "center" });
            } else {
                section.style.display = "none";
            }
        });
    });

    // Logout modal
    const logoutBtn = document.getElementById('logoutBtn');
    const logoutModal = document.getElementById('logoutModal');
    const confirmBtn = document.getElementById('confirmLogout');
    const cancelBtn = document.getElementById('cancelLogout');

    if (logoutBtn && logoutModal) {
        logoutBtn.addEventListener('click', e => {
            e.preventDefault();
            logoutModal.style.display = 'flex';
        });

        confirmBtn.addEventListener('click', () => {
            window.location.href = logoutBtn.href;
        });

        cancelBtn.addEventListener('click', () => {
            logoutModal.style.display = 'none';
        });

        window.addEventListener('click', event => {
            if (event.target === logoutModal) logoutModal.style.display = 'none';
        });
    }
});
