export const THEME_KEY = "ui_theme";
export const DEFAULT_THEME = { mode: "system", preset: "ocean" };

export const PRESETS = [
  { id: "ocean", label: "Océan", swatch: "linear-gradient(135deg, #00C6FF, #0078FF)" },
  { id: "nature", label: "Nature", swatch: "linear-gradient(135deg, #18c480, #0b8f5c)" },
  { id: "crepuscule", label: "Crépuscule", swatch: "linear-gradient(135deg, #FF6B00, #d9480f)" },
  { id: "royal", label: "Royal", swatch: "linear-gradient(135deg, #9b2cfa, #2c62fa)" },
  { id: "monochrome", label: "Monochrome", swatch: "linear-gradient(135deg, #475569, #1e293b)" },
];

export function readTheme() {
  try {
    return { ...DEFAULT_THEME, ...JSON.parse(localStorage.getItem(THEME_KEY) || "{}") };
  } catch {
    return DEFAULT_THEME;
  }
}

export function applyTheme({ mode, preset }) {
  const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
  const isDark = mode === "dark" || (mode === "system" && prefersDark);
  document.documentElement.classList.toggle("dark", isDark);
  document.documentElement.dataset.preset = preset;
}

export function saveTheme(theme) {
  try {
    localStorage.setItem(THEME_KEY, JSON.stringify(theme));
  } catch {
    // Stockage indisponible : le thème s'applique quand même pour cette visite.
  }
  applyTheme(theme);
}

// Exécuté dans le <head> avant le premier rendu, pour éviter un flash de thème.
export const THEME_SCRIPT = `(function(){try{
var s=JSON.parse(localStorage.getItem('${THEME_KEY}')||'{}');
var mode=s.mode||'system',preset=s.preset||'ocean';
var dark=mode==='dark'||(mode==='system'&&matchMedia('(prefers-color-scheme: dark)').matches);
if(dark)document.documentElement.classList.add('dark');
document.documentElement.dataset.preset=preset;
}catch(e){document.documentElement.dataset.preset='ocean';}})();`;
