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

  // Register form
  document.getElementById("registerFormST").addEventListener("submit", e => {
    e.preventDefault();

    const username = document.getElementById("username").value.trim();
    const password = document.getElementById("password").value.trim();
    const selectedTags = Array.from(select.selectedOptions).map(opt => opt.value);

    if(username && password){
      const student = { username, password, tags: selectedTags };
      localStorage.setItem("mhStudent", JSON.stringify(student));
      alert("Student registration successful! Please log in.");
      window.location.href = "loginST.html";
    } else {
      alert("Please fill in all required fields before registering.");
    }
  });
});
