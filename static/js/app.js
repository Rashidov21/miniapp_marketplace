/**
 * Telegram Mini App API helpers (vanilla JS).
 */
(function () {
  const API_BASE = "/api";

  function getInitData() {
    try {
      return window.Telegram && window.Telegram.WebApp
        ? window.Telegram.WebApp.initData || ""
        : "";
    } catch (e) {
      return "";
    }
  }

  function getStartParam() {
    try {
      const u = window.Telegram && window.Telegram.WebApp && window.Telegram.WebApp.initDataUnsafe;
      return (u && u.start_param) || "";
    } catch (e) {
      return "";
    }
  }

  function apiHeaders() {
    const h = { Accept: "application/json" };
    const init = getInitData();
    if (init) h["X-Telegram-Init-Data"] = init;
    return h;
  }

  async function apiFetch(path, options) {
    const opts = options || {};
    const headers = Object.assign({}, apiHeaders(), opts.headers || {});
    if (opts.body && !(opts.body instanceof FormData) && !headers["Content-Type"]) {
      headers["Content-Type"] = "application/json";
    }
    const res = await fetch(API_BASE + path, Object.assign({}, opts, { headers }));
    const text = await res.text();
    let data = null;
    try {
      data = text ? JSON.parse(text) : null;
    } catch (e) {
      data = { detail: text };
    }
    if (!res.ok) {
      const err = new Error((data && (data.detail || data.error)) || res.statusText);
      err.status = res.status;
      err.data = data;
      throw err;
    }
    return data;
  }

  function showAlert(message) {
    try {
      if (window.Telegram && window.Telegram.WebApp) {
        window.Telegram.WebApp.showAlert(message);
        return;
      }
    } catch (e) {}
    window.alert(message);
  }

  function ready() {
    try {
      if (window.Telegram && window.Telegram.WebApp) {
        window.Telegram.WebApp.ready();
        window.Telegram.WebApp.expand();
      }
    } catch (e) {}
  }

  window.MiniApp = {
    getInitData,
    getStartParam,
    apiHeaders,
    apiFetch,
    showAlert,
    ready,
  };
})();
