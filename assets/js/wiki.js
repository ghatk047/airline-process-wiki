// Sidebar accordion
document.addEventListener('DOMContentLoaded', () => {
  // Toggle domain sections
  document.querySelectorAll('.sidebar-domain').forEach(el => {
    el.addEventListener('click', () => {
      el.classList.toggle('open');
      const l2 = el.nextElementSibling;
      if (l2) l2.classList.toggle('open');
    });
  });

  // Auto-open the section containing the active link
  const active = document.querySelector('.sidebar-l3-link.active');
  if (active) {
    let parent = active.closest('.sidebar-l2');
    if (parent) {
      parent.classList.add('open');
      const domain = parent.previousElementSibling;
      if (domain) domain.classList.add('open');
    }
  }

  // Smooth scroll for anchor links
  document.querySelectorAll('a[href^="#"]').forEach(a => {
    a.addEventListener('click', e => {
      const target = document.querySelector(a.getAttribute('href'));
      if (target) {
        e.preventDefault();
        target.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    });
  });
});
