"""Constantes de estilo: Bootstrap 5 + DMC design system."""

# ── Bootstrap CDN (somente CSS — evita conflito com Vue/Quasar) ──────
BOOTSTRAP_CDN = """
<script>
(function(){
  var t=localStorage.getItem('dmc-theme')||'dark';
  document.documentElement.setAttribute('data-theme',t);
  document.documentElement.setAttribute('data-bs-theme',t);
})();
</script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Syne:wght@600;700;800&family=Inter:wght@300;400;500;600&family=DM+Mono:wght@400;500&display=swap" rel="stylesheet">
<link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet">
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
"""

# ── Design System DMC sobre Bootstrap 5 ──────────────────────────────
CSS = """
/* ── Tokens de cor DMC ───────────────────────────────────────────── */
:root {
  --dmc-bg:        #060A06;
  --dmc-bg2:       #0C130C;
  --dmc-bg3:       #111811;
  --dmc-b1:        #182418;
  --dmc-b2:        #1E301E;
  --dmc-green:     #4ADE80;
  --dmc-gd:        #14532D;
  --dmc-amber:     #FBBF24;
  --dmc-text:      #DCE8DC;
  --dmc-muted:     #8BAA8B;
  --dmc-muted2:    #527A52;
  --dmc-fd:        'Syne', sans-serif;
  --dmc-fm:        'Inter', sans-serif;
  --dmc-mono:      'DM Mono', monospace;
  --dmc-header-bg: rgba(6,10,6,.96);
}

/* ── Tema Claro ──────────────────────────────────────────────────── */
html[data-theme="light"] {
  --dmc-bg:        #F4F8F4;
  --dmc-bg2:       #EBF2EB;
  --dmc-bg3:       #E2EDE2;
  --dmc-b1:        #C8D8C8;
  --dmc-b2:        #A8C4A8;
  --dmc-green:     #15803D;
  --dmc-gd:        #BBF7D0;
  --dmc-amber:     #B45309;
  --dmc-text:      #0A1A0A;
  --dmc-muted:     #4A7A4A;
  --dmc-muted2:    #3A6A3A;
  --dmc-header-bg: rgba(244,248,244,.97);
}
html[data-theme="light"] body { background: var(--dmc-bg) !important; color: var(--dmc-text) !important; }
html[data-theme="light"] body::after { display: none; }
html[data-theme="light"] .campo-header img { filter: invert(1) hue-rotate(180deg); }

/* ── Dialog backdrop global ─────────────────────────────────────── */
.q-dialog__backdrop {
  background: rgba(0,0,0,.84) !important;
  backdrop-filter: blur(8px) !important;
}
.q-dialog .q-card {
  background: var(--dmc-bg2) !important;
  color: var(--dmc-text) !important;
}
/* NiceGUI cards default to align-items:flex-start — override for dialogs so
   all child sections stretch to the full card width */
.q-dialog .nicegui-card {
  align-items: stretch !important;
  gap: 0 !important;
  padding: 0 !important;
}
html[data-theme="light"] .q-dialog__backdrop {
  background: rgba(0,0,0,.55) !important;
}

/* ── Bootstrap dark-mode overrides ──────────────────────────────── */
[data-bs-theme="dark"] {
  --bs-body-bg:           var(--dmc-bg);
  --bs-body-bg-rgb:       6, 10, 6;
  --bs-body-color:        var(--dmc-text);
  --bs-body-color-rgb:    220, 232, 220;
  --bs-body-font-family:  var(--dmc-fm);
  --bs-body-font-size:    14px;

  --bs-secondary-bg:      var(--dmc-bg2);
  --bs-tertiary-bg:       var(--dmc-bg3);
  --bs-border-color:      var(--dmc-b1);
  --bs-border-color-translucent: rgba(24,36,24,.6);

  --bs-primary:           var(--dmc-green);
  --bs-primary-rgb:       74, 222, 128;
  --bs-link-color:        var(--dmc-green);
  --bs-link-hover-color:  #86efac;

  --bs-card-bg:           var(--dmc-bg2);
  --bs-card-border-color: var(--dmc-b1);

  --bs-table-color:       var(--dmc-text);
  --bs-table-border-color:var(--dmc-b1);
  --bs-table-hover-bg:    rgba(74,222,128,.04);
  --bs-table-striped-bg:  rgba(74,222,128,.02);

  --bs-list-group-bg:             var(--dmc-bg2);
  --bs-list-group-border-color:   var(--dmc-b1);
  --bs-list-group-color:          var(--dmc-muted);
  --bs-list-group-action-hover-bg:rgba(74,222,128,.07);
  --bs-list-group-action-active-bg:rgba(74,222,128,.1);
}

/* ── Tipografia ──────────────────────────────────────────────────── */
html, body {
  background: var(--dmc-bg) !important;
  font-family: var(--dmc-fm) !important;
  color: var(--dmc-text) !important;
  min-height: 100vh;
}
h1,h2,h3,h4,h5,h6,.dmc-brand,.dmc-display {
  font-family: var(--dmc-fd);
  letter-spacing: .01em;
}
.font-mono, code, pre, .dmc-data {
  font-family: var(--dmc-mono) !important;
}

/* ── Scrollbar ───────────────────────────────────────────────────── */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: var(--dmc-bg2); }
::-webkit-scrollbar-thumb { background: var(--dmc-b2); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--dmc-muted2); }

/* ── Efeito de grade sutil no fundo ──────────────────────────────── */
body::after {
  content: ''; position: fixed; inset: 0; pointer-events: none; z-index: 0;
  background-image:
    repeating-radial-gradient(ellipse at 20% 65%, transparent 0, transparent 44px, rgba(74,222,128,.016) 45px, transparent 46px),
    repeating-radial-gradient(ellipse at 80% 20%, transparent 0, transparent 68px, rgba(74,222,128,.011) 69px, transparent 70px);
}

/* ── Bootstrap btn overrides ─────────────────────────────────────── */
.btn { font-family: var(--dmc-fm); font-weight: 500; letter-spacing: .01em; }

.btn-success {
  --bs-btn-color: #060A06;
  --bs-btn-bg: var(--dmc-green);
  --bs-btn-border-color: var(--dmc-green);
  --bs-btn-hover-color: #060A06;
  --bs-btn-hover-bg: #6ee7a0;
  --bs-btn-hover-border-color: #6ee7a0;
  --bs-btn-active-bg: #6ee7a0;
  --bs-btn-disabled-bg: var(--dmc-b2);
  --bs-btn-disabled-border-color: var(--dmc-b2);
}
.btn-outline-success {
  --bs-btn-color: var(--dmc-green);
  --bs-btn-border-color: var(--dmc-b2);
  --bs-btn-hover-bg: rgba(74,222,128,.12);
  --bs-btn-hover-border-color: var(--dmc-gd);
  --bs-btn-hover-color: var(--dmc-green);
  --bs-btn-active-bg: rgba(74,222,128,.18);
}
.btn-outline-secondary {
  --bs-btn-color: var(--dmc-muted);
  --bs-btn-border-color: var(--dmc-b2);
  --bs-btn-hover-bg: rgba(139,170,139,.1);
  --bs-btn-hover-border-color: var(--dmc-muted2);
  --bs-btn-hover-color: var(--dmc-text);
  --bs-btn-active-bg: rgba(139,170,139,.15);
}
.btn-outline-danger {
  --bs-btn-border-color: #7F1D1D;
  --bs-btn-color: #F87171;
  --bs-btn-hover-bg: rgba(239,68,68,.1);
  --bs-btn-hover-border-color: #991B1B;
  --bs-btn-hover-color: #FCA5A5;
}

/* ── Card ────────────────────────────────────────────────────────── */
.card {
  background: var(--dmc-bg2) !important;
  border-color: var(--dmc-b1) !important;
  border-radius: 12px !important;
  transition: border-color .18s, box-shadow .18s;
}
.card:hover { border-color: var(--dmc-b2) !important; }
.card-header, .card-footer {
  background: transparent !important;
  border-color: var(--dmc-b1) !important;
}

/* ── Form controls ───────────────────────────────────────────────── */
.form-control, .form-select {
  background-color: var(--dmc-bg) !important;
  border-color: var(--dmc-b2) !important;
  color: var(--dmc-text) !important;
  font-family: var(--dmc-fm);
  font-size: 13px;
  transition: border-color .15s, box-shadow .15s;
}
.form-control:focus, .form-select:focus {
  background-color: var(--dmc-bg) !important;
  border-color: var(--dmc-green) !important;
  color: var(--dmc-text) !important;
  box-shadow: 0 0 0 3px rgba(74,222,128,.15) !important;
}
.form-control::placeholder { color: rgba(82,122,82,.5) !important; }
.form-label {
  color: var(--dmc-muted2);
  font-size: 11px;
  font-weight: 500;
  letter-spacing: .06em;
  text-transform: uppercase;
  margin-bottom: 5px;
}
.form-check-input { background-color: var(--dmc-bg); border-color: var(--dmc-b2); }
.form-check-input:checked { background-color: var(--dmc-green); border-color: var(--dmc-green); }
.form-check-input:focus { box-shadow: 0 0 0 3px rgba(74,222,128,.2); border-color: var(--dmc-green); }
.form-check-label { color: var(--dmc-muted); font-size: 13px; }
.input-group-text {
  background: var(--dmc-bg3) !important;
  border-color: var(--dmc-b2) !important;
  color: var(--dmc-muted2) !important;
}

/* ── Table ───────────────────────────────────────────────────────── */
.table-dmc {
  --bs-table-bg: transparent;
  --bs-table-color: var(--dmc-text);
  --bs-table-border-color: var(--dmc-b1);
  --bs-table-hover-bg: rgba(74,222,128,.04);
  color: var(--dmc-text);
}
.table-dmc thead th {
  color: var(--dmc-muted2);
  font-size: 10px;
  font-weight: 500;
  letter-spacing: .12em;
  text-transform: uppercase;
  border-bottom-color: var(--dmc-b1);
  padding-top: 8px;
  padding-bottom: 8px;
}
.table-dmc tbody tr { vertical-align: middle; }
.table-dmc tbody td { border-color: var(--dmc-b1); padding: 10px 12px; }
.table-dmc tbody tr:last-child td { border-bottom: none; }

/* ── Breadcrumb ──────────────────────────────────────────────────── */
.breadcrumb { margin: 0; }
.breadcrumb-item + .breadcrumb-item::before { color: var(--dmc-muted2); content: "›"; }
.breadcrumb-item a { color: var(--dmc-muted2); text-decoration: none; transition: color .15s; }
.breadcrumb-item a:hover { color: var(--dmc-green); }
.breadcrumb-item.active { color: var(--dmc-text); }

.dmc-crumb {
  display: flex;
  flex-wrap: nowrap;
  align-items: center;
  gap: 2px;
  overflow-x: auto;
  overflow-y: hidden;
  scrollbar-width: none;
  -ms-overflow-style: none;
}
.dmc-crumb::-webkit-scrollbar { display: none; }
.dmc-crumb-sep {
  flex-shrink: 0;
  padding: 0 4px;
  color: var(--dmc-muted2);
  font-size: 13px;
  user-select: none;
}
.dmc-crumb-link {
  flex-shrink: 0;
  white-space: nowrap;
  font: 13px var(--dmc-fm);
  color: var(--dmc-muted2);
  text-decoration: none;
  cursor: pointer;
  transition: color .15s;
  padding: 2px 0;
}
.dmc-crumb-link:hover { color: var(--dmc-green); }
.dmc-crumb-cur {
  flex-shrink: 0;
  white-space: nowrap;
  font: 500 13px var(--dmc-fm);
  color: var(--dmc-text);
  padding: 2px 0;
}

/* ── Badge ───────────────────────────────────────────────────────── */
.badge-dmc {
  font-size: 9px; font-weight: 500; letter-spacing: .06em;
  padding: 3px 7px; border-radius: 4px;
}

/* ── List group ──────────────────────────────────────────────────── */
.list-group-item {
  background: transparent !important;
  border-color: var(--dmc-b1) !important;
  color: var(--dmc-muted);
  font-size: 13px;
  transition: all .15s;
}
.list-group-item-action:hover { color: var(--dmc-text) !important; }
.list-group-item.active {
  background: rgba(74,222,128,.08) !important;
  border-color: var(--dmc-gd) !important;
  color: var(--dmc-green) !important;
}

/* ── Viewer overlay ──────────────────────────────────────────────── */
#viewer { position:fixed; inset:0; background:rgba(0,0,0,.93); z-index:9000; display:none; flex-direction:column; }
#viewer.open { display:flex; }
#vhdr { height:54px; background:var(--dmc-bg2); border-bottom:1px solid var(--dmc-b1); display:flex; align-items:center; padding:0 20px; gap:14px; flex-shrink:0; }
#vtitle { font:13px var(--dmc-fm); color:var(--dmc-text); flex:1; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
#vbody { flex:1; overflow:hidden; background:#0a0a0a; }
#vbody iframe { width:100%; height:100%; border:none; }
#vbody img { width:100%; height:100%; object-fit:contain; padding:20px; }
.vbtn { display:inline-flex; align-items:center; gap:6px; padding:6px 14px; border-radius:8px; border:1px solid var(--dmc-b2); background:var(--dmc-bg3); color:var(--dmc-muted); font:12px var(--dmc-fm); cursor:pointer; transition:all .15s; text-decoration:none; flex-shrink:0; }
.vbtn:hover { border-color:var(--dmc-gd); color:var(--dmc-green); }

/* ── Animations ──────────────────────────────────────────────────── */
@keyframes fu { from { opacity:0; transform:translateY(6px); } to { opacity:1; transform:none; } }
.fu { animation: fu .22s ease both; }
@keyframes spin { from { transform:rotate(0deg); } to { transform:rotate(360deg); } }

/* ── File cards ──────────────────────────────────────────────────── */
.dmc-file-card { cursor: default; }
.dmc-file-card:hover { border-color: var(--dmc-b2) !important; box-shadow: 0 4px 24px rgba(74,222,128,.07) !important; }
.dmc-clamp2 { display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical; overflow:hidden; }
.dmc-folder-row:hover { background: rgba(74,222,128,.04) !important; }

/* ── Sidebar ─────────────────────────────────────────────────────── */
.dmc-sidebar {
  position: fixed; top: 60px; left: 0; bottom: 0; width: 260px;
  background: var(--dmc-bg2); border-right: 1px solid var(--dmc-b1);
  display: flex; flex-direction: column; z-index: 800; overflow: hidden;
}
.dmc-sidebar-scroll {
  scrollbar-width: thin;
  scrollbar-color: var(--dmc-muted2) transparent;
}
.dmc-sidebar-scroll::-webkit-scrollbar { width: 4px; }
.dmc-sidebar-scroll::-webkit-scrollbar-track { background: transparent; }
.dmc-sidebar-scroll::-webkit-scrollbar-thumb { background: var(--dmc-muted2); border-radius: 4px; }
.dmc-sidebar-scroll::-webkit-scrollbar-thumb:hover { background: var(--dmc-muted); }
.dmc-sidebar-toggle {
  display: flex; align-items: center; width: 100%;
  background: transparent; border: none; cursor: pointer;
  padding: 10px 14px; gap: 8px;
  transition: background .15s;
}
.dmc-sidebar-toggle:hover { background: rgba(74,222,128,.04); }
.dmc-sidebar-item {
  display: flex; align-items: center; gap: 10px;
  width: calc(100% - 16px); margin: 1px 8px;
  padding: 8px 12px; border-radius: 8px !important;
  background: transparent; border: 1px solid transparent !important;
  color: var(--dmc-muted) !important; font-size: 13px;
  cursor: pointer; transition: all .15s; text-align: left;
}
.dmc-sidebar-item:hover {
  background: rgba(74,222,128,.06) !important;
  color: var(--dmc-text) !important;
}
.dmc-sidebar-item.active {
  background: rgba(74,222,128,.09) !important;
  border-color: var(--dmc-b2) !important;
  color: var(--dmc-green) !important;
}
.dmc-dot { display: inline-block; width: 8px; height: 8px; border-radius: 2px; flex-shrink: 0; }

/* ── Quasar compatibility ─────────────────────────────────────────── */
.q-header { background: transparent !important; box-shadow: none !important; }
.q-notify { font-family: var(--dmc-fm) !important; }
.q-dialog__inner--minimized { padding: 0 !important; padding-left: 260px !important; justify-content: center !important; }
.q-field, .q-input { min-width: 0; font-family: var(--dmc-fm) !important; }
.q-field--outlined .q-field__control { background: var(--dmc-bg) !important; }
.q-field--outlined .q-field__control:before { border-color: var(--dmc-b2) !important; }
.q-field--outlined:hover .q-field__control:before { border-color: var(--dmc-muted2) !important; }
.q-field--outlined.q-field--focused .q-field__control:before,
.q-field--outlined.q-field--focused .q-field__control:after { border-color: var(--dmc-green) !important; }
.q-field__label { color: var(--dmc-muted2) !important; font-family: var(--dmc-fm) !important; font-size: 11px !important; }
.q-field--focused .q-field__label, .q-field--float .q-field__label { color: var(--dmc-green) !important; }
.q-field__native { color: var(--dmc-text) !important; font-family: var(--dmc-fm) !important; font-size: 13px !important; caret-color: var(--dmc-green) !important; }
.q-field__native::placeholder { color: rgba(82,122,82,.5) !important; }
.q-field__prefix, .q-field__suffix { color: var(--dmc-text) !important; }
.q-field__append .q-icon, .q-field__prepend .q-icon { color: var(--dmc-muted) !important; }
.q-field__append .q-btn:hover .q-icon { color: var(--dmc-text) !important; }
.q-field__bottom { display: none !important; }
.q-checkbox__bg { border-color: var(--dmc-b2) !important; }
.q-checkbox--truthy .q-checkbox__bg { background: var(--dmc-green) !important; border-color: var(--dmc-green) !important; }
.q-checkbox__svg { color: #060A06 !important; }
.q-checkbox__label { color: var(--dmc-muted) !important; font-family: var(--dmc-fm) !important; font-size: 13px !important; }
.q-btn { font-family: var(--dmc-fm) !important; font-weight: 500 !important; }
.q-btn--flat { color: var(--dmc-muted) !important; }

/* ── DMC Form components (para página de cadastro) ────────────────── */
.dmc-card { background: var(--dmc-bg2); border: 1px solid var(--dmc-b1); border-radius: 14px; overflow: hidden; margin-bottom: 20px; }
.dmc-card-hdr { border-bottom: 1px solid var(--dmc-b1); padding: 12px 20px; font-size: 10px; letter-spacing: .14em; text-transform: uppercase; color: var(--dmc-green); display: flex; align-items: center; gap: 8px; font-family: var(--dmc-fm); font-weight: 600; }
.dmc-card-hdr .material-icons { font-size: 14px; }
.dmc-card-body { padding: 20px; }
.dmc-label { display: block; color: var(--dmc-muted2); font-family: var(--dmc-fm); font-size: 11px; letter-spacing: .06em; text-transform: uppercase; margin-bottom: 5px; font-weight: 500; }
.dmc-input { display: block; width: 100%; background: var(--dmc-bg); border: 1px solid var(--dmc-b2); border-radius: 8px; color: var(--dmc-text); font-family: var(--dmc-fm); font-size: 13px; padding: 0 12px; height: 40px; outline: none; transition: border-color .15s, box-shadow .15s; box-sizing: border-box; min-width: 0; }
.dmc-input::placeholder { color: rgba(82,122,82,.4); font-size: 12px; }
.dmc-input:hover { border-color: var(--dmc-muted2); }
.dmc-input:focus { border-color: var(--dmc-green); box-shadow: 0 0 0 3px rgba(74,222,128,.12); }
/* ══ Sistema de Botões DMC ══════════════════════════════════════════ */
.dmc-btn, .q-btn.dmc-btn {
  display: inline-flex !important; align-items: center !important;
  justify-content: center !important; gap: 6px !important;
  height: 36px; padding: 0 16px !important;
  border-radius: 10px !important; border: 1.5px solid transparent !important;
  font: 600 12px var(--dmc-mono) !important; letter-spacing: .05em !important;
  cursor: pointer; white-space: nowrap; flex-shrink: 0;
  transition: all .18s !important; text-decoration: none;
  box-shadow: none !important; text-transform: none !important;
}
.dmc-btn .material-icons, .q-btn.dmc-btn .material-icons { font-size: 16px !important; pointer-events: none; }
/* Primário — verde sólido */
.dmc-btn-primary, .q-btn.dmc-btn-primary {
  background: var(--dmc-green) !important; color: #0A1A0A !important; border-color: transparent !important;
}
.dmc-btn-primary:hover, .q-btn.dmc-btn-primary:hover {
  filter: brightness(1.08); box-shadow: 0 4px 14px rgba(74,222,128,.25) !important;
}
html[data-theme="light"] .dmc-btn-primary,
html[data-theme="light"] .q-btn.dmc-btn-primary { color: #fff !important; }
/* Secundário — bordas */
.dmc-btn-secondary, .q-btn.dmc-btn-secondary {
  background: transparent !important; color: var(--dmc-muted) !important; border-color: var(--dmc-b2) !important;
}
.dmc-btn-secondary:hover, .q-btn.dmc-btn-secondary:hover {
  background: rgba(0,0,0,.05) !important; color: var(--dmc-text) !important; border-color: var(--dmc-muted2) !important;
}
/* Perigo — vermelho */
.dmc-btn-danger, .q-btn.dmc-btn-danger {
  background: rgba(248,113,113,.08) !important; color: #F87171 !important; border-color: rgba(248,113,113,.3) !important;
}
.dmc-btn-danger:hover, .q-btn.dmc-btn-danger:hover {
  background: rgba(248,113,113,.18) !important; border-color: #F87171 !important;
}
/* Ghost — transparente */
.dmc-btn-ghost, .q-btn.dmc-btn-ghost {
  background: transparent !important; color: var(--dmc-muted) !important; border-color: transparent !important;
}
.dmc-btn-ghost:hover, .q-btn.dmc-btn-ghost:hover {
  background: rgba(0,0,0,.06) !important; color: var(--dmc-text) !important;
}
/* Ícone — quadrado arredondado (para botões só com ícone, diferente dos flat round) */
.dmc-btn-icon {
  width: 34px !important; height: 34px !important; padding: 0 !important;
  border-radius: 8px !important; border: 1.5px solid var(--dmc-b2) !important;
  background: transparent; color: var(--dmc-muted);
  display: flex; align-items: center; justify-content: center;
  cursor: pointer; transition: all .18s; flex-shrink: 0;
}
.dmc-btn-icon:hover { background: rgba(0,0,0,.06) !important; color: var(--dmc-text) !important; }
.dmc-btn-icon .material-icons { font-size: 17px; pointer-events: none; }
/* Pequeno */
.dmc-btn.dmc-btn-sm, .q-btn.dmc-btn.dmc-btn-sm {
  height: 30px !important; padding: 0 12px !important; font-size: 11px !important; border-radius: 8px !important;
}
.dmc-tipo-btn { flex: 1; padding: 12px 0; border-radius: 10px; cursor: pointer; font-family: var(--dmc-fm); font-size: 13px; font-weight: 400; transition: all .2s; display: flex; align-items: center; justify-content: center; gap: 8px; border: 1px solid var(--dmc-b2); background: var(--dmc-bg2); color: var(--dmc-muted); }
.dmc-tipo-btn.active { border-color: var(--dmc-gd); background: rgba(74,222,128,.12); color: var(--dmc-green); font-weight: 600; }
.dmc-check-row { display: flex; align-items: center; gap: 8px; margin-bottom: 12px; cursor: pointer; }
.dmc-check-row input[type=checkbox] { width: 16px; height: 16px; accent-color: var(--dmc-green); cursor: pointer; }
.dmc-check-row span { color: var(--dmc-muted); font-family: var(--dmc-fm); font-size: 13px; }
.dmc-status { font: 11px var(--dmc-fm); min-height: 18px; margin-top: 6px; }
.dmc-cols-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
.dmc-flex-end { display: flex; gap: 8px; align-items: flex-end; }
.dmc-input[type=date], .dmc-input[type=time] { color-scheme: dark; }
html[data-theme="light"] .dmc-input[type=date],
html[data-theme="light"] .dmc-input[type=time] { color-scheme: light; }
textarea.dmc-input { resize: vertical; min-height: 40px; }
select.dmc-input { appearance: auto; cursor: pointer; }
"""

# ── Viewer HTML + JS ──────────────────────────────────────────────────
VIEWER_HTML = """
<div id="viewer">
  <div id="vhdr">
    <span class="material-icons" style="color:var(--dmc-muted2);font-size:20px;flex-shrink:0">description</span>
    <span id="vtitle">—</span>
    <button class="vbtn" onclick="closeViewer()">
      <span class="material-icons" style="font-size:15px">close</span> Fechar (Esc)
    </button>
    <a id="vdl" href="#" download class="vbtn" style="background:rgba(74,222,128,.08);border-color:var(--dmc-gd);color:var(--dmc-green)">
      <span class="material-icons" style="font-size:15px">download</span> Download
    </a>
  </div>
  <div id="vbody"></div>
</div>
<script>
function openViewer(url,name,type){
  if(type==='pdf'||type==='image'){
    window.open(url,'_blank','noopener,noreferrer');
  } else if(type==='office'){
    window.open('https://docs.google.com/viewer?url='+encodeURIComponent(window.location.origin+url)+'&embedded=false','_blank','noopener,noreferrer');
  } else {
    window.open(url,'_blank','noopener,noreferrer');
  }
}
function closeViewer(){}
</script>
"""

# ── JS utilitário: sidebar toggles + dialog centering + form masks ────
UTILS_JS = """
<script>
function dmcToggleTheme(){
  var html=document.documentElement;
  var isLight=html.getAttribute('data-theme')==='light';
  var next=isLight?'dark':'light';
  html.setAttribute('data-theme',next);
  html.setAttribute('data-bs-theme',next);
  localStorage.setItem('dmc-theme',next);
  var icon=document.getElementById('dmc-theme-icon');
  if(icon) icon.textContent=isLight?'light_mode':'dark_mode';
}
function centerDialog(){
  var dlg=document.querySelector('.q-dialog__inner--minimized');
  if(dlg){dlg.style.paddingLeft='0';dlg.style.marginLeft='0';}
}
var _dlgObs=new MutationObserver(function(muts){
  for(var m of muts) for(var n of m.addedNodes)
    if(n.classList&&n.classList.contains('q-dialog')) setTimeout(centerDialog,50);
});
_dlgObs.observe(document.body,{childList:true,subtree:false});

function _slideToggle(menuId,arrowId,openH){
  var m=document.getElementById(menuId),a=document.getElementById(arrowId);
  if(!m) return;
  var open=m.style.maxHeight&&m.style.maxHeight!=='0px'&&m.style.maxHeight!=='0';
  m.style.maxHeight=open?'0':(openH||'400px');
  if(a) a.style.transform=open?'rotate(0deg)':'rotate(180deg)';
}
function clToggle(){ _slideToggle('cl-menu','cl-arrow','280px'); }
function agToggle(){ _slideToggle('ag-menu','ag-arrow','120px'); }
function obToggle(){ _slideToggle('ob-menu','ob-arrow','120px'); }
function admToggle(){ _slideToggle('adm-menu','adm-arrow','530px'); }
function lgToggle(){  _slideToggle('lg-menu', 'lg-arrow', '60px');  }
function tcToggle(){ _slideToggle('tc-menu','tc-arrow','80px'); }
function prToggle(){ _slideToggle('pr-menu','pr-arrow','280px'); }
function finToggle(){ _slideToggle('fin-menu','fin-arrow','60px'); }
function lkToggle(){ _slideToggle('lk-menu','lk-arrow','200px'); }
function sbToggle(){ _slideToggle('sb-menu','sb-arrow','380px'); }
function sbClose(label){
  var m=document.getElementById('sb-menu'),a=document.getElementById('sb-arrow'),l=document.getElementById('sb-lbl');
  if(m) m.style.maxHeight='0';
  if(a) a.style.transform='rotate(0deg)';
  if(l&&label) l.textContent=label;
}

/* ── Máscaras de formulário (disponíveis em toda a aplicação) ── */
var dmcTipo='PF';
function maskCPF(v){
  v=v.replace(/\D/g,'').slice(0,11);
  if(v.length>9) v=v.slice(0,3)+'.'+v.slice(3,6)+'.'+v.slice(6,9)+'-'+v.slice(9);
  else if(v.length>6) v=v.slice(0,3)+'.'+v.slice(3,6)+'.'+v.slice(6);
  else if(v.length>3) v=v.slice(0,3)+'.'+v.slice(3);
  return v;
}
function maskCNPJ(v){
  v=v.replace(/\D/g,'').slice(0,14);
  if(v.length>12) v=v.slice(0,2)+'.'+v.slice(2,5)+'.'+v.slice(5,8)+'/'+v.slice(8,12)+'-'+v.slice(12);
  else if(v.length>8) v=v.slice(0,2)+'.'+v.slice(2,5)+'.'+v.slice(5,8)+'/'+v.slice(8);
  else if(v.length>5) v=v.slice(0,2)+'.'+v.slice(2,5)+'.'+v.slice(5);
  else if(v.length>2) v=v.slice(0,2)+'.'+v.slice(2);
  return v;
}
function maskCPFCNPJ(v){
  var d=v.replace(/\D/g,'');
  return d.length>11?maskCNPJ(v):maskCPF(v);
}
function maskTel(v){
  v=v.replace(/\D/g,'').slice(0,11);
  if(v.length>10) v='('+v.slice(0,2)+') '+v.slice(2,7)+'-'+v.slice(7);
  else if(v.length>6) v='('+v.slice(0,2)+') '+v.slice(2,6)+'-'+v.slice(6);
  else if(v.length>2) v='('+v.slice(0,2)+') '+v.slice(2);
  else if(v.length>0) v='('+v;
  return v;
}
function maskCEP(v){
  v=v.replace(/\D/g,'').slice(0,8);
  if(v.length>5) v=v.slice(0,5)+'-'+v.slice(5);
  return v;
}
function tcase(s){
  return (s||'').toUpperCase();
}
function setTipo(tipo){
  dmcTipo=tipo;
  document.querySelectorAll('.dmc-tipo-btn').forEach(function(b){
    b.classList.toggle('active',b.dataset.tipo===tipo);
  });
  var lbl=document.getElementById('doc-label');
  var nomeLbl=document.getElementById('nome-label');
  var inp=document.getElementById('f-doc');
  if(lbl) lbl.textContent=tipo==='PF'?'CPF':'CNPJ';
  if(nomeLbl) nomeLbl.textContent=tipo==='PF'?'Nome Completo':'Razão Social';
  if(inp){
    inp.placeholder=tipo==='PF'?'000.000.000-00':'00.000.000/0000-00';
    inp.inputMode=tipo==='PF'?'numeric':'text';
    inp.value='';
    inp.oninput=function(){this.value=tipo==='PF'?maskCPF(this.value):maskCNPJ(this.value);};
  }
  setDocStatus('','transparent');
}
function setCepStatus(prefix,msg,color){
  var el=document.getElementById('cep-status-'+prefix);
  if(el){el.textContent=msg;el.style.color=color;}
}
function setDocStatus(msg,color){
  var el=document.getElementById('doc-status');
  if(el){el.textContent=msg;el.style.color=color||'transparent';}
}
function toggleObra(checked){
  var w=document.getElementById('obra-fields-wrap');
  if(!w) return;
  var _fields=['cep','log','num','comp','bairro','cidade','uf','maps'];
  if(checked){
    _fields.forEach(function(f){
      var src=document.getElementById('f-'+f+'-end');
      var dst=document.getElementById('f-'+f+'-obra');
      if(src&&dst) dst.value=src.value;
    });
    var ss=document.getElementById('cep-status-end');
    var sd=document.getElementById('cep-status-obra');
    if(ss&&sd){sd.textContent=ss.textContent;sd.style.color=ss.style.color;}
    w.querySelectorAll('input,textarea,button').forEach(function(el){el.disabled=true;});
    w.style.opacity='0.45';
  }else{
    w.querySelectorAll('input,textarea,button').forEach(function(el){el.disabled=false;});
    w.style.opacity='1';
  }
}
async function buscarCep(prefix){
  var el=document.getElementById('f-cep-'+prefix);
  if(!el) return;
  var cep=el.value.replace(/\D/g,'');
  if(cep.length!==8){setCepStatus(prefix,'CEP inválido','#F87171');return;}
  setCepStatus(prefix,'Buscando...','#6B8F6B');
  try{
    var r=await fetch('/api/cep/'+cep);
    var d=await r.json();
    if(d.erro){setCepStatus(prefix,'CEP não encontrado','#F87171');return;}
    document.getElementById('f-log-'+prefix).value=tcase(d.logradouro);
    document.getElementById('f-bairro-'+prefix).value=tcase(d.bairro);
    document.getElementById('f-cidade-'+prefix).value=tcase(d.localidade);
    document.getElementById('f-uf-'+prefix).value=(d.uf||'').toUpperCase();
    setCepStatus(prefix,'✓ Endereço encontrado','#4ADE80');
  }catch(e){setCepStatus(prefix,'Erro ao buscar CEP','#F87171');}
}
async function buscarDoc(){
  var raw=(document.getElementById('f-doc')?.value||'').replace(/\D/g,'');
  if(dmcTipo==='PF'){
    if(raw.length!==11){setDocStatus('CPF inválido (11 dígitos)','#F87171');return;}
    setDocStatus('Consultando CPF...','#6B8F6B');
    try{
      var r=await fetch('/api/cpf/'+raw);
      var d=await r.json();
      var nome=tcase(d.nome||d.name||'');
      if(nome){document.getElementById('f-nome').value=nome;setDocStatus('✓ '+nome,'#4ADE80');}
      else{setDocStatus('CPF válido — preencha o nome manualmente','#FBBF24');}
    }catch(e){setDocStatus('CPF válido — consulta indisponível','#FBBF24');}
  }else{
    if(raw.length!==14){setDocStatus('CNPJ inválido (14 dígitos)','#F87171');return;}
    setDocStatus('Consultando Receita Federal...','#6B8F6B');
    try{
      var r=await fetch('/api/cnpj/'+raw);
      var d=await r.json();
      if(d.status==='ERROR'){setDocStatus('CNPJ não encontrado','#F87171');return;}
      var nome=tcase(d.nome||d.fantasia||'');
      document.getElementById('f-nome').value=nome;
      var tel=document.getElementById('f-tel');
      if(tel) tel.value=(d.telefone||'').split('/')[0].trim();
      if(d.logradouro) document.getElementById('f-log-end').value=tcase(d.logradouro);
      if(d.numero)     document.getElementById('f-num-end').value=d.numero;
      if(d.complemento)document.getElementById('f-comp-end').value=d.complemento;
      if(d.bairro)     document.getElementById('f-bairro-end').value=tcase(d.bairro);
      if(d.municipio)  document.getElementById('f-cidade-end').value=tcase(d.municipio);
      if(d.uf)         document.getElementById('f-uf-end').value=d.uf.toUpperCase();
      var cepR=(d.cep||'').replace(/\D/g,'');
      if(cepR.length===8) document.getElementById('f-cep-end').value=cepR.slice(0,5)+'-'+cepR.slice(5);
      setDocStatus('✓ '+nome,'#4ADE80');
    }catch(e){setDocStatus('Erro na consulta','#F87171');}
  }
}

/* ── Auto-logout por inatividade (60 min) ─────────────────────────── */
(function(){
  var WARN_MS = 55 * 60 * 1000;
  var OUT_MS  = 60 * 60 * 1000;
  window._dmcLastAct = Date.now();
  ['mousemove','keydown','mousedown','touchstart','scroll'].forEach(function(ev){
    document.addEventListener(ev, function(){ window._dmcLastAct = Date.now(); }, {passive:true});
  });
  window._dmcIdleStay = function(){
    window._dmcLastAct = Date.now();
    var w = document.getElementById('dmc-idle-warn');
    if (w) w.remove();
  };
  window._dmcIdleOut = function(){
    var b = document.getElementById('dmc-auto-logout');
    if (b) b.click(); else window.location.href = '/login';
  };
  var _warnShown = false;
  setInterval(function(){
    var idle = Date.now() - window._dmcLastAct;
    if (idle >= OUT_MS) { window._dmcIdleOut(); return; }
    if (idle >= WARN_MS && !_warnShown) {
      _warnShown = true;
      var el = document.createElement('div');
      el.id = 'dmc-idle-warn';
      el.style.cssText = 'position:fixed;inset:0;z-index:99999;background:rgba(0,0,0,.86);backdrop-filter:blur(8px);display:flex;align-items:center;justify-content:center;';
      el.innerHTML =
        '<div style="background:var(--dmc-bg2,#0C130C);border:1px solid rgba(251,191,36,.25);border-radius:14px;padding:28px 32px;max-width:360px;width:90%;text-align:center;box-shadow:0 24px 64px rgba(0,0,0,.6)">' +
        '<span class="material-icons" style="font-size:44px;color:#FBBF24;display:block;margin-bottom:12px">timer</span>' +
        '<div style="font:700 15px Syne,sans-serif;color:var(--dmc-text,#DCE8DC);margin-bottom:8px">Sessão prestes a expirar</div>' +
        '<div style="font:12px Inter,sans-serif;color:var(--dmc-muted,#8BAA8B);margin-bottom:20px">Sem atividade detectada. Logout automático em<br>' +
        '<span id="dmc-idle-cd" style="font:700 24px monospace;color:#FBBF24;display:block;margin-top:10px">5:00</span></div>' +
        '<div style="display:flex;gap:10px;justify-content:center">' +
        '<button onclick="_dmcIdleStay()" style="background:var(--dmc-green,#4ADE80);color:#060A06;border:none;border-radius:9px;padding:8px 20px;font:700 12px monospace;cursor:pointer;letter-spacing:.05em">Continuar sessão</button>' +
        '<button onclick="_dmcIdleOut()" style="background:rgba(248,113,113,.1);color:#F87171;border:1px solid rgba(248,113,113,.3);border-radius:9px;padding:8px 20px;font:700 12px monospace;cursor:pointer;letter-spacing:.05em">Sair agora</button>' +
        '</div></div>';
      document.body.appendChild(el);
    }
    if (idle < WARN_MS && _warnShown) {
      _warnShown = false;
      var w = document.getElementById('dmc-idle-warn');
      if (w) w.remove();
    }
    var cd = document.getElementById('dmc-idle-cd');
    if (cd) {
      var rem = Math.max(0, Math.round((OUT_MS - idle) / 1000));
      cd.textContent = Math.floor(rem/60) + ':' + ('0' + (rem%60)).slice(-2);
    }
  }, 5000);
})();
</script>
"""

# ── Header fixo da aplicação ──────────────────────────────────────────
HEADER_HTML = """
<header style="
  position:fixed;top:0;left:0;right:0;height:60px;z-index:1000;
  background:var(--dmc-header-bg);backdrop-filter:blur(16px);
  border-bottom:1px solid var(--dmc-b1);
  display:flex;align-items:center;padding:0 24px;gap:16px;
">
  <!-- ── Logo mark ── -->
  <div style="
    width:40px;height:40px;border-radius:11px;flex-shrink:0;
    background:linear-gradient(150deg,rgba(74,222,128,.12) 0%,rgba(74,222,128,.04) 100%);
    border:1.5px solid rgba(74,222,128,.3);
    display:flex;align-items:center;justify-content:center;
    box-shadow:0 2px 16px rgba(74,222,128,.1),inset 0 1px 0 rgba(74,222,128,.14);
    position:relative;overflow:hidden;
  ">
    <div style="position:absolute;top:-10px;left:-6px;width:28px;height:28px;
      background:radial-gradient(circle,rgba(74,222,128,.18) 0%,transparent 70%);
      pointer-events:none"></div>
    <svg width="22" height="22" viewBox="0 0 22 22" fill="none" style="position:relative;z-index:1">
      <path d="M11 3L19 17H3L11 3Z" fill="rgba(74,222,128,.11)" stroke="#4ADE80" stroke-width="1.3" stroke-linejoin="round"/>
      <path d="M6 13Q11 9.5 16 13" stroke="rgba(74,222,128,.48)" stroke-width="0.85" fill="none" stroke-linecap="round"/>
      <path d="M8 16.5Q11 14.8 14 16.5" stroke="rgba(74,222,128,.27)" stroke-width="0.85" fill="none" stroke-linecap="round"/>
      <circle cx="11" cy="3" r="1.3" fill="#4ADE80"/>
    </svg>
  </div>

  <!-- ── Brand text ── -->
  <div style="display:flex;flex-direction:column;gap:2px;line-height:1;flex-shrink:0">
    <div style="display:flex;align-items:center;gap:7px">
      <span style="font:800 17px 'Syne',sans-serif;color:var(--dmc-text);letter-spacing:.03em;line-height:1">DMC</span>
      <span style="
        font:700 8.5px 'Syne',sans-serif;color:var(--dmc-green);
        letter-spacing:.22em;text-transform:uppercase;line-height:1;
        border-left:1.5px solid rgba(74,222,128,.3);padding-left:7px;
      ">TOPOGRAFIA</span>
    </div>
    <div style="display:flex;align-items:center;gap:5px">
      <span style="font:400 9px 'DM Mono',monospace;color:var(--dmc-muted2);letter-spacing:.1em;text-transform:uppercase">Hub de Serviços</span>
      <span style="width:3px;height:3px;border-radius:50%;background:rgba(74,222,128,.3);flex-shrink:0"></span>
      <span style="font:400 9px 'DM Mono',monospace;color:rgba(82,122,82,.5);letter-spacing:.06em">Levantamento · Drone · GIS</span>
    </div>
  </div>

  <div style="flex:1"></div>

  <div id="dmc-user-slot"></div>

  <div style="width:1px;height:24px;background:var(--dmc-b1);margin:0 8px"></div>

  <div id="dmc-active-slot"></div>

  <div style="width:1px;height:24px;background:var(--dmc-b1);margin:0 8px"></div>

  <div id="clk" style="font:400 12px 'DM Mono',monospace;color:var(--dmc-green);letter-spacing:.02em">—</div>

  <div style="width:1px;height:24px;background:var(--dmc-b1);margin:0 8px"></div>

  <button id="dmc-theme-btn" onclick="dmcToggleTheme()" title="Alternar tema" style="
    width:34px;height:34px;border-radius:8px;
    border:1px solid var(--dmc-b2);background:transparent;cursor:pointer;
    display:flex;align-items:center;justify-content:center;
    color:var(--dmc-muted);transition:all .2s;flex-shrink:0;
  " onmouseover="this.style.background='rgba(128,170,128,.12)'"
     onmouseout="this.style.background='transparent'">
    <span class="material-icons" style="font-size:18px;pointer-events:none" id="dmc-theme-icon">light_mode</span>
  </button>

  <div id="dmc-logout-slot"></div>
</header>
<script>
(function tick(){
  var el=document.getElementById('clk');
  if(el){
    var d=new Date();
    el.textContent=d.toLocaleDateString('pt-BR')+' · '+d.toLocaleTimeString('pt-BR');
  }
  setTimeout(tick,1000);
})();
(function initIcon(){
  var icon=document.getElementById('dmc-theme-icon');
  if(icon) icon.textContent=document.documentElement.getAttribute('data-theme')==='light'?'dark_mode':'light_mode';
})();
</script>
"""

# ── Drag-and-drop global de upload ───────────────────────────────────
DRAG_DROP_HTML = """
<style>
#dmc-drop-overlay {
  display:none; position:fixed; inset:0; z-index:9997;
  background:rgba(10,26,10,.78); backdrop-filter:blur(4px);
  flex-direction:column; align-items:center; justify-content:center; gap:16px;
}
#dmc-drop-overlay.active { display:flex; }
#dmc-drop-border {
  position:absolute; inset:20px;
  border:2.5px dashed rgba(74,222,128,.55); border-radius:20px;
  pointer-events:none;
}
#dmc-drop-icon  { font-size:80px; color:var(--dmc-green); pointer-events:none; }
#dmc-drop-title { font:700 26px var(--dmc-fd); color:var(--dmc-green); pointer-events:none; }
#dmc-drop-sub   { font:14px var(--dmc-mono); color:var(--dmc-muted); pointer-events:none; }

#dmc-up-popup {
  display:none; position:fixed; bottom:24px; right:24px; z-index:9998;
  background:var(--dmc-bg2); border:1px solid var(--dmc-b1); border-radius:16px;
  width:340px; flex-direction:column; overflow:hidden;
  box-shadow:0 8px 40px rgba(0,0,0,.32); animation:fu .2s ease;
}
#dmc-up-popup.active { display:flex; }
#dmc-up-hdr {
  display:flex; align-items:center; gap:10px;
  padding:13px 16px; border-bottom:1px solid var(--dmc-b1);
}
#dmc-up-hdr-icon  { font-size:18px; color:var(--dmc-green); flex-shrink:0; }
#dmc-up-hdr-title { flex:1; font:600 13px var(--dmc-fm); color:var(--dmc-text); }
#dmc-up-hdr-count { font:11px var(--dmc-mono); color:var(--dmc-muted2); flex-shrink:0; }
#dmc-up-overall-wrap { padding:8px 16px 10px; }
#dmc-up-overall-bg  { height:4px; background:var(--dmc-b1); border-radius:2px; }
#dmc-up-overall-bar { height:4px; background:var(--dmc-green); border-radius:2px; width:0%; transition:width .2s; }
#dmc-up-list { max-height:220px; overflow-y:auto; }
.dmc-up-file {
  display:flex; flex-direction:column; gap:4px;
  padding:8px 16px; border-bottom:1px solid rgba(255,255,255,.03);
}
.dmc-up-file-row { display:flex; align-items:center; gap:8px; }
.dmc-up-file-name { flex:1; font:12px var(--dmc-fm); color:var(--dmc-text); overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.dmc-up-file-sz   { font:10px var(--dmc-mono); color:var(--dmc-muted2); flex-shrink:0; }
.dmc-up-file-pct  { font:10px var(--dmc-mono); color:var(--dmc-muted2); width:30px; text-align:right; flex-shrink:0; }
.dmc-up-file-bg   { height:3px; background:var(--dmc-b1); border-radius:2px; }
.dmc-up-file-bar  { height:3px; background:var(--dmc-green); border-radius:2px; width:0%; transition:width .12s; }
#dmc-up-footer {
  padding:10px 16px; display:flex; justify-content:flex-end;
  border-top:1px solid var(--dmc-b1);
}
#dmc-up-close {
  font:600 11px var(--dmc-mono); padding:6px 16px; border-radius:8px;
  border:1px solid var(--dmc-b2); background:transparent;
  color:var(--dmc-muted); cursor:pointer; transition:all .15s;
}
#dmc-up-close:not([disabled]):hover { color:var(--dmc-text); border-color:var(--dmc-muted2); }
#dmc-up-close[disabled] { opacity:.35; cursor:not-allowed; }
</style>

<div id="dmc-drop-overlay">
  <div id="dmc-drop-border"></div>
  <span class="material-icons" id="dmc-drop-icon">cloud_upload</span>
  <div id="dmc-drop-title">Soltar para enviar</div>
  <div id="dmc-drop-sub"></div>
</div>

<div id="dmc-up-popup">
  <div id="dmc-up-hdr">
    <span class="material-icons" id="dmc-up-hdr-icon">cloud_upload</span>
    <span id="dmc-up-hdr-title">Enviando arquivos…</span>
    <span id="dmc-up-hdr-count"></span>
  </div>
  <div id="dmc-up-overall-wrap">
    <div id="dmc-up-overall-bg"><div id="dmc-up-overall-bar"></div></div>
  </div>
  <div id="dmc-up-list"></div>
  <div id="dmc-up-footer">
    <button id="dmc-up-close" disabled>Fechar</button>
  </div>
</div>

<script>
(function(){
  var _dc = 0;
  function fB(b){ return b<1024?b.toFixed(0)+' B':b<1048576?(b/1024).toFixed(1)+' KB':(b/1048576).toFixed(1)+' MB'; }
  function _folder(){
    var raw = window.dmcCurrentPath || '';
    var last = Math.max(raw.lastIndexOf('/'), raw.lastIndexOf('\\\\'));
    return last >= 0 ? raw.slice(last+1) : (raw || 'Raiz');
  }

  function _showOverlay(){
    var ov = document.getElementById('dmc-drop-overlay');
    if (!ov) return;
    ov.classList.add('active');
    var sub = document.getElementById('dmc-drop-sub');
    if (sub) sub.textContent = 'Pasta: ' + (_folder() || 'Raiz');
  }
  function _hideOverlay(){
    var ov = document.getElementById('dmc-drop-overlay');
    if (ov) ov.classList.remove('active');
  }

  window.addEventListener('dragenter', function(e){
    if (!e.dataTransfer || !Array.from(e.dataTransfer.types).includes('Files')) return;
    if (++_dc === 1) _showOverlay();
  });
  window.addEventListener('dragleave', function(){ if (--_dc <= 0){ _dc=0; _hideOverlay(); } });
  window.addEventListener('dragover', function(e){ e.preventDefault(); });
  window.addEventListener('drop', function(e){
    e.preventDefault();
    _dc = 0; _hideOverlay();
    var files = Array.from(e.dataTransfer.files);
    if (files.length) _upload(files);
  });

  var _closeBtn = document.getElementById('dmc-up-close');
  if (_closeBtn) _closeBtn.addEventListener('click', function(){
    document.getElementById('dmc-up-popup').classList.remove('active');
  });

  function _upload(files){
    var path = window.dmcCurrentPath || '';
    var total = files.length;
    var doneCount = 0;
    var bytesTotal = 0;
    files.forEach(function(f){ bytesTotal += f.size; });
    var fileBytesLoaded = new Array(total).fill(0);

    var popup    = document.getElementById('dmc-up-popup');
    var list     = document.getElementById('dmc-up-list');
    var overBar  = document.getElementById('dmc-up-overall-bar');
    var hdrTitle = document.getElementById('dmc-up-hdr-title');
    var hdrCount = document.getElementById('dmc-up-hdr-count');
    var hdrIcon  = document.getElementById('dmc-up-hdr-icon');
    var closeBtn = document.getElementById('dmc-up-close');

    list.innerHTML = '';
    if (overBar)  overBar.style.width = '0%';
    if (hdrTitle) hdrTitle.textContent = 'Enviando ' + total + ' arquivo' + (total>1?'s':'') + '…';
    if (hdrCount) hdrCount.textContent = '0 / ' + total;
    if (hdrIcon)  { hdrIcon.textContent = 'cloud_upload'; hdrIcon.style.color = 'var(--dmc-green)'; }
    if (closeBtn) closeBtn.setAttribute('disabled','');
    if (popup)    popup.classList.add('active');

    var barIds = [], pctIds = [];
    files.forEach(function(f, i){
      var bid = 'upfb-' + i + '-' + Date.now();
      var pid = 'uppct-' + i + '-' + Date.now();
      barIds.push(bid); pctIds.push(pid);
      var row = document.createElement('div');
      row.className = 'dmc-up-file';
      row.innerHTML =
        '<div class="dmc-up-file-row">'
        + '<span class="material-icons" style="font-size:13px;color:var(--dmc-muted2);flex-shrink:0">insert_drive_file</span>'
        + '<span class="dmc-up-file-name" title="' + f.name + '">' + f.name + '</span>'
        + '<span class="dmc-up-file-sz">' + fB(f.size) + '</span>'
        + '<span class="dmc-up-file-pct" id="' + pid + '">0%</span>'
        + '</div>'
        + '<div class="dmc-up-file-bg"><div class="dmc-up-file-bar" id="' + bid + '"></div></div>';
      list.appendChild(row);
    });

    files.forEach(function(f, i){
      var fd = new FormData();
      fd.append('file', f);
      if (path) fd.append('path', path);
      var xhr = new XMLHttpRequest();
      xhr.upload.addEventListener('progress', function(ev){
        if (!ev.lengthComputable) return;
        fileBytesLoaded[i] = ev.loaded;
        var p = Math.round(ev.loaded / ev.total * 100);
        var bar = document.getElementById(barIds[i]);
        var pct = document.getElementById(pctIds[i]);
        if (bar) bar.style.width = p + '%';
        if (pct) pct.textContent = p + '%';
        var loaded = fileBytesLoaded.reduce(function(a,b){return a+b;},0);
        if (overBar && bytesTotal > 0) overBar.style.width = Math.min(100, Math.round(loaded/bytesTotal*100)) + '%';
      });
      xhr.addEventListener('loadend', function(){
        fileBytesLoaded[i] = f.size;
        var bar = document.getElementById(barIds[i]);
        var pct = document.getElementById(pctIds[i]);
        if (bar) bar.style.width = '100%';
        if (pct) pct.textContent = '✓';
        doneCount++;
        if (hdrCount) hdrCount.textContent = doneCount + ' / ' + total;
        var loaded = fileBytesLoaded.reduce(function(a,b){return a+b;},0);
        if (overBar && bytesTotal>0) overBar.style.width = Math.min(100, Math.round(loaded/bytesTotal*100)) + '%';
        if (doneCount === total){
          if (hdrTitle) hdrTitle.textContent = total + ' arquivo' + (total>1?'s':'') + ' enviado' + (total>1?'s':'') + '!';
          if (hdrIcon)  { hdrIcon.textContent='check_circle'; hdrIcon.style.color='var(--dmc-green)'; }
          if (overBar)  overBar.style.width = '100%';
          if (closeBtn) closeBtn.removeAttribute('disabled');
          setTimeout(function(){
            var b = document.getElementById('dmc-refresh-btn');
            if (b) b.click();
          }, 600);
        }
      });
      xhr.open('POST', '/upload');
      xhr.send(fd);
    });
  }
})();
</script>
"""
