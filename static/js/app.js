/**
 * Telegram Mini App helpers — API, UX, safe DOM.
 * v2 — hapticLight + merge with stale cached MiniApp
 */
(function () {
  const API_BASE = "/api";
  const TOAST_LIFETIME_MS = 4200;
  const TOAST_ERROR_MS = 6800;
  const TOAST_WARNING_MS = 5600;
  const API_TIMEOUT_MS = 15000;
  let toastTimer = null;

  /** Inglizcha HTTP status matnlari (brauzer) uchun o‘zbekcha qisqa xabar */
  function _httpStatusUzMessage(status) {
    switch (status) {
      case 400:
        return "So‘rov noto‘g‘ri.";
      case 401:
        return "Kirish rad etildi.";
      case 403:
        return "Ruxsat yo‘q.";
      case 404:
        return "Topilmadi.";
      case 409:
        return "Ma’lumot mos kelmayapti (takroriy so‘rov).";
      case 429:
        return "Juda ko‘p so‘rov. Birozdan keyin urinib ko‘ring.";
      case 500:
      case 502:
      case 503:
      case 504:
        return "Serverda xatolik. Keyinroq urinib ko‘ring.";
      default:
        return "";
    }
  }

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

  /** Ko‘rinish: +998 XX XXX XX XX (faqat ko‘rsatish; yuborishda normalizePhoneUz). */
  function formatUzPhoneDisplay(raw) {
    let d = String(raw || "").replace(/\D/g, "");
    if (d.startsWith("998")) d = d.slice(3);
    else if (d.startsWith("0")) d = d.replace(/^0+/, "");
    if (d.length > 9) d = d.slice(0, 9);
    if (!d) return "";
    const parts = ["+998"];
    if (d.length >= 1) parts.push(d.slice(0, 2));
    if (d.length > 2) parts.push(d.slice(2, 5));
    if (d.length > 5) parts.push(d.slice(5, 7));
    if (d.length > 7) parts.push(d.slice(7, 9));
    return parts.join(" ").trim();
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
    const controller = new AbortController();
    const timer = setTimeout(function () {
      controller.abort();
    }, API_TIMEOUT_MS);
    let res;
    try {
      res = await fetch(
        API_BASE + path,
        Object.assign({}, opts, { headers, signal: controller.signal })
      );
    } catch (networkErr) {
      if (networkErr && networkErr.name === "AbortError") {
        const err = new Error(
          "So‘rov muddati tugadi. Internetni tekshirib qayta urinib ko‘ring."
        );
        err.status = 0;
        err.data = null;
        throw err;
      }
      const err = new Error("Ulanishda muammo. Internetni tekshirib qayta urinib ko‘ring.");
      err.status = 0;
      err.data = null;
      throw err;
    } finally {
      clearTimeout(timer);
    }
    const text = await res.text();
    let data = null;
    try {
      data = text ? JSON.parse(text) : null;
    } catch (e) {
      data = { detail: text };
    }
    if (!res.ok) {
      let msg = (data && (data.detail || data.error)) || res.statusText;
      if (data && typeof data === "object" && !msg) {
        const firstKey = Object.keys(data)[0];
        const v = firstKey ? data[firstKey] : null;
        if (Array.isArray(v) && v.length) msg = String(v[0]);
      }
      if (typeof msg === "object") msg = JSON.stringify(msg);
      if (
        !msg ||
        msg === res.statusText ||
        /^not found|bad request|forbidden|conflict|internal server error$/i.test(String(msg).trim())
      ) {
        msg = _httpStatusUzMessage(res.status) || msg;
      }
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

  function _ensureToastContainer() {
    let c = document.getElementById("app-toast");
    if (c) return c;
    c = document.createElement("div");
    c.id = "app-toast";
    c.className = "app-toast hidden";
    c.innerHTML =
      '<div class="app-toast-card">' +
      '<p id="app-toast-text" class="app-toast-text"></p>' +
      '<button type="button" id="app-toast-close" class="app-toast-close" aria-label="Yopish">Yopish</button>' +
      "</div>";
    document.body.appendChild(c);
    c.querySelector("#app-toast-close").addEventListener("click", function () {
      c.classList.add("hidden");
    });
    return c;
  }

  function showToast(message, type, durationMs) {
    const c = _ensureToastContainer();
    const t = c.querySelector("#app-toast-text");
    c.classList.remove("hidden", "app-toast-success", "app-toast-error", "app-toast-warning", "app-toast-info");
    const ty = type || "info";
    c.classList.add("app-toast-" + ty);
    t.textContent = String(message || "");
    if (toastTimer) clearTimeout(toastTimer);
    let ms = durationMs;
    if (ms == null) {
      if (ty === "error") ms = TOAST_ERROR_MS;
      else if (ty === "warning") ms = TOAST_WARNING_MS;
      else ms = TOAST_LIFETIME_MS;
    }
    toastTimer = setTimeout(function () {
      c.classList.add("hidden");
    }, ms);
  }

  function parseApiError(err, fallbackText) {
    const fallback = fallbackText || "Xatolik yuz berdi.";
    if (!err) return fallback;
    if (err.data && typeof err.data === "object") {
      const code = err.data.code;
      if (code === "payment_pending_exists") {
        return "To‘lov allaqachon yuborilgan — tasdiqlanishini kuting.";
      }
      if (code === "terms_required") {
        return typeof err.data.detail === "string" && err.data.detail
          ? err.data.detail
          : "Avval shartlarga rozilik bering.";
      }
      if (code === "product_limit_reached") {
        return typeof err.data.detail === "string" && err.data.detail
          ? err.data.detail
          : "Mahsulot limiti to‘ldi — obunani kengaytiring.";
      }
      if (typeof err.data.detail === "string" && err.data.detail) return err.data.detail;
      if (Array.isArray(err.data.detail) && err.data.detail.length) return String(err.data.detail[0]);
      const k = Object.keys(err.data)[0];
      if (k) {
        const v = err.data[k];
        if (Array.isArray(v) && v.length) return String(v[0]);
        if (typeof v === "string") return v;
      }
    }
    return err.message || fallback;
  }

  function back(fallbackUrl) {
    try {
      if (window.history.length > 1) {
        window.history.back();
        return;
      }
    } catch (e) {}
    window.location.href = fallbackUrl || "/webapp/";
  }

  function bindBackButton(btnId, fallbackUrl) {
    const btn = document.getElementById(btnId);
    if (!btn) return;
    btn.addEventListener("click", function () {
      back(fallbackUrl);
    });
  }

  /**
   * Mini App dizayni Tailwind bilan ochiq palitrada (bg-slate-50, qora matn, oq kartochkalar).
   * Telegram themeParams ni butun sahifaga qo‘llash qorong‘i fonda yorqin kartochkalarni buzadi
   * (kontrast yo‘qoladi). Shuning uchun faqat Telegram “header” fonini loyiha rangiga yaqin qilib qoldiramiz.
   */
  function ready() {
    try {
      if (window.Telegram && window.Telegram.WebApp) {
        const tw = window.Telegram.WebApp;
        tw.ready();
        tw.expand();
        var shell = "#f8fafc";
        if (tw.setHeaderColor) tw.setHeaderColor(shell);
        if (tw.setBackgroundColor) tw.setBackgroundColor(shell);
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
    formatUzPhoneDisplay,
    apiHeaders,
    apiFetch,
    showAlert,
    showToast,
    parseApiError,
    ready,
    hapticLight,
    back,
    bindBackButton,
  };
  window.MiniApp = Object.assign({}, window.MiniApp || {}, api);
  // Har doim to‘liq implementatsiya (stub yoki eski keshdan keyin ham to‘g‘ri ishlashi uchun).
  window.MiniApp.hapticLight = hapticLight;
})();
