(() => {
  const icons = window.fruitIconColors || [];
  const input = document.querySelector('#icon-search');
  const rows = document.querySelector('#icon-rows');
  const resultStatus = document.querySelector('#result-status');
  const pageStatus = document.querySelector('#page-status');
  const previous = document.querySelector('#previous');
  const next = document.querySelector('#next');
  const pageSize = 80;
  let page = 0;

  function cell(text) {
    const item = document.createElement('td');
    item.textContent = text;
    return item;
  }
  function colorCell(color) {
    const item = document.createElement('td');
    const swatch = document.createElement('span');
    swatch.className = 'color-swatch';
    swatch.style.backgroundColor = color.css;
    swatch.setAttribute('aria-hidden', 'true');
    const label = document.createElement('code');
    label.textContent = color.css;
    item.append(swatch, label);
    return item;
  }
  function render() {
    const query = input.value.trim().toLowerCase();
    const filtered = icons.filter(icon => icon.id.toLowerCase().includes(query));
    const pageCount = Math.max(1, Math.ceil(filtered.length / pageSize));
    page = Math.max(0, Math.min(page, pageCount - 1));
    rows.replaceChildren();
    const fragment = document.createDocumentFragment();
    for (const icon of filtered.slice(page * pageSize, (page + 1) * pageSize)) {
      const row = document.createElement('tr');
      const id = cell(icon.id);
      id.className = 'identity';
      row.append(id, colorCell(icon.colors), colorCell(icon.colors.accent), cell(icon.colors.partContrast.toFixed(2) + ':1'));
      fragment.append(row);
    }
    rows.append(fragment);
    resultStatus.textContent = filtered.length + ' of ' + icons.length + ' icon identities';
    pageStatus.textContent = 'Page ' + (page + 1) + ' of ' + pageCount;
    previous.disabled = page === 0;
    next.disabled = page >= pageCount - 1;
  }
  input.addEventListener('input', () => { page = 0; render(); });
  previous.addEventListener('click', () => { page--; render(); });
  next.addEventListener('click', () => { page++; render(); });
  render();
})();
