(function () {
  渲染导航("post");

  if (!API.isLogged()) {
    setTimeout(() => {
      showToast("请先登录", "error");
      location.href = "/登录注册.html";
    }, 400);
    return;
  }

  const 状态 = { type: 0, category: 0, image_url: "" };

  // 类型切换
  function 渲染类型() {
    document.querySelectorAll(".type-opt").forEach(el => {
      el.classList.toggle("active", Number(el.dataset.v) === 状态.type);
    });
  }
  document.querySelectorAll(".type-opt").forEach(el => {
    el.addEventListener("click", () => { 状态.type = Number(el.dataset.v); 渲染类型(); });
  });

  // 分类下拉
  const catSel = document.getElementById("field-category");
  catSel.innerHTML = Object.entries(CATEGORIES).map(([k, c]) =>
    `<option value="${k}">${c.label}</option>`
  ).join("");
  catSel.addEventListener("change", () => 状态.category = Number(catSel.value));

  // 图片上传
  document.getElementById("uploader").addEventListener("click", () => {
    document.getElementById("file-input").click();
  });
  document.getElementById("file-input").addEventListener("change", async (e) => {
    const f = e.target.files[0];
    if (!f) return;
    const fd = new FormData();
    fd.append("file", f);
    try {
      const res = await API.request("POST", "/api/upload", { body: fd, formData: true });
      if (res && res.url) {
        状态.image_url = res.url;
        const box = document.getElementById("uploader");
        box.innerHTML = `<img src="${res.url}" alt="上传图片" />`;
        showToast("上传成功", "success");
      }
    } catch (err) {
      showToast(err.msg || "上传失败", "error");
    }
  });

  // 重写接口封装，支持 FormData
  const _req = API.request;
  API.request = async function (method, path, opts = {}) {
    if (opts.formData) {
      const headers = {};
      if (API.getToken()) headers["Authorization"] = "Bearer " + API.getToken();
      const resp = await fetch(path, { method, headers, body: opts.body });
      const data = await resp.json();
      if (!resp.ok || (data && data.code && data.code !== 0))
        throw { msg: (data && data.msg) || "请求失败", status: resp.status };
      return data.data;
    }
    return _req(method, path, opts);
  };

  // 提交
  document.getElementById("post-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const payload = {
      type: 状态.type,
      category: 状态.category,
      title: document.getElementById("field-title").value.trim(),
      description: document.getElementById("field-desc").value.trim(),
      location: document.getElementById("field-loc").value.trim(),
      image_url: 状态.image_url,
    };
    if (!payload.title) { showToast("请填写标题", "error"); return; }
    try {
      const r = await API.request("POST", "/api/items", { body: payload, auth: true });
      showToast("发布成功，等待老师审核", "success");
      setTimeout(() => location.href = `/详情.html?id=${r.id}`, 700);
    } catch (err) {
      showToast(err.msg || "发布失败", "error");
    }
  });

  渲染类型();
})();
