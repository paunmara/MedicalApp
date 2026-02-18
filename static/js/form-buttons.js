document.addEventListener("DOMContentLoaded", () => {
    const buttons = document.querySelectorAll(".choice-btn");

    buttons.forEach(btn => {
        btn.addEventListener("click", () => {
            const inputName = btn.dataset.input;
            const value = btn.dataset.value;

            const hiddenInput = document.querySelector(
                `input[name="${inputName}"]`
            );

            if (!hiddenInput) {
                console.error("Hidden input not found:", inputName);
                return;
            }

            hiddenInput.value = value;

            // deactivate siblings
            btn.parentElement
               .querySelectorAll(".choice-btn")
               .forEach(b => b.classList.remove("active-choice"));

            btn.classList.add("active-choice");
        });
    });
});
