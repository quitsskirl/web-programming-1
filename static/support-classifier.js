// support-classifier.js
document.addEventListener("DOMContentLoaded", () => {
  // --- DOM refs ---
  const messageEl    = document.getElementById("message");
  const classifyBtn  = document.getElementById("classifyBtn");
  const exampleBtn   = document.getElementById("exampleBtn");
  const resetBtn     = document.getElementById("resetBtn");
  const resultCard   = document.getElementById("result");
  const deptPill     = document.getElementById("deptPill");
  const scoreFill    = document.getElementById("scoreFill");
  const scoreIDC     = document.getElementById("scoreIDC");
  const scoreOpen    = document.getElementById("scoreOpen");
  const scoreCounsel = document.getElementById("scoreCounsel");
  const crisisBox    = document.getElementById("crisisBox");
  const reasonsUl    = document.getElementById("reasons");

  // Get JWT token from localStorage
  function getToken() {
    return localStorage.getItem("token");
  }

  // Check if user is logged in as student
  function checkAccess() {
    const token = getToken();
    const role = localStorage.getItem("role");
    
    if (!token) {
      alert("Please log in as a student to use the classifier.");
      window.location.href = "/login-student";
      return false;
    }
    
    if (role !== "student") {
      alert("Access denied. Only students can use the classifier.");
      return false;
    }
    
    return true;
  }

  function render(data) {
    resultCard.classList.remove("hidden");

    deptPill.textContent = data.department;
    deptPill.className = "dept-pill pill-" + data.department.toLowerCase();

    scoreFill.style.width = (data.confidence * 100) + "%";

    scoreIDC.style.width     = data.department === "IDC" ? (data.confidence * 100) + "%" : "0%";
    scoreOpen.style.width    = data.department === "OPEN" ? (data.confidence * 100) + "%" : "0%";
    scoreCounsel.style.width = data.department === "COUNSEL" ? (data.confidence * 100) + "%" : "0%";

    crisisBox.classList.toggle("hidden", !data.crisis);

    reasonsUl.innerHTML = "";
    (data.reasons || []).forEach(r => {
      const li = document.createElement("li");
      li.textContent = r;
      reasonsUl.appendChild(li);
    });
  }

  classifyBtn.onclick = async () => {
    // Check access before making request
    if (!checkAccess()) return;

    const msg = messageEl.value.trim();
    if (!msg) return;

    const token = getToken();

    try {
      const r = await fetch("/api/classify", {
        method: "POST",
        headers: { 
          "Content-Type": "application/json",
          "Authorization": "Bearer " + token  // Send JWT token
        },
        body: JSON.stringify({ message: msg })
      });

      console.log("Response status:", r.status);

      if (r.status === 401) {
        alert("Session expired. Please log in again.");
        localStorage.removeItem("token");
        localStorage.removeItem("role");
        window.location.href = "/login-student";
        return;
      }

      if (r.status === 403) {
        alert("Access denied. Only students can use the classifier.");
        return;
      }

      if (!r.ok) {
        const err = await r.json().catch(() => ({}));
        console.error("API error:", err);
        alert("Classification failed. See console for details.");
        return;
      }

      const json = await r.json();
      console.log("API JSON:", json);
      render(json);
    } catch (e) {
      console.error("Fetch failed:", e);
      alert("Could not reach the classifier API.");
    }
  };

  exampleBtn.onclick = () => {
    messageEl.value = "I feel so alone recently, I can't focus in class and I think I'm failing";
  };

  resetBtn.onclick = () => {
    messageEl.value = "";
    resultCard.classList.add("hidden");
  };

  console.log("✅ support-classifier.js loaded and handlers attached");
});
    