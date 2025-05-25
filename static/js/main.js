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
        include_timeline: true,
      };

      console.log("發送的偏好數據:", payload);

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

          // 🔥 顯示食譜和時間軸
          displayRecipeWithTimeline(data);

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

  // 🔥 修改：顯示食譜和時間軸的函數
  function displayRecipeWithTimeline(data) {
    const resultDiv = document.getElementById("result");

    // 清空之前的內容
    resultDiv.innerHTML = "";

    // 顯示主食譜 - 使用 Markdown 渲染
    const recipeDiv = document.createElement("div");
    recipeDiv.className = "recipe-content markdown-content";

    if (typeof marked !== "undefined") {
      recipeDiv.innerHTML = marked.parse(data.recipe);
    } else {
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
            <button class="tab-btn" onclick="showTimelineTab('checklist')">互動檢查清單</button>
            <button class="tab-btn" onclick="showTimelineTab('visual')">視覺時間軸</button>
          </div>
        </div>
        
        <div id="timeline-text" class="timeline-content markdown-content">
          ${
            typeof marked !== "undefined"
              ? marked.parse(data.timeline)
              : `<pre>${data.timeline}</pre>`
          }
        </div>
        
        <div id="timeline-checklist" class="timeline-content checklist-content" style="display:none;">
          ${data.checklist || "檢查清單生成中..."}
        </div>
        
        <div id="timeline-visual" class="timeline-content" style="display:none;">
          ${generateVisualTimeline(data.steps_data, data.total_time)}
        </div>
      `;

      resultDiv.appendChild(timelineContainer);

      // 🔥 不要在這裡初始化，讓 showTimelineTab 來處理
    } else if (data.timeline_error) {
      const errorDiv = document.createElement("div");
      errorDiv.className = "timeline-error";
      errorDiv.innerHTML = `<p>⚠️ 時間軸生成失敗: ${data.timeline_error}</p>`;
      resultDiv.appendChild(errorDiv);
    }

    resultDiv.style.display = "block";
  }

  // 🔥 修改：生成視覺時間軸
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

// 🔥 修改：切換時間軸顯示 - 避免重複處理
function showTimelineTab(tabName) {
  try {
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

      // 如果是檢查清單標籤，處理初始化
      if (tabName === "checklist") {
        const checklistContainer =
          document.getElementById("timeline-checklist");

        // 🔥 每次都重新檢查是否需要初始化
        if (checklistContainer && !checklistContainer.dataset.initialized) {
          setTimeout(() => {
            try {
              processChecklistMarkdown();
              initializeInteractiveChecklist();
              checklistContainer.dataset.initialized = "true";
            } catch (error) {
              console.error("初始化檢查清單時發生錯誤:", error);
              checklistContainer.innerHTML = `
                <div class="timeline-error">
                  <p>⚠️ 無法初始化互動檢查清單</p>
                  <p>錯誤: ${error.message}</p>
                </div>
              `;
            }
          }, 100);
        } else if (checklistContainer) {
          // 已初始化，只更新進度
          setTimeout(() => {
            updateProgress();
          }, 50);
        }
      }
    }

    // 為當前按鈕添加 active 類別
    event.target.classList.add("active");
  } catch (error) {
    console.error("切換時間軸標籤時發生錯誤:", error);
  }
}

// 🔥 修改：處理檢查清單 Markdown - 更強健的格式處理
function processChecklistMarkdown() {
  const checklistContainer = document.getElementById("timeline-checklist");
  if (!checklistContainer) return;

  // 檢查是否已經處理過
  if (checklistContainer.dataset.markdownProcessed === "true") {
    console.log("Markdown 已處理過，跳過重複處理");
    return;
  }

  // 獲取原始內容
  let checklistContent =
    checklistContainer.innerHTML || checklistContainer.textContent;

  // 如果已經包含互動元素，跳過處理
  if (checklistContainer.querySelector(".checklist-item")) {
    console.log("檢查清單已經包含互動元素，跳過處理");
    checklistContainer.dataset.markdownProcessed = "true";
    return;
  }

  try {
    // 🔥 先用 marked 渲染 Markdown
    if (typeof marked !== "undefined" && checklistContent.includes("- [ ]")) {
      const renderedHtml = marked.parse(checklistContent);
      checklistContainer.innerHTML = renderedHtml;
    }

    // 🔥 找到所有的任務列表項目並轉換為互動式
    const listItems = checklistContainer.querySelectorAll("li");
    let convertedCount = 0;

    listItems.forEach((item, index) => {
      const text = item.textContent.trim();

      // 🔥 多重格式檢測模式
      const patterns = [
        // 標準格式：**12:00** - 準備食材 (5分鐘)
        /\*\*(\d{2}:\d{2})\*\*\s*-\s*(.+?)\s*\((\d+)分鐘\)/,
        // 簡化格式：12:00 - 準備食材 (5分鐘)
        /(\d{2}:\d{2})\s*-\s*(.+?)\s*\((\d+)分鐘\)/,
        // 更寬鬆格式：包含時間和分鐘的任何格式
        /(\d{1,2}:\d{2}).*?([^(]+)\s*\((\d+)分鐘\)/,
      ];

      let match = null;
      for (const pattern of patterns) {
        match = text.match(pattern);
        if (match) break;
      }

      if (match) {
        const time = match[1];
        const title = match[2].trim();
        const duration = match[3];
        const checkboxId = `step-checkbox-${index}`;

        item.innerHTML = `
          <div class="checklist-item">
            <input type="checkbox" id="${checkboxId}" class="step-checkbox">
            <label for="${checkboxId}" class="step-label">
              <strong>${time}</strong> - ${title} (${duration}分鐘)
            </label>
          </div>
        `;

        // 添加事件監聽器
        const checkbox = item.querySelector(".step-checkbox");
        if (checkbox) {
          checkbox.addEventListener("change", handleCheckboxChange);
        }

        convertedCount++;
        console.log(`✅ 成功轉換步驟 ${index + 1}: ${time} - ${title}`);
      } else {
        console.log(`⚠️ 無法匹配步驟格式: ${text}`);
      }
    });

    console.log(`🎯 總共轉換了 ${convertedCount} 個檢查清單項目`);

    // 標記為已處理
    checklistContainer.dataset.markdownProcessed = "true";
  } catch (error) {
    console.error("處理檢查清單 Markdown 時發生錯誤:", error);

    // 🔥 錯誤處理：如果處理失敗，顯示錯誤訊息
    checklistContainer.innerHTML = `
      <div class="timeline-error">
        <p>⚠️ 檢查清單格式處理失敗</p>
        <p>原始內容:</p>
        <pre>${checklistContent}</pre>
      </div>
    `;
  }
}

// 🔥 修改：初始化互動式檢查清單 - 增加驗證
function initializeInteractiveChecklist() {
  try {
    const checkboxes = document.querySelectorAll(".step-checkbox");

    if (checkboxes.length === 0) {
      console.log("⚠️ 沒有找到可互動的檢查清單項目");
      return;
    }

    console.log(`🎯 找到 ${checkboxes.length} 個檢查清單項目`);

    // 添加進度條
    const existingProgress = document.querySelector(
      "#timeline-checklist .progress-container"
    );
    if (!existingProgress) {
      addProgressBar();
    }

    // 確保所有 checkbox 都有事件監聽器
    checkboxes.forEach((checkbox, index) => {
      if (!checkbox.dataset.initialized) {
        checkbox.addEventListener("change", handleCheckboxChange);
        checkbox.dataset.initialized = "true";
        console.log(`✅ 初始化檢查項目 ${index + 1}`);
      }
    });

    // 初始化進度顯示
    updateProgress();
  } catch (error) {
    console.error("初始化互動檢查清單時發生錯誤:", error);
  }
}

// 🔥 修改：顯示食譜和時間軸 - 重置狀態
function displayRecipeWithTimeline(data) {
  const resultDiv = document.getElementById("result");

  // 清空之前的內容
  resultDiv.innerHTML = "";

  // 顯示主食譜
  const recipeDiv = document.createElement("div");
  recipeDiv.className = "recipe-content markdown-content";

  if (typeof marked !== "undefined") {
    recipeDiv.innerHTML = marked.parse(data.recipe);
  } else {
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
          <button class="tab-btn" onclick="showTimelineTab('checklist')">互動檢查清單</button>
          <button class="tab-btn" onclick="showTimelineTab('visual')">視覺時間軸</button>
        </div>
      </div>
      
      <div id="timeline-text" class="timeline-content markdown-content">
        ${
          typeof marked !== "undefined"
            ? marked.parse(data.timeline)
            : `<pre>${data.timeline}</pre>`
        }
      </div>
      
      <div id="timeline-checklist" class="timeline-content checklist-content" style="display:none;">
        ${data.checklist || "檢查清單生成中..."}
      </div>
      
      <div id="timeline-visual" class="timeline-content" style="display:none;">
        ${generateVisualTimeline(data.steps_data, data.total_time)}
      </div>
    `;

    resultDiv.appendChild(timelineContainer);
  } else if (data.timeline_error) {
    const errorDiv = document.createElement("div");
    errorDiv.className = "timeline-error";
    errorDiv.innerHTML = `
      <p>⚠️ 時間軸生成失敗: ${data.timeline_error}</p>
      <details>
        <summary>查看詳細資訊</summary>
        <pre>${JSON.stringify(data, null, 2)}</pre>
      </details>
    `;
    resultDiv.appendChild(errorDiv);
  }

  resultDiv.style.display = "block";
}

// 🔥 修改：添加進度條 - 更安全的檢查
function addProgressBar() {
  const checklistContainer = document.querySelector("#timeline-checklist");
  if (!checklistContainer) return;

  // 🔥 更嚴格的檢查，確保不會重複添加
  const existingProgress = checklistContainer.querySelector(
    ".progress-container"
  );
  if (existingProgress) {
    console.log("進度條已存在，跳過添加");
    return;
  }

  const progressHTML = `
    <div class="progress-container">
      <div class="progress-text">完成進度: <span id="progress-count">0</span>/<span id="total-count">0</span></div>
      <div class="progress-bar">
        <div class="progress-fill" id="progress-fill"></div>
      </div>
    </div>
  `;

  checklistContainer.insertAdjacentHTML("afterbegin", progressHTML);

  // 更新總數
  setTimeout(() => {
    const totalSteps = document.querySelectorAll(".step-checkbox").length;
    const totalCountElement = document.getElementById("total-count");
    if (totalCountElement) {
      totalCountElement.textContent = totalSteps;
    }
  }, 50);
}

// 🔥 其他函數保持不變...
function handleCheckboxChange(event) {
  const checkbox = event.target;
  const checklistItem = checkbox.closest(".checklist-item");

  if (checkbox.checked) {
    checklistItem.classList.add("completed");
    playCheckSound();
  } else {
    checklistItem.classList.remove("completed");
  }

  updateProgress();
  checkAllCompleted();
}

function updateProgress() {
  const checkboxes = document.querySelectorAll(".step-checkbox");
  const completedCount = document.querySelectorAll(
    ".step-checkbox:checked"
  ).length;
  const totalCount = checkboxes.length;

  const progressFill = document.getElementById("progress-fill");
  const progressCount = document.getElementById("progress-count");

  if (progressFill && progressCount) {
    const percentage = totalCount > 0 ? (completedCount / totalCount) * 100 : 0;
    progressFill.style.width = percentage + "%";
    progressCount.textContent = completedCount;
  }
}

function checkAllCompleted() {
  const checkboxes = document.querySelectorAll(".step-checkbox");
  const completedCount = document.querySelectorAll(
    ".step-checkbox:checked"
  ).length;

  if (completedCount === checkboxes.length && checkboxes.length > 0) {
    setTimeout(() => {
      celebrateCompletion();
    }, 300);
  } else {
    hideCompletionMessage();
  }
}

function playCheckSound() {
  try {
    if (
      typeof AudioContext === "undefined" &&
      typeof webkitAudioContext === "undefined"
    ) {
      return;
    }

    const audioContext = new (window.AudioContext ||
      window.webkitAudioContext)();

    if (audioContext.state === "suspended") {
      return;
    }

    const oscillator = audioContext.createOscillator();
    const gainNode = audioContext.createGain();

    oscillator.connect(gainNode);
    gainNode.connect(audioContext.destination);

    oscillator.frequency.setValueAtTime(800, audioContext.currentTime);
    oscillator.frequency.setValueAtTime(1000, audioContext.currentTime + 0.1);

    gainNode.gain.setValueAtTime(0.1, audioContext.currentTime);
    gainNode.gain.exponentialRampToValueAtTime(
      0.01,
      audioContext.currentTime + 0.2
    );

    oscillator.start(audioContext.currentTime);
    oscillator.stop(audioContext.currentTime + 0.2);
  } catch (error) {
    console.log("音效播放失敗:", error);
  }
}

function celebrateCompletion() {
  showCompletionMessage();

  const colors = ["#ff6b6b", "#4ecdc4", "#45b7d1", "#96ceb4", "#ffeaa7"];

  for (let i = 0; i < 15; i++) {
    setTimeout(() => {
      createConfetti(colors[Math.floor(Math.random() * colors.length)]);
    }, i * 100);
  }
}

function showCompletionMessage() {
  const checklistContainer = document.querySelector("#timeline-checklist");
  if (!checklistContainer) return;

  let completionMessage = checklistContainer.querySelector(
    ".completion-message"
  );

  if (!completionMessage) {
    completionMessage = document.createElement("div");
    completionMessage.className = "completion-message";
    completionMessage.innerHTML = `
      <div class="completion-content">
        <h3>🎉 恭喜完成所有步驟！</h3>
        <p>現在可以享用您的美食了！</p>
      </div>
    `;
    checklistContainer.appendChild(completionMessage);
  }

  completionMessage.style.display = "block";
  setTimeout(() => {
    completionMessage.classList.add("show");
  }, 50);
}

function hideCompletionMessage() {
  const completionMessage = document.querySelector(".completion-message");
  if (completionMessage) {
    completionMessage.classList.remove("show");
    setTimeout(() => {
      completionMessage.style.display = "none";
    }, 300);
  }
}

function createConfetti(color) {
  try {
    const confetti = document.createElement("div");
    confetti.style.cssText = `
      position: fixed;
      width: 8px;
      height: 8px;
      background: ${color};
      left: ${Math.random() * window.innerWidth}px;
      top: -10px;
      z-index: 1000;
      pointer-events: none;
      border-radius: 50%;
    `;

    document.body.appendChild(confetti);

    let start = null;
    const duration = 3000;
    const endY = window.innerHeight + 10;

    function animate(timestamp) {
      if (!start) start = timestamp;
      const progress = (timestamp - start) / duration;

      if (progress < 1) {
        const y = progress * endY;
        const rotation = progress * 360;
        confetti.style.transform = `translateY(${y}px) rotate(${rotation}deg)`;
        confetti.style.opacity = 1 - progress;
        requestAnimationFrame(animate);
      } else {
        confetti.remove();
      }
    }

    requestAnimationFrame(animate);
  } catch (error) {
    console.log("彩帶效果失敗:", error);
  }
}
