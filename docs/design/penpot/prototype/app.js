const dialog = document.querySelector('[data-dialog]');
const filterPanel = document.querySelector('[data-filter-panel]');
const activeFilter = document.querySelector('[data-active-filter]');
const filterToggle = document.querySelector('[data-toggle-filters]');
const search = document.querySelector('[data-search]');
const rows = [...document.querySelectorAll('[data-search-row]')];

document.querySelector('[data-open-dialog]').addEventListener('click', () => {
  dialog.showModal();
});

filterToggle.addEventListener('click', () => {
  filterPanel.hidden = !filterPanel.hidden;
  filterToggle.setAttribute('aria-expanded', String(!filterPanel.hidden));
});

document.querySelectorAll('[data-clear-filter]').forEach((button) => {
  button.addEventListener('click', () => {
    activeFilter.hidden = true;
    document.querySelector('.count').textContent = '0';
  });
});

search.addEventListener('input', () => {
  const query = search.value.trim().toLowerCase();
  let visible = 0;
  rows.forEach((row) => {
    const match = row.dataset.searchRow.includes(query);
    row.hidden = !match;
    visible += Number(match);
  });
  document.querySelector('[data-count]').textContent = query ? visible : 200;
});
