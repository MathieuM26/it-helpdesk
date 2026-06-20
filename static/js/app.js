// Auto-dismiss alerts after 4 seconds
document.querySelectorAll('.alert').forEach(el => {
  setTimeout(() => { el.style.transition = 'opacity .4s'; el.style.opacity = '0'; setTimeout(() => el.remove(), 400); }, 4000);
});

// Dashboard live filtering
const search   = document.getElementById('search');
const fStatus  = document.getElementById('filter-status');
const fPri     = document.getElementById('filter-priority');
const fCat     = document.getElementById('filter-category');

function applyFilters() {
  const q   = (search?.value || '').toLowerCase();
  const st  = fStatus?.value  || '';
  const pri = fPri?.value     || '';
  const cat = fCat?.value     || '';

  document.querySelectorAll('.ticket-row').forEach(row => {
    const text     = row.textContent.toLowerCase();
    const status   = row.dataset.status   || '';
    const priority = row.dataset.priority || '';
    const category = row.dataset.category || '';

    const match = (!q   || text.includes(q))
               && (!st  || status === st)
               && (!pri || priority === pri)
               && (!cat || category === cat);

    row.style.display = match ? '' : 'none';
  });
}

[search, fStatus, fPri, fCat].forEach(el => el?.addEventListener('input', applyFilters));
