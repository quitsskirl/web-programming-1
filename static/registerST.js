document.addEventListener("DOMContentLoaded", () => {
  const form     = document.getElementById("registerFormST");   // <— grab the form
  const select   = document.getElementById("characteristics");
  const clearBtn = document.getElementById("clearSelections");

  // Add dropdown options dynamically
  const traits = [
    "Curious","Hardworking","Creative","Team Player","Organized","Analytical",
    "Leader","Friendly","Empathetic","Innovative","Calm","Motivated",
    "Adaptable","Problem Solver","Collaborative","Independent","Ambitious",
    "Reliable","Observant","Positive"
  ];

  traits.forEach(trait => {
    const opt = document.createElement("option");
    opt.value = trait;
    opt.textContent = trait;
    select.appendChild(opt);
  });

  // CLEAR button — reset everything + ensure multi-select is cleared
  clearBtn.addEventListener("click", () => {
    form.reset(); // clears inputs/placeholders/checkboxes/single selects
    Array.from(select.options).forEach(o => (o.selected = false)); // clear multi-select explicitly
  });

  // NOTE: The form submit handler is in registerST.html template
  // It calls the /register API and redirects using Flask url_for
  // This JS file only handles dynamic options and clear button
});
