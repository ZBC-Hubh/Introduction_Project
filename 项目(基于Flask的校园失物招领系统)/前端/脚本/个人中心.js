(function () {
  渲染导航("profile");

  if (!API.isLogged()) {
    setTimeout(() => {
      showToast("请先登录", "error");
      location.href = "/登录注册.html";
    }, 300);
    return;
  }

  let 批量模式 = false;
  const 已选择 = new Set();

  async function 加载() {
    // 先加载用户信息
    try {
      const u = await API.me();
      window.__me = u;
    } catch (_) {
      window.__me = null;
    }

    // 再加载物品列表
    try {
      const list = await API.request("GET", "/api/items/mine", { auth: true });
      渲染我的(list || []);
      // 物品加载完后再填充用户信息（此时统计数据可用）
      if (window.__me) 填充用户(window.__me);
    } catch (e) {
      document.getElementById("mine-grid").innerHTML =
        `<p style="grid-column:1/-1;color:var(--danger)">加载失败：${escapeHtml(e.msg || "")}</p>`;
      // 即使物品加载失败也尝试填充用户信息
      if (window.__me) 填充用户(window.__me);
    }
  }

  function 填充用户(u) {
    // u 直接就是后端返回的用户信息对象
    // 字段：id, 身份, 编号, email, name, phone, department/class_name, created_at
    const name = u.name || "用户";
    const 身份 = u.身份 || "student";
    const 编号 = u.编号 || "--";
    const 身份标签 = 身份 === "teacher" ? "老师用户" : "学生用户";

    document.getElementById("avatar").textContent = name[0];
    document.getElementById("p-name").textContent = name;
    document.getElementById("p-role").textContent = 身份标签;
    document.getElementById("p-id").textContent = 编号;
    document.getElementById("p-phone").textContent = u.phone || "未填写";
    document.getElementById("p-created").textContent = String(u.created_at || "").split(" ")[0] || "--";

    // 统计（从我的发布中推算）
    const items = window.__myItems || [];
    const total = items.length;
    const recovered = items.filter(i => i.status === 1).length;
    const pending = items.filter(i => i.audit_status === 0).length;
    const reviewed = items.filter(i => i.audit_status === 1).length;
    const map = { total, recovered, pending, reviewed };
    document.querySelectorAll(".profile-stat-card").forEach(card => {
      const k = card.dataset.k;
      if (map[k] != null) card.querySelector(".n").textContent = map[k];
    });
  }

  function 更新选择状态() {
    const n = 已选择.size;
    const batchBtn = document.getElementById("batch-delete");
    const allBtn = document.getElementById("select-all");
    if (批量模式) {
      allBtn.style.display = "inline-flex";
      const list = window.__myItems || [];
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

  function 渲染我的(list) {
    window.__myItems = list;
    const box = document.getElementById("mine-grid");
    if (!list.length) {
      box.innerHTML = `<div style="grid-column:1/-1;text-align:center;padding:40px;color:var(--muted)">
        您还没有发布任何信息<br>
        <a href="/发布.html" class="btn btn-primary" style="margin-top:14px">现在去发布</a></div>`;
      return;
    }
    box.innerHTML = list.map(it => {
      const 类型 = TYPES[it.type] || TYPES[0];
      const 审核 = ["<span class='tag'>审核中</span>", "<span class='tag tag-done'>审核通过</span>", "<span class='tag tag-lost'>已拒绝</span>"][it.audit_status] || "";
      const img = it.image_url
        ? `background-image: url('${it.image_url}');`
        : `background: ${占位背景(it.id)};`;
      const checked = 已选择.has(it.id) ? "checked" : "";
      const 找回按钮 = (it.status !== 1 && it.audit_status === 1 && !批量模式)
        ? `<button class="btn-found" data-found="${it.id}" onclick="event.stopPropagation()">✅ 已找到</button>` : "";
      return `
      <div class="item-card ${checked ? "selected" : ""}" data-id="${it.id}">
        <div class="item-image" style="${img}">
          <span class="item-tag-row">
            <span class="tag ${类型.tag}">${类型.label}</span>
            ${审核}
            ${it.status === 1 ? '<span class="tag tag-done">已找回</span>' : ""}
          </span>
          ${it.status === 1 ? '<div class="found-stamp">已找到</div>' : ""}
          ${批量模式 ? `<label class="card-check" onclick="event.stopPropagation()"><input type="checkbox" class="row-check" data-id="${it.id}" ${checked}></label>` : `<button class="card-delete" data-del="${it.id}" title="删除此条">🗑</button>`}
        </div>
        <div class="item-body">
          <div class="item-title">${escapeHtml(it.title)}</div>
          <div class="item-meta">
            <span class="loc">${escapeHtml(it.location || "--")}</span>
            <span class="time">${相对时间(it.created_at)}</span>
          </div>
          ${it.audit_status === 2 && it.audit_feedback
            ? `<div style="margin-top:8px;padding:8px;background:rgba(192,58,43,0.08);color:var(--danger);font-size:12px;border-radius:6px">
              审核拒绝：${escapeHtml(it.audit_feedback)}</div>` : ""}
          ${找回按钮}
        </div>
      </div>`;
    }).join("");
    绑定卡片点击("#mine-grid");

    // 绑定已找到按钮
    box.querySelectorAll(".btn-found").forEach(btn => {
      btn.onclick = async (e) => {
        e.stopPropagation();
        const id = Number(btn.dataset.found);
        if (!confirm("确认标记为已找到？")) return;
        try {
          await API.request("POST", `/api/items/${id}/complete`, { auth: true });
          showToast("已标记为找到", "success");
          加载();
        } catch (err) {
          showToast(err.msg || "操作失败", "error");
        }
      };
    });

    // 绑定删除按钮（单条）
    box.querySelectorAll(".card-delete").forEach(btn => {
      btn.onclick = async (e) => {
        e.stopPropagation();
        const id = Number(btn.dataset.del);
        if (!confirm("确认删除此条发布？删除后无法恢复。")) return;
        try {
          await API.request("DELETE", `/api/items/${id}`, { auth: true });
          showToast("删除成功", "success");
          加载();
        } catch (err) {
          showToast(err.msg || "删除失败", "error");
        }
      };
    });

    // 绑定批量选择复选框
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
    if (window.__me) 填充用户(window.__me);
  }

  // 批量选择切换
  document.getElementById("toggle-select").addEventListener("click", () => {
    批量模式 = !批量模式;
    const btn = document.getElementById("toggle-select");
    btn.textContent = 批量模式 ? "取消选择" : "批量选择";
    btn.classList.toggle("active", 批量模式);
    if (!批量模式) 已选择.clear();
    渲染我的(window.__myItems || []);
  });

  // 全选 / 取消全选
  document.getElementById("select-all").addEventListener("click", () => {
    const list = window.__myItems || [];
    const allSelected = list.length > 0 && list.every(it => 已选择.has(it.id));
    if (allSelected) {
      已选择.clear();
      showToast("已取消全选");
    } else {
      list.forEach(it => 已选择.add(it.id));
      showToast(`已选择 ${list.length} 条`);
    }
    渲染我的(window.__myItems || []);
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
    加载();
  });

  加载();
})();
