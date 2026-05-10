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

/* Chat */
function appendMessage(text, isUser = false) {
  const msgs = $('chat-msgs');
  const div = document.createElement('div');
  div.className = `message ${isUser ? 'user' : 'ai'}`;
  
  // Convert basic markdown (bold)
  let formattedText = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  // Format lists
  formattedText = formattedText.replace(/â€¢ (.*?)(?=\n|$)/g, '<li>$1</li>');
  if(formattedText.includes('<li>')) formattedText = `<ul>${formattedText}</ul>`;
  // Format newlines
  formattedText = formattedText.replace(/\n/g, '<br>');
  
  div.innerHTML = `<div class="msg-bubble">${formattedText}</div>`;
  
  // Remove suggestion chips if they exist
  const chips = $('chat-suggestions');
  if (chips && isUser) chips.style.display = 'none';
  
  msgs.appendChild(div);
  msgs.scrollTop = msgs.scrollHeight;
}

function sendChat(message) {
  appendMessage(message, true);
  
  // Show typing indicator
  const typingId = 'typing-' + Date.now();
  const msgs = $('chat-msgs');
  const typing = document.createElement('div');
  typing.className = 'message ai typing-indicator';
  typing.id = typingId;
  typing.innerHTML = '<div class="msg-bubble"><span class="dot"></span><span class="dot"></span><span class="dot"></span></div>';
  msgs.appendChild(typing);
  msgs.scrollTop = msgs.scrollHeight;
  
  const headers = { 'Content-Type': 'application/json' };
  const token = localStorage.getItem('dl_token');
  if (token) headers['Authorization'] = `Bearer ${token}`;
  
  fetch(API + '/api/chat', {
    method: 'POST',
    headers: headers,
    body: JSON.stringify({ message: message })
  })
  .then(r => r.json())
  .then(data => {
    $(typingId).remove();
    appendMessage(data.text || 'Sorry, I could not process that request.');
  })
  .catch(err => {
    $(typingId).remove();
    appendMessage('Network error. Operating in offline mode. What is the fine for driving without a helmet?');
    $('offline-badge').style.display = 'flex';
  });
}

/* Calculator */
let CACHED_VIOLATIONS = null;
let CACHED_STATES = null;

function loadCalcData() {
  if (CACHED_VIOLATIONS) return;
  
  // Load States
  fetch(API + '/api/states')
    .then(r => r.json())
    .then(data => {
      CACHED_STATES = data;
      const select = $('calc-state');
      Object.keys(data).forEach(key => {
        const opt = document.createElement('option');
        opt.value = key;
        opt.innerText = data[key];
        select.appendChild(opt);
      });
    }).catch(e => console.log('Offline: cannot load states'));
    
  // Load Violations
  fetch(API + '/api/violations')
    .then(r => r.json())
    .then(data => {
      CACHED_VIOLATIONS = data;
      const list = $('violation-list');
      Object.keys(data).forEach(key => {
        const item = document.createElement('div');
        item.className = 'violation-item';
        item.innerHTML = `
          <label>
            <input type="checkbox" value="${key}" class="viol-cb">
            <span>${data[key]}</span>
          </label>
        `;
        list.appendChild(item);
      });
      
      // Add event listeners to checkboxes
      document.querySelectorAll('.viol-cb').forEach(cb => {
        cb.addEventListener('change', updateSelectedViolations);
      });
    }).catch(e => console.log('Offline: cannot load violations'));
}

function updateSelectedViolations() {
  const selected = [];
  document.querySelectorAll('.viol-cb:checked').forEach(cb => {
    selected.push(cb.nextElementSibling.innerText);
  });
  
  const container = $('selected-violations');
  if (selected.length === 0) {
    container.innerHTML = '<span class="placeholder-text">Select at least one violation...</span>';
  } else {
    container.innerHTML = selected.map(v => `<span class="chip">${v}</span>`).join('');
  }
}

function calculateFine() {
  const violations = Array.from(document.querySelectorAll('.viol-cb:checked')).map(cb => cb.value);
  
  if (violations.length === 0) {
    showToast('Please select at least one violation', 'error');
    return;
  }
  
  const state = $('calc-state').value;
  const vehicle = $('calc-vehicle').value;
  const isRepeat = document.querySelector('input[name="offense_type"]:checked').value === 'repeat';
  
  const payload = {
    violations: violations,
    vehicle_type: vehicle,
    is_repeat: isRepeat
  };
  if (state !== 'national') payload.state = state;
  
  fetch(API + '/api/calculate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  })
  .then(r => r.json())
  .then(data => {
    if (data.error) throw new Error(data.error);
    
    const results = $('calc-results');
    const breakdown = $('result-breakdown');
    
    breakdown.innerHTML = data.violations.map(v => `
      <div class="fine-row">
        <div>
          <strong>${v.violation_name}</strong>
          <div class="text-sm text-muted">Sec ${v.section}</div>
        </div>
        <div class="text-right">
          <strong>Rs. ${v.total_fine}</strong>
        </div>
      </div>
    `).join('');
    
    $('result-total-amt').innerText = `Rs. ${data.grand_total}`;
    results.style.display = 'block';
    results.scrollIntoView({ behavior: 'smooth' });
  })
  .catch(err => {
    showToast('Failed to calculate fine. Check connection.', 'error');
  });
}


