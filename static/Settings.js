document.addEventListener('DOMContentLoaded', () => {
  // Load user info from localStorage
  const username = localStorage.getItem('username') || 'Guest';
  const tags = localStorage.getItem('tags') || 'No tags set';
  
  document.getElementById('profileUsername').textContent = username;
  document.getElementById('profileTags').textContent = tags;

  const menuBtn = document.getElementById('menuBtn');
  const sideMenu = document.getElementById('sideMenu');
  const closeMenu = document.getElementById('closeMenu');
  const chatBtn = document.getElementById('chatBtn');

  // === Sidebar toggle ===
  menuBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    sideMenu.classList.add('open');
    sideMenu.setAttribute('aria-hidden', 'false');
  });

  closeMenu.addEventListener('click', (e) => {
    e.stopPropagation();
    sideMenu.classList.remove('open');
    sideMenu.setAttribute('aria-hidden', 'true');
  });

  document.addEventListener('click', (e) => {
    if (!sideMenu.contains(e.target) && e.target !== menuBtn) {
      sideMenu.classList.remove('open');
      sideMenu.setAttribute('aria-hidden', 'true');
    }
  });

  // === Chat button ===
  chatBtn.addEventListener('click', () => {
    alert('Chat feature coming soon!');
  });

  // === Show/hide forms ===
  const btnChangePass = document.getElementById('btnChangePass');
  const formChangePass = document.getElementById('formChangePass');
  const btnNotifications = document.getElementById('btnNotifications');
  const formNotifications = document.getElementById('formNotifications');
  const btnBlocked = document.getElementById('btnBlocked');
  const formBlocked = document.getElementById('formBlocked');

  const forms = [formChangePass, formNotifications, formBlocked];

  function hideAllForms() {
    forms.forEach(f => f.style.display = 'none');
  }

  btnChangePass.addEventListener('click', () => {
    hideAllForms();
    formChangePass.style.display = 'block';
  });

  btnNotifications.addEventListener('click', () => {
    hideAllForms();
    formNotifications.style.display = 'block';
  });

  btnBlocked.addEventListener('click', () => {
    hideAllForms();
    formBlocked.style.display = 'block';
  });

  // === Logout button ===
  document.getElementById('btnLogOut').addEventListener('click', () => {
    // You can clear localStorage here if you want to fully log out:
    // localStorage.clear();
    // Redirect to the Flask first page ("/" -> first.first_page)
    window.location.href = '/';
  });

  // === Delete account button ===
  document.getElementById('btnDeleteAccount').addEventListener('click', () => {
    const confirmDelete = confirm(
      'Are you sure you want to delete your account? This cannot be undone.'
    );
    if (confirmDelete) {
      alert('Account will be deleted (placeholder).');
      // Add real deletion logic here if you implement backend support.
    }
  });
});
