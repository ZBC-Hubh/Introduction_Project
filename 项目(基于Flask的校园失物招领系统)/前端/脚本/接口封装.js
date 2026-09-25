const API = (function () {
  const BASE = "";
  const TOKEN_KEY = "campus_lf_token";

  function getToken() {
    return localStorage.getItem(TOKEN_KEY) || "";
  }

  function setToken(token) {
    if (token) localStorage.setItem(TOKEN_KEY, token);
    else localStorage.removeItem(TOKEN_KEY);
  }

  async function request(method, path, { body, auth = false, params } = {}) {
    const headers = { "Content-Type": "application/json" };
    if (auth && getToken()) headers["Authorization"] = "Bearer " + getToken();

    const opts = { method, headers, credentials: "include" };
    if (body !== undefined) opts.body = JSON.stringify(body);

    // 构建带查询参数的URL
    let url = BASE + path;
    if (params && typeof params === "object") {
      const qs = new URLSearchParams();
      for (const [k, v] of Object.entries(params)) {
        if (v !== undefined && v !== null) qs.append(k, v);
      }
      const qsStr = qs.toString();
      if (qsStr) url += (url.includes("?") ? "&" : "?") + qsStr;
    }

    let resp;
    try {
      resp = await fetch(url, opts);
    } catch (e) {
      throw { msg: "网络异常：" + e.message };
    }
    let data = null;
    try { data = await resp.json(); } catch (e) { /* ignore */ }
    if (!resp.ok || (data && data.code && data.code !== 0)) {
      // token 过期或无效
      if (resp.status === 401 && getToken()) {
        setToken("");
        if (typeof showToast === "function") {
          showToast("账号已在其他设备登录，请重新登录", "error");
        }
        setTimeout(() => location.href = "/登录注册.html", 1500);
      }
      throw { msg: (data && data.msg) || ("HTTP " + resp.status), status: resp.status, data };
    }
    return data.data;
  }

  return {
    getToken,
    setToken,
    request,

    // 健康检查
    health: () => request("GET", "/api/health"),

    // 认证
    register: (payload) => request("POST", "/api/auth/register", { body: payload }),
    login: (payload) => request("POST", "/api/auth/login", { body: payload }),
    me: () => request("GET", "/api/auth/me", { auth: true }),

    // 退出
    logout() {
      setToken("");
      location.href = "/登录注册.html";
    },

    // 是否已登录
    isLogged() { return !!getToken(); },
  };
})();
