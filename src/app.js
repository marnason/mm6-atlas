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
const atlasMaps = window.OPENYAMM?.maps || [];
const mapByRegion = new Map(atlasMaps.map(map => [map.region, map]));
const mapById = new Map(atlasMaps.map(map => [map.id, map]));
const allPlaces = atlasMaps.flatMap(map => map.pois.map(poi => ({map, poi})));
const nameKey = value => value.toLowerCase().replace(/[^a-z0-9]+/g,'');
const guideForPlace = (map, poi) => pages.find(page => page.region === map.region && nameKey(page.title) === nameKey(poi.n));
const placeURL = (map, poi) => guideForPlace(map, poi) ? guideURL(guideForPlace(map, poi)) : regionURL(map.region) + '?place=' + encodeURIComponent(poi.id);
const placeGroups = [
  ['highlights','Highlights',poi => ['entrance','bonus','hint','objective','castle'].includes(poi.t)],
  ['all','All places',() => true],
  ['shops','Shops',poi => poi.t === 'vendor'],
  ['services','Services',poi => ['service','transport','guild'].includes(poi.t)],
  ['homes','Homes',poi => poi.t === 'house'],
  ['routes','Routes',poi => poi.t === 'exit']
];
let route = {name:'map'}, searchTerm = '', searchLimit = 18;

function parseRoute() {
  const hash = location.hash.replace(/^#\/?/, '');
  const [path, search = ''] = hash.split('?');
  const [rawName, value] = path.split('/');
  const name = rawName || 'map';
  if (name === 'region' && regionBySlug.has(value)) {
    const params = new URLSearchParams(search);
    const region = regionBySlug.get(value), map = mapByRegion.get(region);
    const selected = map?.pois.find(poi => poi.id === params.get('place'));
    return {name, region, selected, mode:params.get('view') === 'guides' ? 'guides' : 'places', group:placeGroups.some(group => group[0] === params.get('group')) ? params.get('group') : selected ? 'all' : 'highlights'};
  }
  if (name === 'guide' && pageById.has(decodeURIComponent(value || ''))) return {name, page:pageById.get(decodeURIComponent(value))};
  if (name === 'place') {
    const [mapId, poiId] = path.split('/').slice(1);
    const map = mapById.get(mapId), poi = map?.pois.find(item => item.id === poiId);
    if (poi) return {name, map, poi};
  }
  if (name === 'search') return {name, query:new URLSearchParams(search).get('q') || ''};
  if (['map','regions','about'].includes(name)) return {name};
  return {name:'not-found'};
}

function go(href, replace = false) {
  if (location.hash === href) return render();
  history[replace ? 'replaceState' : 'pushState'](replace ? history.state : {atlas:true}, '', href);
  render(true);
}

const crumb = (label, href) => href ? '<a href="' + href + '" data-link>' + esc(label) + '</a>' : '<span aria-current="page">' + esc(label) + '</span>';
function renderNavigation() {
  const parts = [crumb('World map', route.name === 'map' ? null : '#/map')];
  if (route.name === 'regions') parts.push(crumb('Regions'));
  if (route.name === 'region') parts.push(crumb(route.region));
  if (route.name === 'guide') parts.push(crumb(route.page.region, regionURL(route.page.region)), crumb(route.page.title));
  if (route.name === 'place') parts.push(crumb(route.map.region, regionURL(route.map.region)), crumb(route.poi.n));
  if (route.name === 'search') parts.push(crumb('Search'));
  if (route.name === 'about') parts.push(crumb('About'));
  if (route.name === 'not-found') parts.push(crumb('Not found'));
  $('#breadcrumbs').innerHTML = parts.join('<span class="crumb-separator" aria-hidden="true">/</span>');
  $('#back-button').hidden = !history.state?.atlas;
  document.querySelectorAll('.primary-nav a').forEach(link => {
    const current = link.dataset.route === route.name || (['region','place'].includes(route.name) && link.dataset.route === 'regions');
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
const placeType = poi => poi.k || ({entrance:'Dungeon entrance',exit:'Region exit',bonus:'Shrine or fountain',hint:'Obelisk',objective:'Landmark',castle:'Castle',house:'Home',service:'Service',vendor:'Shop',guild:'Guild',transport:'Transport'}[poi.t] || 'Place');
function placeRow(map, poi) {
  return '<a class="place-row" href="' + placeURL(map,poi) + '" data-link><span class="place-kind">' + esc(placeType(poi)) + '</span><strong>' + esc(poi.n) + '</strong><span class="place-arrow" aria-hidden="true">→</span></a>';
}
function regionMap(map, points) {
  const markers = points.map((poi,index) => '<a class="poi-marker poi-' + esc(poi.t) + (route.selected?.id === poi.id ? ' selected' : '') + '" href="' + placeURL(map,poi) + '" data-link style="left:' + (poi.u * 100) + '%;top:' + (poi.v * 100) + '%" aria-label="' + esc(poi.n + ', ' + placeType(poi)) + (guideForPlace(map,poi) ? ', opens guide' : ', show details') + '" title="' + esc(poi.n) + '"' + (route.selected?.id === poi.id ? ' aria-current="location"' : '') + '><span>' + (index + 1) + '</span></a>').join('');
  return '<div class="region-map-toolbar"><span>' + esc(map.sourceName) + ' · 1024 × 1024 map</span><button type="button" class="zoom-button" data-zoom>View at full size</button></div><div class="region-map-scroll"><div class="region-map-surface"><img src="' + map.image + '" alt="High-resolution map of ' + esc(map.sourceName) + '" loading="lazy"><div class="poi-markers">' + markers + '</div></div></div>';
}
function renderRegion(region) {
  const items = pages.filter(page => page.region === region);
  const map = mapByRegion.get(region);
  const tabs = '<nav class="region-tabs" aria-label="Region views"><a href="' + regionURL(region) + '" data-link class="' + (route.mode === 'places' ? 'active' : '') + '">Map & places' + (map ? ' · ' + map.pois.length : '') + '</a><a href="' + regionURL(region) + '?view=guides" data-link class="' + (route.mode === 'guides' ? 'active' : '') + '">Magic Grounds guides · ' + items.length + '</a></nav>';
  if (route.mode === 'guides') return heading('Region guide',region,'Recovered maps and field notes from Magic Grounds.','<a class="text-link" href="#/regions" data-link>All regions →</a>') + tabs + '<div class="guide-list">' + items.map(guideRow).join('') + '</div>';
  if (!map) return heading('Region',region) + tabs + '<p class="empty">No detailed map is available for this region.</p>';
  const group = placeGroups.find(group => group[0] === route.group) || placeGroups[0];
  const points = map.pois.filter(group[2]);
  const filters = placeGroups.map(([key,label,test]) => '<a href="' + regionURL(region) + (key === 'highlights' ? '' : '?group=' + key) + '" data-link data-replace-route class="' + (route.group === key ? 'active' : '') + '">' + label + ' <small>' + map.pois.filter(test).length + '</small></a>').join('');
  const selected = route.selected;
  const detail = selected ? '<section class="selected-place" aria-label="Selected place"><div class="selected-place-top"><span class="place-kind">' + esc(placeType(selected)) + '</span><a href="' + regionURL(region) + '?group=all" data-link aria-label="Close location details">×</a></div><h2>' + esc(selected.n) + '</h2>' + (selected.x === undefined ? '' : '<p>In-game X ' + selected.x.toLocaleString() + ' · Y ' + selected.y.toLocaleString() + '</p>') + (selected.people?.length ? '<p>People: ' + esc(selected.people.join(', ')) + '</p>' : '') + (selected.d ? '<p>' + esc(selected.d) + '</p>' : '') + '</section>' : '';
  return heading('Explore the region',region,'High-resolution map with in-game locations and coordinates.','<a class="text-link" href="#/regions" data-link>All regions →</a>') + tabs + '<div class="place-filters" aria-label="Place categories">' + filters + '</div><div class="region-explorer"><div class="region-map-column">' + regionMap(map,points) + '</div><aside class="place-list">' + detail + '<div class="place-list-heading"><strong>' + esc(group[1]) + '</strong><small>' + points.length + ' places</small></div><div class="place-list-items">' + points.slice().sort((a,b) => a.n.localeCompare(b.n)).map(poi => placeRow(map,poi)).join('') + '</div></aside></div><p class="map-credit">Map and coordinates: OpenYAMM. Coordinates use the game world, not real-world GPS. <a href="LICENSE.md">Source credits</a></p>';
}
function renderGuide(page) {
  const mapImage = page.images.at(-1);
  const image = (src, main = false) => '<figure' + (main ? ' class="guide-main-map"' : '') + '><img src="assets/places/' + encodeURI(src) + '" alt="' + (main ? 'Map of ' : 'Scene from ') + esc(page.title) + '"' + (main ? '' : ' loading="lazy"') + '><figcaption>' + (main ? 'Guide map' : 'Additional view') + ' · ' + esc(src.split('/').pop()) + '</figcaption></figure>';
  const images = mapImage ? '<div class="guide-visuals">' + image(mapImage,true) + (page.images.length > 1 ? '<div class="guide-supplementary">' + page.images.slice(0,-1).map(src => image(src)).join('') + '</div>' : '') + '</div>' : '';
  const siblings = pages.filter(item => item.region === page.region), index = siblings.findIndex(item => item.id === page.id), previous = siblings[index - 1], next = siblings[index + 1];
  const pager = (item, label) => item ? '<a href="' + guideURL(item) + '" data-link><small>' + label + '</small><strong>' + esc(item.title) + '</strong></a>' : '<span></span>';
  const mapped = mapByRegion.get(page.region);
  const matched = mapped?.pois.find(poi => nameKey(poi.n) === nameKey(page.title));
  const mapLink = matched ? '<a href="' + regionURL(page.region) + '?place=' + encodeURIComponent(matched.id) + '" data-link>See location on regional map →</a>' : '<a href="' + regionURL(page.region) + '" data-link>View regional map →</a>';
  return '<article class="guide-view">' + heading(page.region + ' · Guide ' + (index + 1) + ' of ' + siblings.length,page.title,'','<a class="text-link" href="' + regionURL(page.region) + '?view=guides" data-link>All ' + esc(page.region) + ' guides →</a>') + '<div class="guide-content">' + images + '<section class="guide-notes"><h2>Field notes</h2><p>' + esc(page.body).replace(/\n/g,'<br>') + '</p></section></div><div class="guide-source">' + mapLink + ' · Original: <a href="https://user.xmission.com/~tnelson/mm6/gameplay/places/' + encodeURI(page.sourcePath) + '" target="_blank" rel="noopener">Magic Grounds ↗</a></div><nav class="guide-pager" aria-label="Guide navigation">' + pager(previous,'← Previous guide') + pager(next,'Next guide →') + '</nav></article>';
}
function searchResults() {
  const words = searchTerm.toLowerCase().trim().split(/\s+/).filter(Boolean);
  const guides = words.length ? pages.filter(page => words.every(word => (page.title + ' ' + page.region + ' ' + page.body).toLowerCase().includes(word))).map(page => ({kind:'guide',name:page.title,page})) : [];
  const places = words.length ? allPlaces.filter(({map,poi}) => !guideForPlace(map,poi) && words.every(word => (poi.n + ' ' + map.region + ' ' + placeType(poi) + ' ' + (poi.d || '') + ' ' + (poi.people || []).join(' ')).toLowerCase().includes(word))).map(item => ({kind:'place',name:item.poi.n,...item})) : [];
  const matches = [...guides,...places].sort((a,b) => Number(b.name.toLowerCase().startsWith(searchTerm.toLowerCase())) - Number(a.name.toLowerCase().startsWith(searchTerm.toLowerCase())) || a.name.localeCompare(b.name));
  $('#search-results').innerHTML = words.length ? '<p class="result-count">' + guides.length + ' guides · ' + places.length + ' mapped places</p><div class="search-result-list">' + (matches.slice(0,searchLimit).map((item,index) => item.kind === 'guide' ? guideRow(item.page,index) : placeRow(item.map,item.poi)).join('') || '<p class="empty">No matches. Try a place, dungeon, or treasure name.</p>') + '</div>' + (matches.length > searchLimit ? '<button class="more-button" id="more-results" type="button">Show more results (' + (matches.length - searchLimit) + ' remaining)</button>' : '') : '<div class="search-prompt"><span>⌕</span><h2>Find a place or secret</h2><p>Search ' + pages.length + ' guides and ' + allPlaces.length + ' mapped places.</p></div>';
}
function renderSearch() { return heading('Full atlas search','Search the atlas','Find places, game coordinates, dungeon notes, and guides across every region.') + '<div id="search-results"></div>'; }
function renderAbout() { return heading('Preservation note','About this atlas') + '<div class="about-copy"><p>Enroth Atlas combines recovered Magic Grounds maps and notes with high-resolution region maps and location data exported from OpenYAMM. All site data and map images are bundled for offline use once the site has been visited.</p><p>The archive contains ' + pages.length + ' searchable guides and ' + allPlaces.length + ' mapped places across ' + regions.length + ' regions. Map X/Y coordinates are approximate in-game locations, not real-world GPS. See the <a href="LICENSE.md">source credits and license</a> or <a href="https://github.com/marnason/mm6-atlas">project repository</a>.</p><p>This is an unofficial fan project and is not affiliated with Ubisoft or New World Computing.</p></div>'; }
function render(moveFocus = false) {
  route = parseRoute(); renderNavigation();
  if (route.name === 'place') { go(placeURL(route.map,route.poi), true); return; }
  $('#search-input').value = route.name === 'search' ? route.query : '';
  if (route.name === 'search') searchTerm = route.query;
  const views = {map:renderMap,regions:renderRegions,region:()=>renderRegion(route.region),guide:()=>renderGuide(route.page),search:renderSearch,about:renderAbout};
  $('#view').innerHTML = views[route.name]?.() || heading('Lost passage','Page not found') + '<a class="text-link" href="#/map" data-link>Return to the map →</a>';
  if (route.name === 'search') searchResults();
  const label = route.name === 'guide' ? route.page.title : route.name === 'place' ? route.poi.n : route.name === 'region' ? route.region : route.name === 'map' ? 'World Map' : route.name[0].toUpperCase() + route.name.slice(1);
  document.title = label + ' — Enroth Atlas';
  if (moveFocus) {window.scrollTo(0,0); $('#view').focus({preventScroll:true});}
}
document.addEventListener('click', event => {
  const link = event.target.closest('a[data-link], a[data-route]');
  if (link && !event.metaKey && !event.ctrlKey && !event.shiftKey && !event.altKey && event.button === 0) {event.preventDefault(); go(link.getAttribute('href'),link.hasAttribute('data-replace-route'));}
  if (event.target.id === 'more-results') {searchLimit += 18; searchResults();}
  if (event.target.matches('[data-zoom]')) {
    const surface = event.target.closest('.region-map-column').querySelector('.region-map-surface');
    const zoomed = surface.classList.toggle('zoomed');
    event.target.textContent = zoomed ? 'Fit to panel' : 'View at full size';
  }
});
$('#back-button').addEventListener('click', () => history.back());
$('#quick-search').addEventListener('submit', event => {event.preventDefault(); searchLimit = 18; const q = $('#search-input').value.trim(); go(q ? '#/search?q=' + encodeURIComponent(q) : '#/search');});
$('#search-input').addEventListener('input', event => {searchTerm = event.target.value; if (route.name === 'search') {searchLimit = 18; history.replaceState(history.state, '', searchTerm ? '#/search?q=' + encodeURIComponent(searchTerm) : '#/search'); searchResults();}});
document.addEventListener('keydown', event => {if (event.key === '/' && !/input|textarea/i.test(document.activeElement.tagName)) {event.preventDefault(); $('#search-input').focus();}});
window.addEventListener('popstate', () => render(true));
window.addEventListener('hashchange', () => render(true));
render();
if ('serviceWorker' in navigator && location.protocol.startsWith('http')) navigator.serviceWorker.register('sw.js');
