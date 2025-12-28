(function () {
  const menuBtn = document.getElementById('menuBtn');
  const sideMenu = document.getElementById('sideMenu');
  const closeMenu = document.getElementById('closeMenu');
  const chatBtn = document.getElementById('chatBtn');
  const userBtn = document.getElementById('userBtn');
  const userPopup = document.getElementById('userPopup');

  // === OPEN SIDEBAR ===
  menuBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    sideMenu.classList.add('open');
    sideMenu.setAttribute('aria-hidden', 'false');
  });

  // === CLOSE SIDEBAR WITH X BUTTON ===
  closeMenu.addEventListener('click', (e) => {
    e.stopPropagation();
    sideMenu.classList.remove('open');
    sideMenu.setAttribute('aria-hidden', 'true');
  });

  // === CLOSE SIDEBAR WHEN CLICKING OUTSIDE ===
  document.addEventListener('click', (e) => {
    if (!sideMenu.contains(e.target) && e.target !== menuBtn) {
      sideMenu.classList.remove('open');
      sideMenu.setAttribute('aria-hidden', 'true');
    }
  });

  // === CHAT BUTTON PLACEHOLDER ===
  chatBtn.addEventListener('click', () => {
    alert('Chat feature coming soon!');
  });

  // === USER POPUP TOGGLE ===
  userBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    userPopup.classList.toggle('active');
  });

  // === CLOSE USER POPUP ON OUTSIDE CLICK ===
  document.addEventListener('click', (e) => {
    if (!userPopup.contains(e.target) && e.target !== userBtn) {
      userPopup.classList.remove('active');
    }
  });

  // === LOAD USER INFO FROM LOCAL STORAGE ===
  document.addEventListener('DOMContentLoaded', () => {
    const username = localStorage.getItem('username') || 'Guest';
    const specialty = localStorage.getItem('specialty');

    document.getElementById('username').textContent = `Username: ${username}`;
    document.getElementById('userTags').textContent = specialty ? `Specialty: ${specialty}` : 'Specialty: Not set';
  });
})();
