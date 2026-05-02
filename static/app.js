/* DriveLegal.ai â€” Client v1.2 */

const API = '';
let MAP = null;
let MAP_READY = false;
let CURRENT_PANEL = 'chat';
let THEME = localStorage.getItem('dl_theme') || 'dark';
let MAP_TILE_LAYER = null;

const TILE_DARK = 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png';
const TILE_LIGHT = 'https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png';

// Translation dictionary will be loaded here
let i18n = {};
let currentLang = 'en';

function $(id) { return document.getElementById(id); }

/* Navigation */
function go(panel) {
  document.querySelectorAll('.panel').forEach(el => el.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
  
  const target = $('p-' + panel);
  if (target) target.classList.add('active');
  
  const navBtn = document.querySelector('.nav-item[data-panel="' + panel + '"]');
  if (navBtn) navBtn.classList.add('active');
  
  CURRENT_PANEL = panel;
  
  // Close mobile sidebar if open
  document.body.classList.remove('sidebar-open');
  
  // Update header title
  const title = navBtn ? navBtn.querySelector('.sidebar-text').innerText : 'DriveLegal.ai';
  $('h-title').innerText = title;
  
  // Init map if needed
  if (panel === 'map' && !MAP_READY) setTimeout(initMap, 100);
  if (panel === 'map' && MAP) setTimeout(() => MAP.invalidateSize(), 200);
  
  // Load data if needed
  if (panel === 'calculator') loadCalcData();
  if (panel === 'dashboard') loadDashboard();
}

/* UI interactions */
document.addEventListener('DOMContentLoaded', () => {
  // Theme initialization
  if (THEME === 'light') {
    document.body.classList.add('light-theme');
  }
  
  // Event listeners
  $('btn-theme').addEventListener('click', toggleTheme);
  $('btn-menu').addEventListener('click', () => document.body.classList.add('sidebar-open'));
  $('btn-close-sidebar').addEventListener('click', () => document.body.classList.remove('sidebar-open'));
  
  // Chat input
  $('btn-send').addEventListener('click', () => {
    const input = $('chat-input');
    if (input.value.trim()) {
      sendChat(input.value.trim());
      input.value = '';
    }
  });
  
  $('chat-input').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
      const input = $('chat-input');
      if (input.value.trim()) {
        sendChat(input.value.trim());
        input.value = '';
      }
    }
  });
  
  // Calculator
  $('btn-calculate').addEventListener('click', calculateFine);
  
  // Auth Modal
  $('btn-auth-action').addEventListener('click', () => {
    $('auth-modal').classList.add('active');
  });
  
  $('btn-auth-toggle').addEventListener('click', () => {
    const isLogin = $('auth-title').innerText === 'Sign In';
    $('auth-title').innerText = isLogin ? 'Create Account' : 'Sign In';
    $('btn-auth-submit').innerText = isLogin ? 'Create Account' : 'Sign In';
    $('btn-auth-toggle').innerText = isLogin ? 'Already have an account? Sign in' : "Don't have an account? Create one";
    document.querySelector('.auth-register-only').style.display = isLogin ? 'block' : 'none';
  });
  
  // Emergency
  $('btn-sos').addEventListener('click', activateSOS);
  
  // Load data
  loadTranslations();
  checkAuth();
  
  // PWA setup
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/sw.js').catch(console.error);
  }
});

/* Theme */
function toggleTheme() {
  THEME = THEME === 'dark' ? 'light' : 'dark';
  if (THEME === 'light') {
    document.body.classList.add('light-theme');
  } else {
    document.body.classList.remove('light-theme');
  }
  localStorage.setItem('dl_theme', THEME);
  updateMapTiles();
  showToast(THEME === 'dark' ? 'Switched to dark mode' : 'Switched to light mode');
}

/* Map initialization */
function initMap() {
  if (MAP_READY || typeof L === 'undefined') return;
  MAP_READY = true;

  MAP = L.map('map-view', {
    zoomControl: false, attributionControl: false,
    zoomAnimation: true, markerZoomAnimation: true
  }).setView([20.5937, 78.9629], 5);

  MAP_TILE_LAYER = L.tileLayer(THEME === 'light' ? TILE_LIGHT : TILE_DARK, {
    maxZoom: 19, subdomains: 'abcd'
  }).addTo(MAP);

  L.control.zoom({ position: 'bottomleft' }).addTo(MAP);
  
  // Auto-locate
  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        MAP.setView([pos.coords.latitude, pos.coords.longitude], 13);
        L.marker([pos.coords.latitude, pos.coords.longitude]).addTo(MAP)
          .bindPopup("You are here").openPopup();
      },
      () => {}
    );
  }
  
  // Load hazards
  fetch(API + '/api/hazards')
    .then(r => r.json())
    .then(data => {
      if(Array.isArray(data)) {
        data.forEach(h => {
          L.circleMarker([h.lat, h.lng], {
            color: h.type === 'accident' ? 'red' : 'orange',
            radius: 8,
            fillOpacity: 0.7
          }).addTo(MAP).bindPopup(`<b>${h.type.toUpperCase()}</b><br>${h.description}`);
        });
      }
    }).catch(e => console.log('Offline: cannot load map hazards'));
}

function updateMapTiles() {
  if (!MAP || !MAP_TILE_LAYER) return;
  MAP.removeLayer(MAP_TILE_LAYER);
  MAP_TILE_LAYER = L.tileLayer(THEME === 'light' ? TILE_LIGHT : TILE_DARK, {
    maxZoom: 19, subdomains: 'abcd'
  }).addTo(MAP);
}


