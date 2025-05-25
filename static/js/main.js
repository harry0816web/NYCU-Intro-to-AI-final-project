let lastRecipe = null;
let lastPayload = null;

document.addEventListener("DOMContentLoaded", () => {
  // 讀取初次 /api/ingredients
  async function loadIngredients() {
    try {
      const resp = await fetch("/api/ingredients");
      const data = await resp.json();
      if (resp.ok) {
        document.getElementById("ingredientList").value = data.ingredients.join("\n");
      }
    } catch {
      console.log("尚無食材清單");
    }
  }
  loadIngredients();

  // 各偏好欄位
  const flavorIpt = document.getElementById("flavor_preference");
  const typeIpt   = document.getElementById("recipe_type_preference");
  const avoidIpt  = document.getElementById("avoid_ingredients");
  const timeIpt   = document.getElementById("cooking_constraints");
  const dietIpt   = document.getElementById("dietary_restrictions");

  const loading   = document.getElementById("loading");
  const result    = document.getElementById("result");
  const feedback  = document.getElementById("feedback");

  // 圖片上傳 → 模型辨識
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

  // 最終產生食譜 → JSON 送到 /api/recipe
  document.getElementById("submitRecipeBtn").addEventListener("click", async () => {
    const userId = document.querySelector(".user-panel span").textContent.replace("歡迎, ", "").trim();
    const edited = document.getElementById("ingredientList").value.trim();
    if (!edited) {
      return alert("食材清單不能為空");
    }

    // 建立 JSON payload
    const payload = {
      user_id: userId,
      ingredients: edited.split(/\r?\n/).join("、"),
      flavor_preference: flavorIpt.value.trim() || "無",
      recipe_type_preference: typeIpt.value.trim() || "無",
      avoid_ingredients: avoidIpt.value.trim() || "無",
      cooking_constraints: timeIpt.value.trim() || "無",
      dietary_restrictions: dietIpt.value.trim() || "無"
    };

    loading.style.display = "";
    try {
      const resp = await fetch("/api/recipe", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      const data = await resp.json();
      if (resp.ok) {
        lastRecipe = data.recipe;         // 💡 把最後的 recipe 記錄下來
        lastPayload = payload;            // 💡 把最後的 payload 記錄下來
        result.textContent = lastRecipe;
        feedback.style.display = "";
      } else {
        result.textContent = "錯誤：" + data.error;
      }
    } catch {
      result.textContent = "網路錯誤，請稍後再試";
    } finally {
      loading.style.display = "none";
    }
  });

  // 回饋按鈕
  document.getElementById("btnLike").addEventListener("click", async () => {
    if (!lastRecipe || !lastPayload) return alert("請先產生食譜！");
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

  document.getElementById("btnDislike").addEventListener("click", () => {
    feedback.style.display = "none";
  });
});
