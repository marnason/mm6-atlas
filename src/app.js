const pages = window.ATLAS_PAGES || [];
const regions = [...new Set(pages.map(page => page.region))].sort();
const mapRegions = [
  'Sweet Water','Kriegspire','White Cap','Silver Cove','Eel Infested Waters',
  'Paradise Valley','Blackshire','Free Haven','Bootleg Bay','Mist',
  'Hermits Isle','Dragonsand','Mire Of The Damned','Castle Ironfist','New Sorpigal'
];
const $ = selector => document.querySelector(selector);
const esc = value => String(value).replace(/[&<>"']/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
const slug = region => region.toLowerCase().replace(/[^a-z0-9]+/g, '-');
const regionURL = region => '#/region/' + slug(region);
const guideURL = page => '#/guide/' + encodeURIComponent(page.id);
const regionBySlug = new Map(regions.map(region => [slug(region), region]));
const pageById = new Map(pages.map(page => [page.id, page]));
let route = {name:'map'}, searchTerm = '', searchLimit = 18;

function parseRoute() {
  const hash = location.hash.replace(/^#\/?/, '');
  const [path, search = ''] = hash.split('?');
  const [rawName, value] = path.split('/');
  const name = rawName || 'map';
  if (name === 'region' && regionBySlug.has(value)) return {name, region:regionBySlug.get(value)};
  if (name === 'guide' && pageById.has(decodeURIComponent(value || ''))) return {name, page:pageById.get(decodeURIComponent(value))};
  if (name === 'search') return {name, query:new URLSearchParams(search).get('q') || ''};
  if (['map','regions','about'].includes(name)) return {name};
  return {name:'not-found'};
}

function go(href, replace = false) {
  if (location.hash === href) return render();
  history[replace ? 'replaceState' : 'pushState']({atlas:true}, '', href);
  render(true);
}

const crumb = (label, href) => href ? '<a href="' + href + '" data-link>' + esc(label) + '</a>' : '<span aria-current="page">' + esc(label) + '</span>';
function renderNavigation() {
  const parts = [crumb('World map', route.name === 'map' ? null : '#/map')];
  if (route.name === 'regions') parts.push(crumb('Regions'));
  if (route.name === 'region') parts.push(crumb(route.region));
  if (route.name === 'guide') parts.push(crumb(route.page.region, regionURL(route.page.region)), crumb(route.page.title));
  if (route.name === 'search') parts.push(crumb('Search'));
  if (route.name === 'about') parts.push(crumb('About'));
  if (route.name === 'not-found') parts.push(crumb('Not found'));
  $('#breadcrumbs').innerHTML = parts.join('<span class="crumb-separator" aria-hidden="true">/</span>');
  $('#back-button').hidden = !history.state?.atlas;
  document.querySelectorAll('.primary-nav a').forEach(link => {
    const current = link.dataset.route === route.name || (route.name === 'region' && link.dataset.route === 'regions');
    link.classList.toggle('active', current);
    if (current) link.setAttribute('aria-current', 'page'); else link.removeAttribute('aria-current');
  });
}

function regionItem(region) {
  const count = pages.filter(page => page.region === region).length;
  return '<a class="region-item" href="' + regionURL(region) + '" data-link><span class="region-mark">✦</span><span>' + esc(region) + '</span><small>' + count + ' guides</small><span aria-hidden="true">↗</span></a>';
}
function heading(eyebrow, title, subhead = '', action = '') {
  return '<div class="view-heading"><div><p class="eyebrow">' + esc(eyebrow) + '</p><h1>' + esc(title) + '</h1>' + (subhead ? '<p class="subhead">' + esc(subhead) + '</p>' : '') + '</div>' + action + '</div>';
}
function renderMap() {
  const zones = mapRegions.map(region => '<a class="map-zone" href="' + regionURL(region) + '" data-link aria-label="Explore ' + esc(region) + '"><span>' + esc(region) + '</span></a>').join('');
  return heading('Might and Magic VI · Field companion','Explore Enroth','Select any square to open its region. ' + pages.length + ' recovered guides are available offline.','<a class="text-link" href="#/regions" data-link>Browse all regions →</a>') + '<div class="map-layout"><div class="map-canvas"><div class="map-surface"><img src="assets/places/World/big.jpg" alt="Map of the world of Enroth" draggable="false"><div class="map-zones" aria-label="Map regions">' + zones + '</div></div></div><aside class="map-aside"><p class="eyebrow">Atlas index</p><h2>Where to?</h2><p>Each square opens its matching region and guide list.</p><div class="featured-regions">' + ['New Sorpigal','Castle Ironfist','Free Haven','Mist'].map(regionItem).join('') + '</div><a class="aside-link" href="#/regions" data-link>All ' + regions.length + ' regions →</a></aside></div>';
}
function renderRegions() { return heading('Explore by place','Regions of Enroth',regions.length + ' regions. Choose one to see its recovered guides.') + '<div class="region-grid">' + regions.map(regionItem).join('') + '</div>'; }
function guideRow(page, index) {
  const excerpt = page.body.replace(/\s+/g,' ').slice(0,130);
  return '<a class="guide-row" href="' + guideURL(page) + '" data-link><span class="guide-number">' + String(index + 1).padStart(2,'0') + '</span><span class="guide-summary"><strong>' + esc(page.title) + '</strong><small>' + esc(excerpt) + (page.body.length > 130 ? '…' : '') + '</small></span><span class="guide-meta">' + page.images.length + ' ' + (page.images.length === 1 ? 'image' : 'images') + '</span><span class="guide-arrow" aria-hidden="true">→</span></a>';
}
function renderRegion(region) {
  const items = pages.filter(page => page.region === region);
  return heading('Region · ' + items.length + ' guides',region,'Maps, locations, and field notes from the Magic Grounds archive.','<a class="text-link" href="#/regions" data-link>All regions →</a>') + '<div class="guide-list">' + items.map(guideRow).join('') + '</div>';
}
function renderGuide(page) {
  const images = page.images.map(src => '<figure><img src="assets/places/' + encodeURI(src) + '" alt="Map or scene for ' + esc(page.title) + '" loading="lazy"><figcaption>' + esc(src.split('/').pop()) + '</figcaption></figure>').join('');
  const siblings = pages.filter(item => item.region === page.region), index = siblings.findIndex(item => item.id === page.id), previous = siblings[index - 1], next = siblings[index + 1];
  const pager = (item, label) => item ? '<a href="' + guideURL(item) + '" data-link><small>' + label + '</small><strong>' + esc(item.title) + '</strong></a>' : '<span></span>';
  return '<article class="guide-view">' + heading(page.region + ' · Guide ' + (index + 1) + ' of ' + siblings.length,page.title,'','<a class="text-link" href="' + regionURL(page.region) + '" data-link>All ' + esc(page.region) + ' guides →</a>') + '<div class="guide-content">' + (images ? '<div class="image-gallery">' + images + '</div>' : '') + '<section class="guide-notes"><h2>Field notes</h2><p>' + esc(page.body).replace(/\n/g,'<br>') + '</p></section></div><div class="guide-source">Original: <a href="https://user.xmission.com/~tnelson/mm6/gameplay/places/' + encodeURI(page.sourcePath) + '" target="_blank" rel="noopener">Magic Grounds ↗</a></div><nav class="guide-pager" aria-label="Guide navigation">' + pager(previous,'← Previous guide') + pager(next,'Next guide →') + '</nav></article>';
}
function searchResults() {
  const words = searchTerm.toLowerCase().trim().split(/\s+/).filter(Boolean);
  const matches = words.length ? pages.filter(page => words.every(word => (page.title + ' ' + page.region + ' ' + page.body).toLowerCase().includes(word))) : [];
  $('#search-results').innerHTML = words.length ? '<p class="result-count">' + matches.length + ' ' + (matches.length === 1 ? 'guide' : 'guides') + ' found</p><div class="guide-list">' + (matches.slice(0,searchLimit).map(guideRow).join('') || '<p class="empty">No matches. Try a place, dungeon, or treasure name.</p>') + '</div>' + (matches.length > searchLimit ? '<button class="more-button" id="more-results" type="button">Show more results (' + (matches.length - searchLimit) + ' remaining)</button>' : '') : '<div class="search-prompt"><span>⌕</span><h2>Find a place or secret</h2><p>Search the titles and notes of all ' + pages.length + ' recovered guides.</p></div>';
}
function renderSearch() { return heading('Full archive search','Search the atlas','Find locations, dungeon notes, towns, and treasures across every region.') + '<div id="search-results"></div>'; }
function renderAbout() { return heading('Preservation note','About this atlas') + '<div class="about-copy"><p>Enroth Atlas reorganizes the recovered Magic Grounds maps and notes into a compact field guide. All guide content and images are bundled for offline use once the site has been visited.</p><p>The archive contains ' + pages.length + ' searchable guides across ' + regions.length + ' regions. See the <a href="LICENSE.md">source credits and license</a> or <a href="https://github.com/marnason/mm6-atlas">project repository</a>.</p><p>This is an unofficial fan project and is not affiliated with Ubisoft or New World Computing.</p></div>'; }
function render(moveFocus = false) {
  route = parseRoute(); renderNavigation();
  $('#search-input').value = route.name === 'search' ? route.query : '';
  if (route.name === 'search') searchTerm = route.query;
  const views = {map:renderMap,regions:renderRegions,region:()=>renderRegion(route.region),guide:()=>renderGuide(route.page),search:renderSearch,about:renderAbout};
  $('#view').innerHTML = views[route.name]?.() || heading('Lost passage','Page not found') + '<a class="text-link" href="#/map" data-link>Return to the map →</a>';
  if (route.name === 'search') searchResults();
  const label = route.name === 'guide' ? route.page.title : route.name === 'region' ? route.region : route.name === 'map' ? 'World Map' : route.name[0].toUpperCase() + route.name.slice(1);
  document.title = label + ' — Enroth Atlas';
  if (moveFocus) {window.scrollTo(0,0); $('#view').focus({preventScroll:true});}
}
document.addEventListener('click', event => {
  const link = event.target.closest('a[data-link], a[data-route]');
  if (link && !event.metaKey && !event.ctrlKey && !event.shiftKey && !event.altKey && event.button === 0) {event.preventDefault(); go(link.getAttribute('href'));}
  if (event.target.id === 'more-results') {searchLimit += 18; searchResults();}
});
$('#back-button').addEventListener('click', () => history.back());
$('#quick-search').addEventListener('submit', event => {event.preventDefault(); searchLimit = 18; const q = $('#search-input').value.trim(); go(q ? '#/search?q=' + encodeURIComponent(q) : '#/search');});
$('#search-input').addEventListener('input', event => {searchTerm = event.target.value; if (route.name === 'search') {searchLimit = 18; history.replaceState(history.state, '', searchTerm ? '#/search?q=' + encodeURIComponent(searchTerm) : '#/search'); searchResults();}});
document.addEventListener('keydown', event => {if (event.key === '/' && !/input|textarea/i.test(document.activeElement.tagName)) {event.preventDefault(); $('#search-input').focus();}});
window.addEventListener('popstate', () => render(true));
window.addEventListener('hashchange', () => render(true));
render();
if ('serviceWorker' in navigator && location.protocol.startsWith('http')) navigator.serviceWorker.register('sw.js');
