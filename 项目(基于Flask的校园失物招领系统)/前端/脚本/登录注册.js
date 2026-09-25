(function () {
  const TAB_LOGIN = "login";
  const TAB_REGISTER = "register";

  let currentTab = TAB_LOGIN;
  let currentRole = "student"; // student | teacher

  // DOM 引用
  const tabs = document.querySelector(".card-tabs");
  const tabBtns = document.querySelectorAll(".tab-btn");
  const formTitle = document.getElementById("form-title");
  const formDesc = document.getElementById("form-desc");
  const formActions = document.getElementById("form-actions");
  const bottomLink = document.getElementById("bottom-link");
  const errBox = document.getElementById("error-text");

  // 字段
  const codeInput = document.getElementById("field-code");
  const codeLabel = document.getElementById("label-code");
  const nameWrap = document.getElementById("wrap-name");
  const extraWrap = document.getElementById("wrap-extra");
  const extraLabel = document.getElementById("label-extra");
  const extraInput = document.getElementById("field-extra");
  const phoneWrap = document.getElementById("wrap-phone");
  const passwordInput = document.getElementById("field-password");

  // 确保 showToast 可用（公共工具.js 已定义，这里做兜底）
  if (typeof window.showToast !== "function") {
    window.showToast = function (msg, type) {
      let el = document.getElementById("toast");
      if (!el) { el = document.createElement("div"); el.id = "toast"; document.body.appendChild(el); }
      el.textContent = msg;
      el.className = "toast show " + (type === "success" ? "success" : type === "error" ? "error" : "");
      clearTimeout(window.showToast._t);
      window.showToast._t = setTimeout(() => { el.style.opacity = "0"; }, 2200);
    };
  }

  function switchTab(tab) {
    currentTab = tab;
    tabs.dataset.active = tab;
    tabBtns.forEach(b => b.classList.toggle("active", b.dataset.tab === tab));

    if (tab === TAB_LOGIN) {
      formTitle.textContent = "欢迎回来";
      formDesc.textContent = "登录后即可发布、认领与留言";
      nameWrap.style.display = "none";
      extraWrap.style.display = "none";
      phoneWrap.style.display = "none";
      renderActionCode();
      formActions.innerHTML = '<button class="btn btn-primary" type="submit">登 录</button>';
      bottomLink.innerHTML = '还没有账号？<a href="#" data-switch="register">立即注册</a>';
    } else {
      formTitle.textContent = "加入校园失物招领";
      formDesc.textContent = "学生可发布/认领；老师额外拥有后台管理权限";
      nameWrap.style.display = "block";
      extraWrap.style.display = "block";
      phoneWrap.style.display = "block";
      renderActionCode();
      formActions.innerHTML = '<button class="btn btn-primary" type="submit">注 册</button>';
      bottomLink.innerHTML = '已有账号？<a href="#" data-switch="login">去登录</a>';
    }
    hideError();
  }

  function switchRole(role) {
    currentRole = role;
    document.querySelectorAll(".role-card").forEach(c => {
      c.classList.toggle("active", c.dataset.role === role);
    });
    renderActionCode();
  }

  function renderActionCode() {
    const isTeacher = currentRole === "teacher";
    codeLabel.textContent = isTeacher ? "工号" : "学号";
    codeInput.placeholder = isTeacher ? "请输入工号" : "请输入学号";
    // 注册时显示附加字段
    if (currentTab === TAB_REGISTER) {
      extraLabel.textContent = isTeacher ? "院系" : "班级";
      extraInput.placeholder = isTeacher ? "如：计算机学院" : "如：软件 2201";
      extraWrap.classList.add("show");
    } else {
      extraWrap.classList.remove("show");
    }
  }

  function showError(msg) { errBox.textContent = msg; }
  function hideError() { errBox.textContent = ""; }

  // 收集表单数据
  function collectForm() {
    const isTeacher = currentRole === "teacher";
    const 编号字段 = isTeacher ? "teacher_id" : "student_id";
    const 附加字段 = isTeacher ? "department" : "class_name";

    const data = {
      身份: currentRole,
      [编号字段]: codeInput.value.trim(),
      password: passwordInput.value,
    };
    if (currentTab === TAB_REGISTER) {
      data.name = document.getElementById("field-name").value.trim();
      const extra = extraInput.value.trim();
      if (extra) data[附加字段] = extra;
      const phone = document.getElementById("field-phone").value.trim();
      if (phone) data.phone = phone;
    }
    return data;
  }

  function validate(data) {
    if (!data.password) { showError("请输入密码"); return false; }
    if (currentTab === TAB_REGISTER) {
      const isTeacher = currentRole === "teacher";
      const codeKey = isTeacher ? "teacher_id" : "student_id";
      if (!data[codeKey]) { showError(`请输入${isTeacher ? "工号" : "学号"}`); return false; }
      if (!data.name) { showError("请输入姓名"); return false; }
      if (data.password.length < 6) { showError("密码长度至少 6 位"); return false; }
    } else {
      const isTeacher = currentRole === "teacher";
      const codeKey = isTeacher ? "teacher_id" : "student_id";
      if (!data[codeKey]) { showError(`请输入${isTeacher ? "工号" : "学号"}`); return false; }
    }
    hideError();
    return true;
  }

  async function handleSubmit(e) {
    e.preventDefault();
    const data = collectForm();
    if (!validate(data)) return;

    try {
      let res;
      if (currentTab === TAB_LOGIN) {
        res = await API.login(data);
        showToast("登录成功", "success");
      } else {
        res = await API.register(data);
        showToast("注册成功", "success");
      }
      API.setToken(res.token);
      setTimeout(() => {
        // 老师跳后台管理，学生跳首页（后续页面）
        location.href = currentRole === "teacher" ? "/后台管理.html" : "/";
      }, 600);
    } catch (err) {
      showError((err && (err.msg || err.message)) || "请求失败");
    }
  }

  // 事件绑定
  tabBtns.forEach(b => b.addEventListener("click", () => switchTab(b.dataset.tab)));
  document.querySelectorAll(".role-card").forEach(c => {
    c.addEventListener("click", () => switchRole(c.dataset.role));
  });
  document.getElementById("auth-form").addEventListener("submit", handleSubmit);

  // 底部链接委托
  document.body.addEventListener("click", (e) => {
    const t = e.target.closest("[data-switch]");
    if (t) { e.preventDefault(); switchTab(t.dataset.switch); }
  });

  // 初始：登录页 + 学生身份
  switchTab(TAB_LOGIN);
  switchRole("student");
})();
