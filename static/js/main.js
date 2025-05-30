let lastRecipe = null;
let lastPayload = null;
let selectedRecipeMode = null;

document.addEventListener("DOMContentLoaded", () => {
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

  // 使用者偏好
  const flavorIpt = document.getElementById("flavor_preference");
  const typeIpt = document.getElementById("recipe_type_preference");
  const avoidIpt = document.getElementById("avoid_ingredients");
  const timeIpt = document.getElementById("cooking_constraints");
  const dietIpt = document.getElementById("dietary_restrictions");

  const loading = document.getElementById("loading");
  const result = document.getElementById("result");
  const feedback = document.getElementById("feedback");

  const innovativeBtn = document.getElementById("createInnovativeBtn");
  const recommendedBtn = document.getElementById("pastRecommendationBtn");
  const selectedMode = document.getElementById("selectedMode");
  const selectedModeText = document.getElementById("selectedModeText");

  // 創新料理按鈕
  innovativeBtn.addEventListener("click", () => {
    selectedRecipeMode = "innovative";
    innovativeBtn.classList.add("selected");
    recommendedBtn.classList.remove("selected");
    selectedModeText.textContent = "創新料理 - 探索全新料理風格";
    selectedMode.style.display = "block";
    console.log("選擇模式：創新料理");
  });

  // 過往推薦按鈕
  recommendedBtn.addEventListener("click", () => {
    selectedRecipeMode = "recommended";
    recommendedBtn.classList.add("selected");
    innovativeBtn.classList.remove("selected");
    selectedModeText.textContent = "過往推薦 - 基於您的喜好歷史";
    selectedMode.style.display = "block";
    console.log("選擇模式：過往推薦");
  });

  // 上傳圖片並傳入model
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

  document
    .getElementById("submitRecipeBtn")
    .addEventListener("click", async () => {
      // 檢查是否已選擇食譜模式
      if (!selectedRecipeMode) {
        alert("請先選擇食譜生成方式（創新料理或過往推薦）");
        return;
      }

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
        recipe_mode: selectedRecipeMode,
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

  function generateVisualTimeline(steps, totalTime) {
    if (!steps || steps.length === 0) {
      return "<p>無可用的時間軸數據</p>";
    }

    let visualHTML = `
      <div class="visual-timeline">
        <div class="timeline-header-info">
          <h4>視覺化烹飪流程</h4>
          <p><strong>總時間：${totalTime} 分鐘</strong></p>
        </div>
        <div class="timeline-progress">
    `;

    steps.forEach((step, index) => {
      const isFirst = index === 0;
      const isLast = index === steps.length - 1;
      const widthPercentage =
        totalTime > 0 ? (step.duration / totalTime) * 100 : 10;

      visualHTML += `
        <div class="timeline-step" style="flex: ${
          step.duration
        }; min-width: ${Math.max(widthPercentage, 10)}%;">
          <div class="step-bar ${isFirst ? "first" : ""} ${
        isLast ? "last" : ""
      }">
            <div class="step-info">
              <div class="step-number">步驟 ${step.step_number}</div>
              <div class="step-title">${step.title}</div>
              <div class="step-duration">${step.duration}分鐘</div>
            </div>
            <div class="step-time-range">
              ${step.start_time
                .toString()
                .padStart(2, "0")}:00 - ${step.end_time
        .toString()
        .padStart(2, "0")}:00
            </div>
          </div>
        </div>
      `;
    });

    visualHTML += `
        </div>
      </div>
    `;

    return visualHTML;
  }

  function displayRecipeWithTimeline(data) {
    const resultDiv = document.getElementById("result");
    resultDiv.innerHTML = "";

    const modeInfo = document.createElement("div");
    modeInfo.className = "recipe-mode-info";
    const modeText =
      selectedRecipeMode === "innovative" ? "創新料理" : "過往推薦";
    modeInfo.innerHTML = `<p class="mode-indicator">生成模式：${modeText}</p>`;
    resultDiv.appendChild(modeInfo);

    const recipeDiv = document.createElement("div");
    recipeDiv.className = "recipe-content markdown-content";

    if (typeof marked !== "undefined") {
      recipeDiv.innerHTML = marked.parse(data.recipe);
    } else {
      recipeDiv.innerHTML = `<pre class="markdown-fallback">${data.recipe}</pre>`;
    }

    resultDiv.appendChild(recipeDiv);

    if (data.has_timeline && data.timeline) {
      const timelineContainer = document.createElement("div");
      timelineContainer.className = "timeline-container";

      let visualTimelineHTML = "<p>視覺時間軸數據不完整</p>";
      if (data.steps_data && data.total_time) {
        try {
          visualTimelineHTML = generateVisualTimeline(
            data.steps_data,
            data.total_time
          );
        } catch (error) {
          console.error("生成視覺時間軸時發生錯誤:", error);
          visualTimelineHTML = `<p>視覺時間軸生成失敗: ${error.message}</p>`;
        }
      }

      timelineContainer.innerHTML = `
        <div class="timeline-header">
          <h3>烹飪時間軸</h3>
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
          ${visualTimelineHTML}
        </div>
      `;

      resultDiv.appendChild(timelineContainer);

    } else if (data.timeline_error) {
      const errorDiv = document.createElement("div");
      errorDiv.className = "timeline-error";
      errorDiv.innerHTML = `
        <p>時間軸生成失敗: ${data.timeline_error}</p>
        <details>
          <summary>查看詳細資訊</summary>
          <pre>${JSON.stringify(data, null, 2)}</pre>
        </details>
      `;
      resultDiv.appendChild(errorDiv);
    }

    resultDiv.style.display = "block";
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
        recipe_mode: selectedRecipeMode,
      }),
    });
    alert("已記錄到 recipe_history！");
    feedback.style.display = "none";
  });

  document.getElementById("btnDislike").addEventListener("click", () => {
    feedback.style.display = "none";
  });
});


function showTimelineTab(tabName) {
  try {
    document.querySelectorAll(".timeline-content").forEach((el) => {
      el.style.display = "none";
    });

    document.querySelectorAll(".tab-btn").forEach((btn) => {
      btn.classList.remove("active");
    });

    const targetContent = document.getElementById(`timeline-${tabName}`);
    if (targetContent) {
      targetContent.style.display = "block";

      if (tabName === "checklist") {
        const checklistContainer =
          document.getElementById("timeline-checklist");
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
                  <p>無法初始化互動檢查清單</p>
                  <p>錯誤: ${error.message}</p>
                </div>
              `;
            }
          }, 100);
        } else if (checklistContainer) {
          setTimeout(() => {
            updateProgress();
          }, 50);
        }
      }
    }

    event.target.classList.add("active");
  } catch (error) {
    console.error("切換時間軸標籤時發生錯誤:", error);
  }
}

function processChecklistMarkdown() {
  const checklistContainer = document.getElementById("timeline-checklist");
  if (!checklistContainer) return;

  if (checklistContainer.dataset.markdownProcessed === "true") {
    console.log("Markdown 已處理過，跳過重複處理");
    return;
  }

  let checklistContent =
    checklistContainer.innerHTML || checklistContainer.textContent;

  // 如果已經包含互動元素，跳過處理
  if (checklistContainer.querySelector(".checklist-item")) {
    console.log("檢查清單已經包含互動元素，跳過處理");
    checklistContainer.dataset.markdownProcessed = "true";
    return;
  }

  try {
    if (typeof marked !== "undefined" && checklistContent.includes("- [ ]")) {
      const renderedHtml = marked.parse(checklistContent);
      checklistContainer.innerHTML = renderedHtml;
    }

    const listItems = checklistContainer.querySelectorAll("li");
    let convertedCount = 0;

    listItems.forEach((item, index) => {
      const text = item.textContent.trim();

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

        const checkbox = item.querySelector(".step-checkbox");
        if (checkbox) {
          checkbox.addEventListener("change", handleCheckboxChange);
        }

        convertedCount++;
        console.log(`成功轉換步驟 ${index + 1}: ${time} - ${title}`);
      } else {
        console.log(`無法匹配步驟格式: ${text}`);
      }
    });

    console.log(`總共轉換了 ${convertedCount} 個檢查清單項目`);

    checklistContainer.dataset.markdownProcessed = "true";
  } catch (error) {
    console.error("處理檢查清單 Markdown 時發生錯誤:", error);

    checklistContainer.innerHTML = `
      <div class="timeline-error">
        <p>檢查清單格式處理失敗</p>
        <p>原始內容:</p>
        <pre>${checklistContent}</pre>
      </div>
    `;
  }
}

function initializeInteractiveChecklist() {
  try {
    const checkboxes = document.querySelectorAll(".step-checkbox");

    if (checkboxes.length === 0) {
      console.log("沒有找到可互動的檢查清單項目");
      return;
    }
    console.log(`找到 ${checkboxes.length} 個檢查清單項目`);
    const existingProgress = document.querySelector(
      "#timeline-checklist .progress-container"
    );
    if (!existingProgress) {
      addProgressBar();
    }

    checkboxes.forEach((checkbox, index) => {
      if (!checkbox.dataset.initialized) {
        checkbox.addEventListener("change", handleCheckboxChange);
        checkbox.dataset.initialized = "true";
        console.log(`初始化檢查項目 ${index + 1}`);
      }
    });

    updateProgress();
  } catch (error) {
    console.error("初始化互動檢查清單時發生錯誤:", error);
  }
}

function displayRecipeWithTimeline(data) {
  const resultDiv = document.getElementById("result");

  resultDiv.innerHTML = "";

  const recipeDiv = document.createElement("div");
  recipeDiv.className = "recipe-content markdown-content";

  if (typeof marked !== "undefined") {
    recipeDiv.innerHTML = marked.parse(data.recipe);
  } else {
    recipeDiv.innerHTML = `<pre class="markdown-fallback">${data.recipe}</pre>`;
  }

  resultDiv.appendChild(recipeDiv);

  if (data.has_timeline && data.timeline) {
    const timelineContainer = document.createElement("div");
    timelineContainer.className = "timeline-container";
    timelineContainer.innerHTML = `
      <div class="timeline-header">
        <h3>烹飪時間軸</h3>
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
      <p>時間軸生成失敗: ${data.timeline_error}</p>
      <details>
        <summary>查看詳細資訊</summary>
        <pre>${JSON.stringify(data, null, 2)}</pre>
      </details>
    `;
    resultDiv.appendChild(errorDiv);
  }

  resultDiv.style.display = "block";
}

function addProgressBar() {
  const checklistContainer = document.querySelector("#timeline-checklist");
  if (!checklistContainer) return;

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
        <h3>恭喜完成所有步驟！</h3>
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
