document.addEventListener("DOMContentLoaded", () => {
  async function loadIngredients() {
    try {
      const resp = await fetch("/api/ingredients");
      const data = await resp.json();
      if (resp.ok) {
        document.getElementById("ingredientList").value = data.ingredients.join("\n");
      } else {
        console.log("尚無食材清單");
      }
    } catch (err) {
      console.log("尚無食材清單");
    }
  }
  loadIngredients();
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

  document.getElementById("confirmIngredients").addEventListener("click", async (e) => {
    e.preventDefault();
    const files = document.getElementById("ingredients").files;
    if (!files.length) {
      alert("請至少上傳一張食材圖片");
      return;
    }
  
    const formData = new FormData();
    for (const f of files) formData.append("ingredients", f);
  
    loading.style.display = "";
    try {
      const resp = await fetch("/api/upload_images", {
        method: "POST",
        body: formData
      });
      const data = await resp.json();
      if (resp.ok) {
        // 把模型回傳的食材清單用換行放到 textarea
        document.getElementById("ingredientList").value = data.ingredients.join("\n");
      } else {
        alert("錯誤：" + data.error);
      }
    } catch {
      alert("網路錯誤，請稍後再試");
    } finally {
      loading.style.display = "none";
    }
  });  
  

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const userId = document.querySelector(".user-panel span").textContent.replace("歡迎, ", "").trim();
    const edited = document.getElementById("ingredientList").value.trim();
    if (!edited) {
      alert("食材清單不能為空");
      return;
    }
  
    // 儲存偏好（保持原本做法）
    await fetch("/api/preferences", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        user_id: userId,
        flavor_preference: flavorIpt.value.trim() || "無",
        recipe_type_preference: typeIpt.value.trim() || "無",
        avoid_ingredients: avoidIpt.value.trim() || "無",
        cooking_constraints: timeIpt.value.trim() || "無",
        dietary_restrictions: dietIpt.value.trim() || "無"
      })
    });
  
    loading.style.display = "";
    result.textContent = "";
    feedback.style.display = "none";
  
    // 準備最終 payload
    const payload = {
      user_id: userId,
      // 把換行轉成中文頓號分隔
      ingredients: edited.split(/\r?\n/).join("、"),
      flavor_preference: flavorIpt.value.trim() || "無",
      recipe_type_preference: typeIpt.value.trim() || "無",
      avoid_ingredients: avoidIpt.value.trim() || "無",
      cooking_constraints: timeIpt.value.trim() || "無",
      dietary_restrictions: dietIpt.value.trim() || "無"
    };
  
    try {
      const resp = await fetch("/api/recipe", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      const data = await resp.json();
      if (resp.ok) {
        lastRecipe = data.recipe;
        lastPayload = payload;
        result.textContent = lastRecipe;
        feedback.style.display = "";
      } else {
        result.textContent = "錯誤：" + (data.error || resp.statusText);
      }
    } catch {
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
