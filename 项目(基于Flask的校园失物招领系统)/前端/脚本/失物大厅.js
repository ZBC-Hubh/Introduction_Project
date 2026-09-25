(function () {
  渲染导航("items");

  const 状态 = {
    type: null, category: null, keyword: "", page: 1, size: 12
  };
  const params = new URLSearchParams(location.search);
  if (params.get("category")) 状态.category = Number(params.get("category"));
  if (params.get("type")) 状态.type = Number(params.get("type"));

  let 是管理员 = false;
  let 批量模式 = false;
  const 已选择 = new Set();

  // 检查当前用户是否为管理员（老师）
  async function 检查权限() {
    if (API.isLogged()) {
      try {
        const u = await API.me();
        是管理员 = (u.身份 === "teacher");
      } catch (_) {}
    }
    if (是管理员) {
      document.getElementById("toggle-select").style.display = "inline-flex";
    }
  }

  function 渲染分类筛选() {
    const wrap = document.getElementById("filter-cat");
    if (!wrap) return;
    wrap.innerHTML = `<div class="chip ${状态.category == null ? "active" : ""}" data-v="">全部</div>` +
      Object.entries(CATEGORIES).map(([k, c]) =>
        `<div class="chip ${状态.category == k ? "active" : ""}" data-v="${k}">${c.label}</div>`
      ).join("");
    wrap.querySelectorAll(".chip").forEach(el => {
      el.addEventListener("click", () => {
        状态.category = el.dataset.v === "" ? null : Number(el.dataset.v);
        状态.page = 1;
        渲染分类筛选(); 加载列表();
      });
    });
  }
  function 渲染类型筛选() {
    const wrap = document.getElementById("filter-type");
    if (!wrap) return;
    const list = [
      { v: null, l: "全部" },
      { v: 0, l: "丢失" },
      { v: 1, l: "捡到" },
    ];
    wrap.innerHTML = list.map(t =>
      `<div class="chip ${状态.type == t.v ? "active" : ""}" data-v="${t.v == null ? "" : t.v}">${t.l}</div>`
    ).join("");
    wrap.querySelectorAll(".chip").forEach(el => {
      el.addEventListener("click", () => {
        状态.type = el.dataset.v === "" ? null : Number(el.dataset.v);
        状态.page = 1;
        渲染类型筛选(); 加载列表();
      });
    });
  }

  function 构建查询串() {
    const p = [];
    if (状态.type != null) p.push(`type=${状态.type}`);
    if (状态.category != null) p.push(`category=${状态.category}`);
    if (状态.keyword) p.push(`keyword=${encodeURIComponent(状态.keyword)}`);
    p.push(`page=${状态.page}`);
    p.push(`size=${状态.size}`);
    return p.join("&");
  }

  function 更新选择状态() {
    const n = 已选择.size;
    const batchBtn = document.getElementById("batch-delete");
    const allBtn = document.getElementById("select-all");
    if (批量模式 && 是管理员) {
      allBtn.style.display = "inline-flex";
      const list = window.__hallItems || [];
      const allSelected = list.length > 0 && list.every(it => 已选择.has(it.id));
      allBtn.textContent = allSelected ? "取消全选" : "全选";
      batchBtn.style.display = "inline-flex";
      batchBtn.textContent = n > 0 ? `🗑 一键删除(${n})` : "🗑 一键删除";
      batchBtn.disabled = n === 0;
      batchBtn.style.opacity = n === 0 ? "0.5" : "1";
    } else {
      batchBtn.style.display = "none";
      allBtn.style.display = "none";
      已选择.clear();
    }
  }

  async function 加载列表() {
    const box = document.getElementById("hall-grid");
    box.innerHTML = Array(状态.size).fill(0).map(() => `
      <div class="item-card"><div class="skeleton" style="height:170px"></div>
      <div class="item-body"><div class="skeleton" style="height:14px;margin-bottom:8px"></div>
      <div class="skeleton" style="height:12px;width:80%"></div></div></div>
    `).join("");
    try {
      const 数据 = await API.request("GET", `/api/items?${构建查询串()}`) || {};
      const list = 数据.list || [];
      window.__hallItems = list;
      document.getElementById("result-count").textContent = 数据.total || 0;
      if (!list.length) {
        box.innerHTML = `<div style="grid-column:1/-1;text-align:center;padding:40px;color:var(--muted)">
          暂无符合条件的物品<br><a href="/发布.html" class="btn btn-primary" style="margin-top:14px">去发布</a></div>`;
      } else {
        box.innerHTML = list.map(it => 管理员卡片(it)).join("");
        绑定卡片点击("#hall-grid");
        绑定删除按钮();
      }
      渲染分页(数据.total || 0);
    } catch (e) {
      box.innerHTML = `<div style="grid-column:1/-1;color:var(--danger)">加载失败：${escapeHtml(e.msg || "")}</div>`;
    }
  }

  function 管理员卡片(项) {
    const 类型 = TYPES[项.type] || TYPES[0];
    const img = 项.image_url
      ? `background-image: url('${项.image_url}');`
      : `background: ${占位背景(项.id)};`;
    const checked = 已选择.has(项.id) ? "checked" : "";
    let 右上角 = "";
    if (是管理员) {
      if (批量模式) {
        右上角 = `<label class="card-check" onclick="event.stopPropagation()"><input type="checkbox" class="row-check" data-id="${项.id}" ${checked}></label>`;
      } else {
        右上角 = `<button class="card-delete" data-del="${项.id}" title="删除此条">🗑</button>`;
      }
    }
    let 找回按钮 = "";
    if (是管理员 && 项.status !== 1 && 项.audit_status === 1 && !批量模式) {
      找回按钮 = `<button class="btn-found" data-found="${项.id}" onclick="event.stopPropagation()">✅ 已找到</button>`;
    }
    return `
    <div class="item-card ${checked ? "selected" : ""}" data-id="${项.id}">
      <div class="item-image" style="${img}">
        <span class="item-tag-row">
          <span class="tag ${类型.tag}">${类型.label}</span>
          <span class="tag">${项.category_label}</span>
        </span>
        ${项.status === 1 ? '<span class="tag" style="background:var(--forest);color:var(--cream)">已找回</span>' : ""}
        ${项.status === 1 ? '<div class="found-stamp">已找到</div>' : ""}
        ${右上角}
      </div>
      <div class="item-body">
        <div class="item-title">${escapeHtml(项.title)}</div>
        <div class="item-meta">
          <span class="loc">${escapeHtml(项.location || "未填写地点")}</span>
          <span class="time">${相对时间(项.created_at)}</span>
        </div>
        ${找回按钮}
      </div>
    </div>
  `;
  }

  function 绑定删除按钮() {
    const box = document.getElementById("hall-grid");
    // 已找到按钮
    box.querySelectorAll(".btn-found").forEach(btn => {
      btn.onclick = async (e) => {
        e.stopPropagation();
        const id = Number(btn.dataset.found);
        if (!confirm("确认标记为已找到？")) return;
        try {
          await API.request("POST", `/api/items/${id}/complete`, { auth: true });
          showToast("已标记为找到", "success");
          加载列表();
        } catch (err) {
          showToast(err.msg || "操作失败", "error");
        }
      };
    });
    // 单条删除
    box.querySelectorAll(".card-delete").forEach(btn => {
      btn.onclick = async (e) => {
        e.stopPropagation();
        const id = Number(btn.dataset.del);
        if (!confirm("确认删除此条发布？删除后无法恢复。")) return;
        try {
          await API.request("DELETE", `/api/items/${id}`, { auth: true });
          showToast("删除成功", "success");
          加载列表();
        } catch (err) {
          showToast(err.msg || "删除失败", "error");
        }
      };
    });
    // 批量选择
    box.querySelectorAll(".row-check").forEach(cb => {
      cb.onchange = (e) => {
        e.stopPropagation();
        const id = Number(cb.dataset.id);
        if (cb.checked) {
          已选择.add(id);
          cb.closest(".item-card").classList.add("selected");
        } else {
          已选择.delete(id);
          cb.closest(".item-card").classList.remove("selected");
        }
        更新选择状态();
      };
    });
    更新选择状态();
  }

  function 渲染分页(总数) {
    const wrap = document.getElementById("pagination");
    if (!wrap) return;
    const 总页 = Math.max(1, Math.ceil(总数 / 状态.size));
    let html = `<button class="page-btn" ${状态.page <= 1 ? "disabled" : ""} data-p="${状态.page - 1}">上一页</button>`;
    const 起始 = Math.max(1, 状态.page - 2);
    const 结束 = Math.min(总页, 起始 + 4);
    for (let i = 起始; i <= 结束; i++) {
      html += `<button class="page-btn ${i === 状态.page ? "active" : ""}" data-p="${i}">${i}</button>`;
    }
    html += `<button class="page-btn" ${状态.page >= 总页 ? "disabled" : ""} data-p="${状态.page + 1}">下一页</button>`;
    wrap.innerHTML = html;
    wrap.querySelectorAll(".page-btn").forEach(b => {
      b.addEventListener("click", () => {
        const p = Number(b.dataset.p);
        if (!b.disabled && p !== 状态.page) { 状态.page = p; 加载列表(); 渲染分页(总数); window.scrollTo({ top: 0, behavior: "smooth" }); }
      });
    });
  }

  // 事件
  document.getElementById("search-btn").addEventListener("click", () => {
    状态.keyword = document.getElementById("search-input").value.trim();
    状态.page = 1; 加载列表();
  });
  document.getElementById("search-input").addEventListener("keyup", e => {
    if (e.key === "Enter") {
      状态.keyword = document.getElementById("search-input").value.trim();
      状态.page = 1; 加载列表();
    }
  });

  // 批量选择切换
  document.getElementById("toggle-select").addEventListener("click", () => {
    批量模式 = !批量模式;
    const btn = document.getElementById("toggle-select");
    btn.textContent = 批量模式 ? "取消选择" : "批量选择";
    btn.classList.toggle("active", 批量模式);
    if (!批量模式) 已选择.clear();
    加载列表();
  });

  // 全选 / 取消全选
  document.getElementById("select-all").addEventListener("click", () => {
    const list = window.__hallItems || [];
    const allSelected = list.length > 0 && list.every(it => 已选择.has(it.id));
    if (allSelected) {
      已选择.clear();
      showToast("已取消全选");
    } else {
      list.forEach(it => 已选择.add(it.id));
      showToast(`已选择 ${list.length} 条`);
    }
    加载列表();
  });

  // 一键删除
  document.getElementById("batch-delete").addEventListener("click", async () => {
    if (已选择.size === 0) { showToast("请先选择要删除的物品", "error"); return; }
    if (!confirm(`确认删除选中的 ${已选择.size} 条发布？删除后无法恢复！`)) return;
    let 成功 = 0, 失败 = 0;
    for (const id of 已选择) {
      try {
        await API.request("DELETE", `/api/items/${id}`, { auth: true });
        成功++;
      } catch (_) { 失败++; }
    }
    showToast(`已删除 ${成功} 条${失败 > 0 ? `，${失败} 条失败` : ""}`, 成功 > 0 ? "success" : "error");
    批量模式 = false;
    已选择.clear();
    document.getElementById("toggle-select").textContent = "批量选择";
    document.getElementById("toggle-select").classList.remove("active");
    加载列表();
  });

  渲染分类筛选();
  渲染类型筛选();
  检查权限().then(() => 加载列表());
})();
