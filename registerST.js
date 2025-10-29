document.addEventListener("DOMContentLoaded", () => {
  const select = document.getElementById("characteristics");
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

  // Clear selections
  clearBtn.addEventListener("click", () => {
    Array.from(select.options).forEach(o => o.selected = false);
  });

  // Register form submission
  document.getElementById("registerFormST").addEventListener("submit", async e => {
    e.preventDefault();

    const username = document.getElementById("username").value.trim();
    const password = document.getElementById("password").value.trim();
    const selectedTags = Array.from(select.selectedOptions).map(opt => opt.value);

    if (username && password) {
      const student = { username, password, tags: selectedTags };

      try {
        const response = await fetch("http://127.0.0.1:5000/register", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(student)
        });

        const data = await response.json();

        if (response.ok) {
          alert(data.message);
          window.location.href = "loginST.html";
        } else {
          alert("❌ Error: " + data.message);
        }
      } catch (error) {
        console.error("Error:", error);
        alert("⚠️ Could not connect to the server.");
      }
    } else {
      alert("Please fill in all required fields before registering.");
    }
  });
});
