(function () {
  渲染导航("items");

  const ID = new URLSearchParams(location.search).get("id");
  if (!ID) {
    document.querySelector(".page").innerHTML =
      '<div style="padding:60px;text-align:center;color:var(--muted)">参数错误，<a href="/失物大厅.html">返回大厅</a></div>';
    return;
  }

  // 存储物品数据，供聊天使用
  window.__itemData = null;

  function 填充(数据) {
    window.__itemData = 数据;
    const 类型 = TYPES[数据.type] || TYPES[0];
    document.getElementById("detail-title").textContent = 数据.title;

    const tags = [
      `<span class="tag ${类型.tag}">${类型.label}</span>`,
      `<span class="tag">${CATEGORIES[数据.category]?.label || "其他"}</span>`,
    ];
    if (数据.status === 1) tags.push('<span class="tag tag-done">已找回</span>');
    if (数据.audit_status !== 1) tags.push('<span class="tag">审核中</span>');
    document.getElementById("detail-tags").innerHTML = tags.join("");

    const box = document.getElementById("detail-image");
    if (数据.image_url) {
      box.style.backgroundImage = `url('${数据.image_url}')`;
      box.innerHTML = 数据.status === 1 ? '<div class="found-stamp">已找到</div>' : "";
    } else {
      box.style.background = 占位背景(数据.id);
      box.textContent = "";
      const label = CATEGORIES[数据.category]?.label || "校园失物招领";
      box.innerHTML = `<span style="font-size:18px;font-family:var(--font-display)">${label}</span>` +
        (数据.status === 1 ? '<div class="found-stamp">已找到</div>' : "");
    }

    document.getElementById("detail-desc").textContent = 数据.description || "（发布者未填写详细描述）";
    document.getElementById("row-loc").textContent = 数据.location || "未填写";
    document.getElementById("row-time").textContent = 相对时间(数据.created_at);
    document.getElementById("row-views").textContent = 数据.view_count || 0;
    document.getElementById("row-publisher").textContent =
      `${数据.publisher?.name || "匿名用户"}${数据.publisher?.type === "teacher" ? "（老师）" : "（学生）"}`;
    const c = 数据.publisher?.contact;
    document.getElementById("row-contact").textContent = c ? c : "请通过留言区与发布者沟通";

    // 操作按钮
    const 我是发布者 = API.isLogged() && 数据.publisher &&
      window.__me &&
      String(window.__me.id) === String(数据.publisher.id) &&
      window.__me.身份 === 数据.publisher.type;
    const 是管理员 = API.isLogged() && window.__me && window.__me.身份 === "teacher";

    const btns = document.getElementById("detail-actions");
    let html = "";
    if (数据.status !== 1 && (我是发布者 || 是管理员) && 数据.audit_status === 1) {
      html += `<button class="btn btn-primary" id="btn-complete">✅ 已找到</button>`;
    }
    if (数据.status !== 1 && 我是发布者 && 数据.audit_status === 0) {
      html += `<button class="btn btn-primary" disabled title="审核通过后可标记">✅ 已找到（审核中）</button>`;
    }
    if (我是发布者) {
      html += `<button class="btn btn-danger" id="btn-delete" style="background:var(--danger);color:#fff;border:1px solid var(--danger)">🗑 删除发布</button>`;
    }
    if (数据.status !== 1 && !我是发布者 && 数据.publisher) {
      html += `<button class="btn btn-primary" id="btn-chat">💬 和发布者私聊</button>`;
    }
    html += `<button class="btn btn-ghost" id="btn-copy">复制详情页链接</button>`;
    btns.innerHTML = html;

    const bc = document.getElementById("btn-copy");
    if (bc) bc.onclick = async () => {
      try {
        await navigator.clipboard.writeText(location.href);
        showToast("链接已复制", "success");
      } catch { showToast("复制失败", "error"); }
    };

    const bc2 = document.getElementById("btn-complete");
    if (bc2) bc2.onclick = async () => {
      if (!confirm("确认标记为已找回？")) return;
      try {
        await API.request("POST", `/api/items/${ID}/complete`, { auth: true });
        showToast("已标记为找回", "success");
        setTimeout(() => location.reload(), 600);
      } catch (e) { showToast(e.msg || "操作失败", "error"); }
    };

    const bd = document.getElementById("btn-delete");
    if (bd) bd.onclick = async () => {
      if (!confirm("确认删除此条发布？删除后无法恢复！")) return;
      try {
        await API.request("DELETE", `/api/items/${ID}`, { auth: true });
        showToast("删除成功", "success");
        setTimeout(() => location.href = "/个人中心.html", 600);
      } catch (e) { showToast(e.msg || "删除失败", "error"); }
    };

    const bc3 = document.getElementById("btn-chat");
    if (bc3) bc3.onclick = () => {
      if (!API.isLogged()) {
        showToast("请先登录", "error");
        setTimeout(() => location.href = "/登录注册.html", 1000);
        return;
      }
      打开聊天窗口(数据.publisher);
    };
  }

  let 聊天窗口 = null;
  let 聊天对方 = null;
  let 聊天已加载 = false;

  function 打开聊天窗口(对方信息) {
    聊天对方 = 对方信息;
    if (!聊天窗口) {
      创建聊天窗口();
    }
    const overlay = document.getElementById("chat-overlay");
    overlay.classList.add("show");
    document.getElementById("chat-other-name").textContent =
      `${对方信息.name || "用户"}（${对方信息.type === "teacher" ? "老师" : "学生"}）`;
    加载聊天记录();
  }

  function 关闭聊天窗口() {
    const overlay = document.getElementById("chat-overlay");
    overlay.classList.remove("show");
  }

  function 创建聊天窗口() {
    const html = `
      <div id="chat-overlay" class="chat-overlay">
        <div class="chat-panel">
          <div class="chat-header">
            <div class="chat-title" id="chat-other-name">用户</div>
            <button class="chat-close" id="chat-close">✕</button>
          </div>
          <div class="chat-body" id="chat-body">
            <div class="chat-loading">加载中...</div>
          </div>
          <div class="chat-input-area">
            <textarea id="chat-input" placeholder="输入消息..."></textarea>
            <button id="chat-send" class="btn btn-primary">发送</button>
          </div>
        </div>
      </div>
    `;
    document.body.insertAdjacentHTML("beforeend", html);
    聊天窗口 = document.getElementById("chat-overlay");

    document.getElementById("chat-close").onclick = 关闭聊天窗口;
    聊天窗口.onclick = (e) => { if (e.target === 聊天窗口) 关闭聊天窗口(); };

    const input = document.getElementById("chat-input");
    input.addEventListener("keydown", (e) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        发送消息();
      }
    });

    document.getElementById("chat-send").onclick = 发送消息;
  }

  async function 加载聊天记录() {
    const body = document.getElementById("chat-body");
    body.innerHTML = '<div class="chat-loading">加载中...</div>';
    try {
      const 数据 = await API.request("GET", "/api/messages/conversation", {
        auth: true,
        params: {
          other_id: 聊天对方.id,
          other_type: 聊天对方.type,
          limit: 50
        }
      });
      渲染聊天记录(数据.messages || []);
    } catch (e) {
      body.innerHTML = `<div class="chat-loading" style="color:var(--danger)">加载失败</div>`;
    }
  }

  function 渲染聊天记录(消息列表) {
    const body = document.getElementById("chat-body");
    if (!消息列表.length) {
      body.innerHTML = '<div class="chat-loading">暂无消息，开始聊天吧～</div>';
      return;
    }
    body.innerHTML = 消息列表.map(m => `
      <div class="chat-msg ${m.is_self ? "chat-self" : "chat-other"}">
        <div class="chat-bubble">
          ${escapeHtml(m.content)}
        </div>
        <div class="chat-time">${(m.created_at || "").substring(5)}</div>
      </div>
    `).join("");
    body.scrollTop = body.scrollHeight;
  }

  async function 发送消息() {
    const input = document.getElementById("chat-input");
    const content = input.value.trim();
    if (!content) { showToast("请输入消息内容", "error"); return; }
    try {
      await API.request("POST", "/api/messages/send", {
        body: {
          receiver_id: 聊天对方.id,
          receiver_type: 聊天对方.type,
          content: content,
          item_id: ID
        },
        auth: true
      });
      input.value = "";
      await 加载聊天记录();
    } catch (e) {
      showToast(e.msg || "发送失败", "error");
    }
  }

  function 渲染留言(list) {
    const box = document.getElementById("msg-list");
    if (!list.length) {
      box.innerHTML = '<p style="color:var(--muted);text-align:center;padding:20px">暂无留言，来做第一个吧～</p>';
      return;
    }
    box.innerHTML = list.map(m => `
      <div class="msg-item">
        <div class="msg-avatar">${m.name ? m.name[0] : "?"}</div>
        <div class="msg-body">
          <div class="msg-head">
            <span><span class="msg-name">${escapeHtml(m.name)}</span>
              <span class="msg-role">${m.role === "teacher" ? "老师" : "学生"}</span></span>
            <span class="msg-time">${相对时间(m.created_at)}</span>
          </div>
          <div class="msg-text">${escapeHtml(m.content)}</div>
        </div>
      </div>
    `).join("");
  }

  async function 加载() {
    // 先拿到当前用户
    if (API.isLogged()) {
      try { window.__me = await API.me(); } catch (_) {}
    }
    try {
      const 数据 = await API.request("GET", `/api/items/${ID}`);
      填充(数据);
      const msg = await API.request("GET", `/api/items/${ID}/messages`);
      渲染留言(msg || []);
    } catch (e) {
      document.querySelector(".page").innerHTML =
        `<div style="padding:60px;text-align:center;color:var(--danger)">
          ${escapeHtml(e.msg || "数据加载失败")}<br><br>
          <a class="btn btn-primary" href="/失物大厅.html">返回大厅</a></div>`;
    }
  }

  document.getElementById("send-msg").addEventListener("click", async () => {
    const ta = document.getElementById("msg-input");
    const c = ta.value.trim();
    if (!c) { showToast("请输入留言内容", "error"); return; }
    try {
      await API.request("POST", `/api/items/${ID}/messages`, { body: { content: c }, auth: true });
      ta.value = "";
      showToast("留言成功", "success");
      const msg = await API.request("GET", `/api/items/${ID}/messages`);
      渲染留言(msg || []);
    } catch (e) {
      showToast(e.msg || "留言失败", "error");
    }
  });

  加载();
})();
