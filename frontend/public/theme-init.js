// Applies the stored theme before the first paint. useTheme only runs after
// React renders, which showed the OS theme for a frame on every load.
// A plain external file rather than an inline <script>, so it keeps working
// under a `script-src 'self'` CSP. Keep STORAGE_KEY in sync with
// src/lib/useTheme.ts.
(function () {
  var STORAGE_KEY = "vulnscan-theme";
  try {
    var stored = localStorage.getItem(STORAGE_KEY);
    if (stored === "light" || stored === "dark") {
      document.documentElement.setAttribute("data-theme", stored);
    }
  } catch (e) {
    // Storage blocked (some private modes): fall back to the OS theme.
  }
})();
