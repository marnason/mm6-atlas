const pages = window.ATLAS_PAGES || [];
const regions = [...new Set(pages.map(page => page.region))].sort();
const positions = {
  'Sweet Water':[26,13],'Kriegspire':[42,20],'White Cap':[61,14],'Silver Cove':[77,25],'Eel Infested Waters':[88,42],
  'Paradise Valley':[18,31],'Blackshire':[35,38],'Free Haven':[52,39],'Bootleg Bay':[70,44],'Mist':[85,58],
  'Hermits Isle':[12,55],'Dragonsand':[28,66],'Mire Of The Damned':[46,63],'Castle Ironfist':[61,66],'New Sorpigal':[77,76]
};
const $ = selector => document.querySelector(selector);
const escapeHTML = value => value.replace(/[&<>"']/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
let query = '', activeRegion = 'All';

$('#page-count').textContent = pages.length;
$('#region-count').textContent = regions.length;

function openPage(page) {
  const images = page.images.map(src => `<img src="assets/places/${encodeURI(src)}" alt="Map or scene from ${escapeHTML(page.title)}" loading="lazy">`).join('');
  $('#detail-content').innerHTML = `<header class="detail-head"><p class="eyebrow">${escapeHTML(page.region)}</p><h2>${escapeHTML(page.title)}</h2></header><div class="detail-body">${images ? `<div class="gallery">${images}</div>` : ''}<pre>${escapeHTML(page.body)}</pre><a class="source-link" href="https://user.xmission.com/~tnelson/mm6/gameplay/places/${encodeURI(page.sourcePath)}" target="_blank" rel="noopener">View the archived source page ↗</a></div>`;
  $('#detail').showModal();
  history.replaceState(null, '', `#guide=${page.id}`);
}

function renderCards() {
  const words = query.toLowerCase().trim().split(/\s+/).filter(Boolean);
  const results = pages.filter(page => (activeRegion === 'All' || page.region === activeRegion) && words.every(word => `${page.title} ${page.region} ${page.body}`.toLowerCase().includes(word)));
  $('#result-note').textContent = `${results.length} ${results.length === 1 ? 'guide' : 'guides'} found${query ? ` for “${query}”` : ''}`;
  $('#cards').innerHTML = results.length ? results.map((page, index) => `<button class="card" data-id="${page.id}"><span class="number">${String(index + 1).padStart(2,'0')}</span><h3>${escapeHTML(page.title)}</h3><p>${escapeHTML(page.body.slice(0,140))}${page.body.length > 140 ? '…' : ''}</p><footer>${escapeHTML(page.region)} · ${page.images.length} ${page.images.length === 1 ? 'map' : 'maps'}</footer></button>`).join('') : '<p class="empty">No passages match this search. Try a region, dungeon, or treasure name.</p>';
  document.querySelectorAll('.card').forEach(card => card.addEventListener('click', () => openPage(pages.find(page => page.id === card.dataset.id))));
}

function setRegion(region, scroll = false) {
  activeRegion = region;
  document.querySelectorAll('#filters button').forEach(button => button.classList.toggle('active', button.dataset.region === region));
  document.querySelectorAll('.pin').forEach(pin => pin.classList.toggle('active', pin.dataset.region === region));
  const regionPages = pages.filter(page => page.region === region);
  if (region !== 'All') $('#map-panel').innerHTML = `<p class="eyebrow">Selected region</p><h3>${escapeHTML(region)}</h3><p>${regionPages.length} recovered guides and locations.</p><div class="map-links">${regionPages.slice(0,7).map(page => `<button data-id="${page.id}">${escapeHTML(page.title)}</button>`).join('')}</div>`;
  document.querySelectorAll('.map-links button').forEach(button => button.addEventListener('click', () => openPage(pages.find(page => page.id === button.dataset.id))));
  renderCards();
  if (scroll) $('#archive').scrollIntoView({behavior:'smooth'});
}

$('#filters').innerHTML = ['All', ...regions].map(region => `<button data-region="${region}" class="${region === 'All' ? 'active' : ''}">${region}</button>`).join('');
document.querySelectorAll('#filters button').forEach(button => button.addEventListener('click', () => setRegion(button.dataset.region)));
$('#map-pins').innerHTML = regions.map(region => { const [x,y] = positions[region] || [50,50]; return `<button class="pin" data-region="${region}" aria-label="Explore ${region}" style="left:${x}%;top:${y}%"><span>${region}</span></button>`; }).join('');
document.querySelectorAll('.pin').forEach(pin => pin.addEventListener('click', () => setRegion(pin.dataset.region, true)));

function setQuery(value) { query = value; $('#global-search').value = value; $('#archive-search').value = value; renderCards(); if (value) $('#archive').scrollIntoView({behavior:'smooth'}); }
$('#global-search').addEventListener('input', event => setQuery(event.target.value));
$('#archive-search').addEventListener('input', event => { query = event.target.value; $('#global-search').value = query; renderCards(); });
document.addEventListener('keydown', event => { if (event.key === '/' && !/input|textarea/i.test(document.activeElement.tagName)) { event.preventDefault(); $('#global-search').focus(); } if (event.key === 'Escape' && $('#detail').open) $('#detail').close(); });
$('.close').addEventListener('click', () => $('#detail').close());
$('#detail').addEventListener('click', event => { if (event.target === $('#detail')) $('#detail').close(); });
$('#detail').addEventListener('close', () => history.replaceState(null, '', '#archive'));
renderCards();
const linked = location.hash.match(/^#guide=(.+)$/)?.[1];
if (linked) { const page = pages.find(item => item.id === linked); if (page) openPage(page); }
if ('serviceWorker' in navigator && location.protocol.startsWith('http')) navigator.serviceWorker.register('sw.js');
