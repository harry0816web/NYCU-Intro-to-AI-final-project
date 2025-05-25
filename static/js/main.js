let lastRecipe = null;
let lastPayload = null;

document.addEventListener("DOMContentLoaded", () => {
  // 讀取初次 /api/ingredients
  async function loadIngredients() {
    try {
      const resp = await fetch("/api/ingredients");
      const data = await resp.json();
      if (resp.ok) {
        document.getElementById("ingredientList").value =
          data.ingredients.join("\n");
      }
    } catch {
      console.log("尚無食材清單");
    }
  }
  loadIngredients();

  // 各偏好欄位
  const flavorIpt = document.getElementById("flavor_preference");
  const typeIpt = document.getElementById("recipe_type_preference");
  const avoidIpt = document.getElementById("avoid_ingredients");
  const timeIpt = document.getElementById("cooking_constraints");
  const dietIpt = document.getElementById("dietary_restrictions");

  const loading = document.getElementById("loading");
  const result = document.getElementById("result");
  const feedback = document.getElementById("feedback");

  // 圖片上傳 → 模型辨識
  document
    .getElementById("confirmIngredients")
    .addEventListener("click", async (e) => {
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
          body: formData,
        });
        const data = await resp.json();
        if (resp.ok) {
          document.getElementById("ingredientList").value =
            data.ingredients.join("\n");
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
  document
    .getElementById("submitRecipeBtn")
    .addEventListener("click", async () => {
      const userId = document
        .querySelector(".user-panel span")
        .textContent.replace("歡迎, ", "")
        .trim();
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
        dietary_restrictions: dietIpt.value.trim() || "無",
        include_timeline: true, // 🔥 啟用時間軸
      };

      console.log("發送的偏好數據:", payload); // 🔍 調試用

      loading.style.display = "";
      try {
        const resp = await fetch("/api/recipe", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
        const data = await resp.json();
        if (resp.ok) {
          lastRecipe = data.recipe;
          lastPayload = payload;

          // 🔥 顯示 Markdown 格式食譜和時間軸
          displayMarkdownRecipeWithTimeline(data);

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

  // 🔥 新增：顯示 Markdown 食譜和時間軸的函數
  function displayMarkdownRecipeWithTimeline(data) {
    const resultDiv = document.getElementById("result");

    // 清空之前的內容
    resultDiv.innerHTML = "";

    // 顯示主食譜 - 使用 Markdown 渲染
    const recipeDiv = document.createElement("div");
    recipeDiv.className = "recipe-content markdown-content";

    // 🔥 使用 marked.js 渲染 Markdown（需要在 HTML 中引入）
    if (typeof marked !== "undefined") {
      recipeDiv.innerHTML = marked.parse(data.recipe);
    } else {
      // 如果沒有 marked.js，使用簡單的 HTML 渲染
      recipeDiv.innerHTML = `<pre class="markdown-fallback">${data.recipe}</pre>`;
    }

    resultDiv.appendChild(recipeDiv);

    // 如果有時間軸，顯示時間軸區域
    if (data.has_timeline && data.timeline) {
      const timelineContainer = document.createElement("div");
      timelineContainer.className = "timeline-container";
      timelineContainer.innerHTML = `
        <div class="timeline-header">
          <h3>🕐 烹飪時間軸</h3>
          <div class="timeline-tabs">
            <button class="tab-btn active" onclick="showTimelineTab('text')">文字時間軸</button>
            <button class="tab-btn" onclick="showTimelineTab('checklist')">檢查清單</button>
            <button class="tab-btn" onclick="showTimelineTab('visual')">視覺時間軸</button>
          </div>
        </div>
        
        <div id="timeline-text" class="timeline-content">
          <pre>${data.timeline}</pre>
        </div>
        
        <div id="timeline-checklist" class="timeline-content" style="display:none;">
          <pre>${data.checklist || "檢查清單生成中..."}</pre>
        </div>
        
        <div id="timeline-visual" class="timeline-content" style="display:none;">
          ${generateVisualTimeline(data.steps_data, data.total_time)}
        </div>
      `;

      resultDiv.appendChild(timelineContainer);
    } else if (data.timeline_error) {
      const errorDiv = document.createElement("div");
      errorDiv.className = "timeline-error";
      errorDiv.innerHTML = `<p>⚠️ 時間軸生成失敗: ${data.timeline_error}</p>`;
      resultDiv.appendChild(errorDiv);
    }

    resultDiv.style.display = "block";
  }

  // 🔥 新增：生成視覺時間軸
  function generateVisualTimeline(steps, totalTime) {
    if (!steps || steps.length === 0) {
      return "<p>⚠️ 無時間軸數據</p>";
    }

    let html = `<div class="visual-timeline">
                  <h4>📊 視覺化時間軸 (總計: ${totalTime} 分鐘)</h4>`;

    steps.forEach((step, index) => {
      const percentage = Math.max((step.duration / totalTime) * 100, 5); // 最小5%
      html += `
        <div class="timeline-step-visual">
          <div class="step-info">
            <span class="step-time">${step.start_time}:00 - ${step.end_time}:00</span>
            <span class="step-title">步驟${step.step_number}: ${step.title}</span>
          </div>
          <div class="step-bar">
            <div class="step-progress" style="width: ${percentage}%"></div>
            <span class="step-duration">${step.duration}分</span>
          </div>
        </div>
      `;
    });

    html += "</div>";
    return html;
  }

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

// 🔥 新增：切換時間軸顯示的全域函數
function showTimelineTab(tabName) {
  // 隱藏所有時間軸內容
  document.querySelectorAll(".timeline-content").forEach((el) => {
    el.style.display = "none";
  });

  // 移除所有按鈕的 active 類別
  document.querySelectorAll(".tab-btn").forEach((btn) => {
    btn.classList.remove("active");
  });

  // 顯示選中的內容
  const targetContent = document.getElementById(`timeline-${tabName}`);
  if (targetContent) {
    targetContent.style.display = "block";
  }

  // 為當前按鈕添加 active 類別
  event.target.classList.add("active");
}
