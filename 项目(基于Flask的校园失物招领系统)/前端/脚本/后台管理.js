(function () {
  渲染导航("admin");

  // 权限检查
  API.me().then(u => {
    const role = u?.["身份"] || u?.role || u?.token_user?.["身份"];
    if (role !== "teacher") {
      document.body.innerHTML =
        `<div style="padding:80px;text-align:center">
          <h2 style="font-size:24px;margin-bottom:14px">无权限访问</h2>
          <p style="color:var(--muted);margin-bottom:20px">后台管理仅老师端账号可用，请切换身份登录。</p>
          <a class="btn btn-primary" href="/登录注册.html">去登录</a>
          <a class="btn btn-ghost" href="/失物大厅.html" style="margin-left:8px">返回大厅</a>
        </div>`;
    }
  }).catch((e) => {
    // 检查是否有token
    if (API.isLogged()) {
      // 有token但API调用失败，显示错误信息而不是直接跳转
      document.body.innerHTML =
        `<div style="padding:80px;text-align:center">
          <h2 style="font-size:24px;margin-bottom:14px">⚠️ 验证失败</h2>
          <p style="color:var(--muted);margin-bottom:20px">${escapeHtml((e && e.msg) || '身份验证失败，请重新登录')}</p>
          <a class="btn btn-primary" href="/登录注册.html">重新登录</a>
          <a class="btn btn-ghost" href="/失物大厅.html" style="margin-left:8px">返回大厅</a>
        </div>`;
    } else {
      setTimeout(() => location.href = "/登录注册.html", 300);
    }
  });

  const tabs = document.querySelectorAll(".admin-tab");
  function 切换面板(k) {
    tabs.forEach(t => t.classList.toggle("active", t.dataset.k === k));
    document.querySelectorAll(".admin-panel").forEach(p => p.classList.toggle("active", p.dataset.k === k));
  }
  tabs.forEach(t => t.addEventListener("click", () => 切换面板(t.dataset.k)));

  /* ==== 统计面板 ==== */
  async function 加载统计() {
    try {
      const s = await API.request("GET", "/api/admin/stats", { auth: true });
      const 总数 = Math.max(1, s.total_items || 0);
      document.getElementById("stat-total").textContent = s.total_items || 0;
      document.getElementById("stat-recovered").textContent = s.total_recovered || 0;
      document.getElementById("stat-pending").textContent = s.pending_audit || 0;
      document.getElementById("stat-users").textContent = (s.students || 0) + (s.teachers || 0);

      document.querySelector("#stat-total-card .fill").style.width = "100%";
      document.querySelector("#stat-recovered-card .fill").style.width =
        `${Math.round((s.total_recovered || 0) / 总数 * 100)}%`;
      document.querySelector("#stat-pending-card .fill").style.width =
        `${Math.min(100, Math.round((s.pending_audit || 0) / 总数 * 100))}%`;
      document.querySelector("#stat-users-card .fill").style.width = "100%";

      // 分类柱状图 - s.category_distribution 现在是 {0: count, 1: count, ...}
      const 分类 = s.category_distribution || {};
      const 分类最大值 = Math.max(1, ...Object.keys(CATEGORIES).map(k => 分类[k] || 0));
      document.querySelectorAll(".bar-item").forEach((el, i) => {
        const v = 分类[i] || 0;
        const h = (v / 分类最大值) * 100;
        el.querySelector(".bar").style.height = `${h}%`;
        el.querySelector(".bar .val").textContent = v;
        el.querySelector(".bar-label").textContent = CATEGORIES[i].label;
      });

      // 环形图
      const lost = s.total_lost || 0;
      const found = s.total_found || 0;
      const all = Math.max(1, lost + found);
      const pct = Math.round(lost / all * 100);
      const donut = document.querySelector(".donut");
      donut.style.setProperty("--lost-pct", pct + "%");
      donut.querySelector(".num").textContent = all;
      document.getElementById("legend-lost").querySelector(".n").textContent = lost;
      document.getElementById("legend-found").querySelector(".n").textContent = found;

      // 用户比例
      document.getElementById("stat-stu").textContent = s.students || 0;
      document.getElementById("stat-tea").textContent = s.teachers || 0;
    } catch (e) {
      console.error("加载统计失败", e);
    }
  }

  /* ==== 审核面板 ==== */
  let 待审数据 = [];
  const 已选择 = new Set();

  function 切换全选() {
    const 全选 = document.getElementById("select-all");
    已选择.clear();
    if (全选.checked) {
      待审数据.forEach(it => 已选择.add(it.id));
    }
    更新选择状态();
    渲染待审表格();
  }

  function 更新选择状态() {
    const n = 已选择.size;
    document.getElementById("selected-count").textContent = n > 0 ? `已选 ${n} 项` : "未选择";
    document.getElementById("batch-pass").disabled = n === 0;
    document.getElementById("batch-reject").disabled = n === 0;
  }

  async function 加载待审() {
    const box = document.getElementById("pending-body");
    box.innerHTML = `<tr><td colspan="7" style="padding:40px;text-align:center;color:var(--muted)">加载中...</td></tr>`;
    try {
      const data = await API.request("GET", "/api/admin/items/pending", { auth: true });
      待审数据 = data.list || [];
      已选择.clear();
      document.getElementById("select-all").checked = false;
      更新选择状态();
      if (!待审数据.length) {
        box.innerHTML = `<tr><td colspan="7" style="padding:40px;text-align:center;color:var(--muted)">
          🎉 全部处理完成，暂无待审核物品</td></tr>`;
        return;
      }
      渲染待审表格();
    } catch (e) {
      box.innerHTML = `<tr><td colspan="7" style="padding:30px;text-align:center;color:var(--danger)">
        ${escapeHtml(e.msg || "加载失败")}</td></tr>`;
    }
  }

  function 渲染待审表格() {
    const box = document.getElementById("pending-body");
    if (!待审数据.length) {
      box.innerHTML = `<tr><td colspan="7" style="padding:40px;text-align:center;color:var(--muted)">
        🎉 全部处理完成，暂无待审核物品</td></tr>`;
      return;
    }
    box.innerHTML = 待审数据.map(it => {
      const checked = 已选择.has(it.id) ? "checked" : "";
      return `
      <tr data-id="${it.id}">
        <td style="width:36px;text-align:center"><input type="checkbox" class="row-check" ${checked}></td>
        <td class="td-title">${escapeHtml(it.title)}</td>
        <td>
          <span class="tag ${it.type === 0 ? "tag-lost" : "tag-found"}">
            ${it.type === 0 ? "丢失" : "捡到"}
          </span>
          <span class="tag">${CATEGORIES[it.category]?.label || "其他"}</span>
        </td>
        <td>${escapeHtml(it.publisher?.name || "--")}
          <span style="font-size:11px;color:var(--muted)">
            (${it.user_type === 1 ? "老师" : "学生"})
          </span>
        </td>
        <td style="font-size:12px;color:var(--muted)">${相对时间(it.created_at)}</td>
        <td style="max-width:260px;color:var(--muted);font-size:13px;
          overflow:hidden;text-overflow:ellipsis;white-space:nowrap"
            title="${escapeHtml(it.description || "")}">${escapeHtml(it.description || "--")}</td>
        <td>
          <div class="actions-row">
            <button class="btn-detail" data-act="detail">详情</button>
            <button class="btn-pass" data-act="pass">通过</button>
            <button class="btn-reject" data-act="reject">拒绝</button>
          </div>
        </td>
      </tr>`;
    }).join("");

    // 绑定复选框
    box.querySelectorAll(".row-check").forEach(cb => {
      cb.addEventListener("change", () => {
        const id = Number(cb.closest("tr").dataset.id);
        if (cb.checked) 已选择.add(id);
        else 已选择.delete(id);
        更新选择状态();
      });
    });

    // 绑定按钮
    box.querySelectorAll("tr").forEach(tr => {
      const id = Number(tr.dataset.id);
      tr.querySelector(".td-title").onclick = () =>
        window.open(`/详情.html?id=${id}`, "_blank");
      tr.querySelectorAll("button").forEach(btn => {
        btn.onclick = () => {
          const act = btn.dataset.act;
          if (act === "detail") { window.open(`/详情.html?id=${id}`, "_blank"); return; }
          let feedback = "";
          if (act === "reject") {
            feedback = prompt("请输入拒绝原因：", "信息不清晰 / 不完整 / 违反规定");
            if (!feedback) return;
          }
          API.request("POST", `/api/admin/items/${id}/audit`,
            { body: { pass: act === "pass", feedback }, auth: true })
            .then(() => {
              showToast(act === "pass" ? "✅ 审核通过成功" : "❌ 审核拒绝成功", "success");
              加载待审();
            })
            .catch(e => showToast(e.msg || "处理失败", "error"));
        };
      });
    });
  }

  // 全选/反选
  document.getElementById("select-all").addEventListener("change", 切换全选);

  // 一键通过
  document.getElementById("batch-pass").addEventListener("click", () => {
    if (已选择.size === 0) { showToast("请先选择物品", "error"); return; }
    if (!confirm(`确认批量通过 ${已选择.size} 条待审核物品？`)) return;
    API.request("POST", "/api/admin/items/batch-audit", {
      body: { ids: Array.from(已选择), pass: true }, auth: true
    }).then(r => { showToast(`✅ 批量通过 ${已选择.size} 条成功`, "success"); 加载待审(); })
      .catch(e => showToast(e.msg || "批量操作失败", "error"));
  });

  // 一键拒绝
  document.getElementById("batch-reject").addEventListener("click", () => {
    if (已选择.size === 0) { showToast("请先选择物品", "error"); return; }
    const feedback = prompt("请输入批量拒绝原因：", "信息不清晰 / 不完整 / 违反规定");
    if (!feedback) return;
    API.request("POST", "/api/admin/items/batch-audit", {
      body: { ids: Array.from(已选择), pass: false, feedback }, auth: true
    }).then(r => { showToast(`❌ 批量拒绝 ${已选择.size} 条成功`, "success"); 加载待审(); })
      .catch(e => showToast(e.msg || "批量操作失败", "error"));
  });

  /* ==== 用户面板 ==== */
  async function 加载用户() {
    const box = document.getElementById("user-grid");
    box.innerHTML = '<p style="color:var(--muted);grid-column:1/-1;text-align:center;padding:30px">加载中...</p>';
    try {
      const d = await API.request("GET", "/api/admin/users", { auth: true });
      const list = (d && Array.isArray(d.list)) ? d.list : (Array.isArray(d) ? d : []);
      if (!list.length) {
        box.innerHTML = '<p style="color:var(--muted);grid-column:1/-1;text-align:center;padding:40px">暂无注册用户</p>';
        return;
      }
      box.innerHTML = list.map(u => `
        <div class="user-card">
          <div class="user-avatar">${u.name ? u.name[0] : "?"}</div>
          <div class="user-info">
            <div class="name">${escapeHtml(u.name)}
              <span style="color:var(--muted);font-size:12px;font-weight:normal">
                · ${escapeHtml(u.code || "--")}
              </span>
            </div>
            <div class="meta">
              ${escapeHtml(u.phone || "未填手机号")}
              <br>
              加入于 ${相对时间(u.created_at)} · 发布 ${u.items || 0} 条
            </div>
          </div>
          <span class="user-role ${u.role}">${u.role === "teacher" ? "老师" : "学生"}</span>
        </div>
      `).join("");
    } catch (e) {
      box.innerHTML = `<p style="color:var(--danger);grid-column:1/-1;text-align:center;padding:30px">加载失败：${escapeHtml(e.msg || "")}</p>`;
    }
  }

  /* ==== 公告面板 ==== */
  async function 加载公告() {
    try {
      const list = await API.request("GET", "/api/admin/announcements", { auth: true }) || [];
      const box = document.getElementById("ann-list");
      if (!list.length) {
        box.innerHTML = '<p style="color:var(--muted);padding:14px 0">暂无公告</p>';
        return;
      }
      box.innerHTML = list.map(n => `
        <div class="ann-item">
          <div>
            <div class="t">${escapeHtml(n.title)}</div>
            <div class="c">${escapeHtml(n.content)}</div>
            <div class="m">${n.publisher || "管理员"} · ${相对时间(n.created_at)}</div>
          </div>
        </div>
      `).join("");
    } catch (_) {}
  }

  document.getElementById("ann-form").addEventListener("submit", async e => {
    e.preventDefault();
    const body = {
      title: document.getElementById("ann-title").value.trim(),
      content: document.getElementById("ann-content").value.trim(),
    };
    if (!body.title || !body.content) { showToast("标题和内容都要填", "error"); return; }
    try {
      await API.request("POST", "/api/admin/announcements", { body, auth: true });
      showToast("公告发布成功", "success");
      document.getElementById("ann-form").reset();
      加载公告();
    } catch (e) {
      showToast(e.msg || "发布失败", "error");
    }
  });

  // 懒加载
  const 已加载 = {};
  tabs.forEach(t => t.addEventListener("click", () => {
    const k = t.dataset.k;
    if (已加载[k]) return;
    已加载[k] = true;
    if (k === "audit") 加载待审();
    else if (k === "users") 加载用户();
    else if (k === "announcement") 加载公告();
  }));

  // 审核面板的批量按钮也需要首次加载
  已加载.dashboard = true;
  已加载.audit = true; // 提前标记，下面立即加载

  加载统计();
  加载待审();
})();
