document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("recipeForm");

  /* 1️⃣ 找到所有文字輸入框（排除 submit/button 類型） */
  const inputs = Array.from(
    form.querySelectorAll("input:not([type=submit]):not([type=button])")
  );

  /* 2️⃣ 為每個 input 標註順序索引 */
  inputs.forEach((inp, idx) => (inp.dataset.idx = idx));

  /* 3️⃣ 針對每個 input 綁 keydown → 攔 Enter */
  inputs.forEach((inp) => {
    inp.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        e.preventDefault(); // 阻止預設送出
        const idx = +e.target.dataset.idx; // 目前索引
        if (idx < inputs.length - 1) {
          inputs[idx + 1].focus(); // 跳到下一欄
        } else {
          form.requestSubmit(); // 最後一欄才送表單
        }
      }
    });
  });

  // 2️⃣ 抓元素
  const userIdInput = document.getElementById("user_id");
  const flavorIpt = document.getElementById("flavor_preference");
  const typeIpt = document.getElementById("recipe_type_preference");
  const avoidIpt = document.getElementById("avoid_ingredients");
  const timeIpt = document.getElementById("cooking_constraints");
  const dietIpt = document.getElementById("dietary_restrictions");

  // 4️⃣ 送出表單產生食譜 + 顯示回饋按鈕
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const userId = document.querySelector(".user-panel span").textContent.replace("歡迎, ", "").trim();
    // 用 FormData 抓取整個 <form> 的內容，包括圖片
    const formData = new FormData(form);
    formData.append("user_id", userId);  // 加入 user_id
    // 檢查圖片是否至少有一張
    const files = document.getElementById("ingredients").files;
    if (!files.length) {
      alert("請至少上傳一張食材圖片");
      return;
    }

    // 儲存偏好（這部分仍用 JSON）
    await fetch("/api/preferences", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        user_id: userId,
        flavor_preference: document.getElementById("flavor_preference").value.trim() || "無",
        recipe_type_preference: document.getElementById("recipe_type_preference").value.trim() || "無",
        avoid_ingredients: document.getElementById("avoid_ingredients").value.trim() || "無",
        cooking_constraints: document.getElementById("cooking_constraints").value.trim() || "無",
        dietary_restrictions: document.getElementById("dietary_restrictions").value.trim() || "無",
      }),
    });
    loading.style.display = "";
    result.textContent = "";
    feedback.style.display = "none";

    try {
      const resp = await fetch("/api/recipe", {
        method: "POST",
        body: formData,  // 重點！傳送圖片 + 文字偏好
      });
      const data = await resp.json();
      if (resp.ok) {
        lastRecipe = data.recipe;
        lastPayload = { user_id: userId, ingredients: data.ingredients.join("、") };
        result.textContent = lastRecipe;
        feedback.style.display = "";
      } else {
        result.textContent = "錯誤：" + (data.error || resp.statusText);
      }
    } catch (err) {
      result.textContent = "網路錯誤，請稍後再試";
    } finally {
      loading.style.display = "none";
    }
  });


  // 5️⃣ 回饋按鈕
  btnLike.addEventListener("click", async () => {
    if (!lastRecipe) return;
    await fetch("/api/store_recipe", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        user_id: lastPayload.user_id,
        ingredients: lastPayload.ingredients,
        recipe: lastRecipe,
      }),
    });
    alert("👍 已記錄到 recipe_history！");
    feedback.style.display = "none";
  });
  btnDislike.addEventListener("click", () => {
    feedback.style.display = "none";
  });
});
