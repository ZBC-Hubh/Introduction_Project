const CATEGORIES = {
  0: { label: "电子设备", icon: "💻", desc: "手机电脑等" },
  1: { label: "证件卡类", icon: "🪪", desc: "校园卡身份证等" },
  2: { label: "书籍文具", icon: "📚", desc: "课本笔记本等" },
  3: { label: "生活用品", icon: "🧴", desc: "雨伞水杯钥匙" },
  4: { label: "其他物品", icon: "🧩", desc: "其他分类" },
};
const TYPES = { 0: { label: "丢失", tag: "tag-lost" }, 1: { label: "捡到", tag: "tag-found" } };

/* 占位图背景（渐变色块，按物品 ID 选择） */
function 占位背景(id) {
  const list = [
    "linear-gradient(135deg, #2D5F4E 0%, #E8A87C 100%)",
    "linear-gradient(135deg, #C03A2B 0%, #E8A87C 100%)",
    "linear-gradient(135deg, #1F4438 0%, #4F8A6A 100%)",
    "linear-gradient(135deg, #FF8C42 0%, #2D5F4E 100%)",
    "linear-gradient(135deg, #6E6A63 0%, #E8A87C 100%)",
  ];
  return list[Number(id || 0) % list.length];
}

/* 相对时间格式化 */
function 相对时间(str) {
  if (!str) return "";
  const t = new Date(str.replace(/-/g, "/")).getTime();
  const diff = Date.now() - t;
  const min = Math.floor(diff / 60000);
  if (min < 1) return "刚刚";
  if (min < 60) return `${min} 分钟前`;
  const h = Math.floor(min / 60);
  if (h < 24) return `${h} 小时前`;
  const d = Math.floor(h / 24);
  if (d < 30) return `${d} 天前`;
  return str.split(" ")[0];
}

/* 渲染顶部导航（供所有页面调用） */
function 渲染导航(当前页) {
  const 根 = document.getElementById("topbar-slot");
  if (!根) return;
  const token = API.getToken();
  const 已登录 = !!token;

  let links = [
    { key: "home", href: "/失物大厅.html", label: "失物大厅" },
    { key: "post", href: "/发布.html", label: "我要发布" },
    { key: "profile", href: "/个人中心.html", label: "个人中心" },
  ];
  if (已登录) {
    // 从 JWT 中解析身份（不请求 /me，减轻开销）
    try {
      const payload = JSON.parse(atob(token.split(".")[1]));
      if (payload["身份"] === "teacher") {
        links.push({ key: "admin", href: "/后台管理.html", label: "后台管理" });
      }
    } catch (_) {}
  }

  根.innerHTML = `
    <div class="topbar">
      <div class="topbar-inner">
        <div style="display:flex;align-items:center;gap:10px">
          ${当前页 !== "home" ? `<button class="back-btn" onclick="history.length>1?history.back():location.href='/失物大厅.html'">← 返回</button>` : ""}
          <div class="brand" onclick="location.href='/失物大厅.html'">
            <div class="brand-mini">寻</div>
            <div class="brand-title">校园失物招领</div>
          </div>
        </div>
        <nav class="nav-links">
          ${links.map(l => `<a class="nav-link ${l.key === 当前页 ? "active" : ""}" href="${l.href}">${l.label}</a>`).join("")}
        </nav>
        <div class="nav-user" id="nav-user">
          ${已登录 ? `
            <div class="nav-avatar" id="nav-avatar">?</div>
            <a class="nav-link" href="/个人中心.html">我的</a>
            <a class="nav-link" href="javascript:API.logout()">退出</a>
          ` : `
            <a class="nav-btn" href="/登录注册.html">登录注册</a>
          `}
        </div>
      </div>
    </div>
  `;

  if (已登录) {
    API.me().then(u => {
      const av = document.getElementById("nav-avatar");
      if (av && u && u.name) av.textContent = u.name[0];
    }).catch(() => {});
  }
}

/* 渲染物品卡片 */
function 物品卡片(项) {
  const 类型 = TYPES[项.type] || TYPES[0];
  const img = 项.image_url
    ? `background-image: url('${项.image_url}');`
    : `background: ${占位背景(项.id)};`;
  return `
    <div class="item-card" data-id="${项.id}">
      <div class="item-image" style="${img}">
        <span class="item-tag-row">
          <span class="tag ${类型.tag}">${类型.label}</span>
          <span class="tag">${项.category_label}</span>
        </span>
        ${项.status === 1 ? '<span class="tag" style="background:var(--forest);color:var(--cream)">已找回</span>' : ""}
        ${项.status === 1 ? '<div class="found-stamp">已找到</div>' : ""}
      </div>
      <div class="item-body">
        <div class="item-title">${escapeHtml(项.title)}</div>
        <div class="item-meta">
          <span class="loc">${escapeHtml(项.location || "未填写地点")}</span>
          <span class="time">${相对时间(项.created_at)}</span>
        </div>
      </div>
    </div>
  `;
}

function escapeHtml(s) {
  return String(s == null ? "" : s)
    .replaceAll("&", "&amp;").replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;").replaceAll('"', "&quot;").replaceAll("'", "&#39;");
}

/* 点击卡片跳转详情 */
function 绑定卡片点击(容器选择器) {
  const wrap = document.querySelector(容器选择器);
  if (!wrap) return;
  wrap.addEventListener("click", (e) => {
    const c = e.target.closest(".item-card");
    if (c) location.href = `/详情.html?id=${c.dataset.id}`;
  });
}

function showToast(msg, type = "") {
  let el = document.getElementById("toast");
  if (!el) {
    el = document.createElement("div");
    el.id = "toast";
    el.className = "toast";
    document.body.appendChild(el);
  }
  el.textContent = msg;
  el.className = "toast show " + (type === "success" ? "success" : type === "error" ? "error" : "");
  el.style.opacity = "1";
  el.style.transform = "translateX(-50%) translateY(0)";
  clearTimeout(showToast._t);
  showToast._t = setTimeout(() => {
    el.style.opacity = "0";
  }, 2200);
}
window.showToast = showToast;
