/**
 * Telegram Mini App helpers — API, UX, safe DOM.
 * v2 — hapticLight + merge with stale cached MiniApp
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

  /** Telegram user from initDataUnsafe (no server trust — UX prefill only). */
  function getTelegramUser() {
    try {
      const u = window.Telegram && window.Telegram.WebApp && window.Telegram.WebApp.initDataUnsafe;
      return (u && u.user) || null;
    } catch (e) {
      return null;
    }
  }

  function escapeHtml(str) {
    if (str == null || str === "") return "";
    const d = document.createElement("div");
    d.textContent = String(str);
    return d.innerHTML;
  }

  /** Simple display name: first + last or username. */
  function getSuggestedName() {
    const u = getTelegramUser();
    if (!u) return "";
    const parts = [u.first_name, u.last_name].filter(Boolean);
    if (parts.length) return parts.join(" ").trim();
    return (u.username && "@" + u.username) || "";
  }

  /**
   * Normalize phone for Uzbekistan: digits only, ensure +998 prefix for local 9 digits.
   */
  function normalizePhoneUz(raw) {
    let s = String(raw || "").replace(/\D/g, "");
    if (s.startsWith("998") && s.length >= 12) return "+" + s.slice(0, 12);
    if (s.length === 9) return "+998" + s;
    if (s.startsWith("998") && s.length === 12) return "+" + s;
    const trimmed = String(raw || "").trim();
    return trimmed.startsWith("+") ? trimmed : "+" + s.replace(/^\+/, "");
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
      let msg = (data && (data.detail || data.error)) || res.statusText;
      if (typeof msg === "object") msg = JSON.stringify(msg);
      const err = new Error(msg);
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
        const tw = window.Telegram.WebApp;
        tw.ready();
        tw.expand();
        if (tw.setHeaderColor) tw.setHeaderColor("#f8fafc");
        if (tw.setBackgroundColor) tw.setBackgroundColor("#f8fafc");
      }
    } catch (e) {}
  }

  /** Light haptic on supported clients */
  function hapticLight() {
    try {
      if (window.Telegram && window.Telegram.WebApp && window.Telegram.WebApp.HapticFeedback) {
        window.Telegram.WebApp.HapticFeedback.impactOccurred("light");
      }
    } catch (e) {}
  }

  const api = {
    getInitData,
    getStartParam,
    getTelegramUser,
    getSuggestedName,
    escapeHtml,
    normalizePhoneUz,
    apiHeaders,
    apiFetch,
    showAlert,
    ready,
    hapticLight,
  };
  window.MiniApp = Object.assign({}, window.MiniApp || {}, api);
  if (typeof window.MiniApp.hapticLight !== "function") {
    window.MiniApp.hapticLight = hapticLight;
  }
})();
