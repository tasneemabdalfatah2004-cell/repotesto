
function togglePassword() {
    const password = document.getElementById('password');
    if (password.type === "password") {
        password.type = "text";
    } else {
        password.type = "password";
    }
}
document.addEventListener("DOMContentLoaded", function () {
    const tabs = document.querySelectorAll(".works-tabs .tab");
    const cards = Array.from(document.querySelectorAll(".portfolio-card"));

    // عدد الأعمال الحديثة اللي نعرضها
    const LATEST_COUNT = 12;

    function showLatest() {
        cards.forEach((card, index) => {
            if (index < LATEST_COUNT) {
                card.classList.remove("hidden");
            } else {
                card.classList.add("hidden");
            }
        });
    }

    function showAll() {
        cards.forEach(card => card.classList.remove("hidden"));
    }

    tabs.forEach(tab => {
        tab.addEventListener("click", () => {
            // تحديث التاب النشط
            tabs.forEach(t => t.classList.remove("active"));
            tab.classList.add("active");

            if (tab.dataset.filter === "latest") {
                showLatest();
            } else if (tab.dataset.filter === "all") {
                showAll();
            }
        });
    });

    // افتراضيًا: عرض أحدث الأعمال
    showLatest();
});
