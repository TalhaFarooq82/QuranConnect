document.addEventListener("DOMContentLoaded", function () {

    const hamburger = document.getElementById("qcHamburger");
    const drawer = document.querySelector(".qc-mobile-drawer");
    const overlay = document.querySelector(".qc-mobile-overlay");
    const closeBtn = document.getElementById("qcCloseMenu");

    if (!hamburger || !drawer || !overlay || !closeBtn) {
        return;
    }

    function openDrawer() {
        drawer.classList.add("open");
        overlay.classList.add("show");
        document.body.style.overflow = "hidden";
    }

    function closeDrawer() {
        drawer.classList.remove("open");
        overlay.classList.remove("show");
        document.body.style.overflow = "";
    }

    hamburger.addEventListener("click", openDrawer);

    closeBtn.addEventListener("click", closeDrawer);

    overlay.addEventListener("click", closeDrawer);

    document.addEventListener("keydown", function (event) {
        if (event.key === "Escape") {
            closeDrawer();
        }
    });

});