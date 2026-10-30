/**
 * StudyBuddy AI - Frontend Client Architecture
 * Collaborative AI Study Partner & Shared Document Vault
 */

document.addEventListener("DOMContentLoaded", () => {
  // Application State
  const state = {
    ollamaConnected: false,
    ollamaUrl: "http://localhost:11434",
    models: {
      ollama_models: [],
      gemini_models: [],
      openai_models: [],
      anthropic_models: []
    },
    cloudKeysConfigured: {
      gemini: false,
      openai: false,
      anthropic: false
    },
    selectedModel: "qwen2.5:3b",
    studyMode: "general", // "general", "explain", "quiz", "flashcards", "summarize"
    focusDocId: null,
    focusDocName: "",
    selectedSubjectFilter: "all",
    ragEnabled: true,
    topK: 4,
    threshold: 0.05,
    temperature: 0.7,
    systemPrompt: "",
    isGenerating: false,
    documents: [],
    abortController: null,
    networkInfo: { local_ip: "127.0.0.1", port: 8000, url: "http://localhost:8000" },
    pomodoro: {
      timeRemaining: 25 * 60,
      isRunning: false,
      intervalId: null,
      mode: "Focus" // "Focus" or "Break"
    }
  };

  // DOM Elements - Header & Status
  const statusDot = document.getElementById("statusDot");
  const statusText = document.getElementById("statusText");
  const headerModelSelect = document.getElementById("headerModelSelect");
  const modalModelSelect = document.getElementById("modalModelSelect");
  const footerActiveModel = document.getElementById("footerActiveModel");
  const footerStudyMode = document.getElementById("footerStudyMode");
  const btnShareModalOpen = document.getElementById("btnShareModalOpen");
  const headerIpText = document.getElementById("headerIpText");

  // Cloud Settings Inputs & Badges
  const geminiApiKeyInput = document.getElementById("geminiApiKeyInput");
  const openaiApiKeyInput = document.getElementById("openaiApiKeyInput");
  const openaiBaseUrlInput = document.getElementById("openaiBaseUrlInput");
  const anthropicApiKeyInput = document.getElementById("anthropicApiKeyInput");
  const geminiStatusBadge = document.getElementById("geminiStatusBadge");
  const openaiStatusBadge = document.getElementById("openaiStatusBadge");
  const anthropicStatusBadge = document.getElementById("anthropicStatusBadge");
  const btnTestGemini = document.getElementById("btnTestGemini");
  const geminiTestFeedback = document.getElementById("geminiTestFeedback");
  const btnTestOpenAI = document.getElementById("btnTestOpenAI");
  const openaiTestFeedback = document.getElementById("openaiTestFeedback");
  const btnTestAnthropic = document.getElementById("btnTestAnthropic");
  const anthropicTestFeedback = document.getElementById("anthropicTestFeedback");

  // Pomodoro
  const pomodoroTime = document.getElementById("pomodoroTime");
  const pomodoroMode = document.getElementById("pomodoroMode");
  const btnPomodoroToggle = document.getElementById("btnPomodoroToggle");
  const btnPomodoroReset = document.getElementById("btnPomodoroReset");
  const pomodoroPlayIcon = document.getElementById("pomodoroPlayIcon");

  // Study Vault / Left Sidebar
  const statDocCount = document.getElementById("statDocCount");
  const statChunkCount = document.getElementById("statChunkCount");
  const statWordCount = document.getElementById("statWordCount");
  const docCountBadge = document.getElementById("docCountBadge");
  const uploadDropzone = document.getElementById("uploadDropzone");
  const fileInput = document.getElementById("fileInput");
  const uploadSubjectSelect = document.getElementById("uploadSubjectSelect");
  const uploadProgressContainer = document.getElementById("uploadProgressContainer");
  const uploadProgressBar = document.getElementById("uploadProgressBar");
  const uploadProgressText = document.getElementById("uploadProgressText");
  const subjectFilterPills = document.getElementById("subjectFilterPills");
  const docFilterInput = document.getElementById("docFilterInput");
  const documentsList = document.getElementById("documentsList");
  const btnLoadSamples = document.getElementById("btnLoadSamples");
  const btnClearAllDocs = document.getElementById("btnClearAllDocs");

  // Study Controls & Chat Workspace
  const studyModeButtons = document.querySelectorAll(".mode-btn");
  const focusDocBadge = document.getElementById("focusDocBadge");
  const focusDocName = document.getElementById("focusDocName");
  const btnResetFocusDoc = document.getElementById("btnResetFocusDoc");
  const ragToggle = document.getElementById("ragToggle");
  const ragToggleTitle = document.getElementById("ragToggleTitle");
  const btnClearChat = document.getElementById("btnClearChat");

  const chatMessages = document.getElementById("chatMessages");
  const welcomeHero = document.getElementById("welcomeHero");
  const chatForm = document.getElementById("chatForm");
  const messageInput = document.getElementById("messageInput");
  const btnSendMessage = document.getElementById("btnSendMessage");
  const btnStopGeneration = document.getElementById("btnStopGeneration");
  const btnQuickUpload = document.getElementById("btnQuickUpload");

  // Modals
  const settingsModal = document.getElementById("settingsModal");
  const btnOpenSettings = document.getElementById("btnOpenSettings");
  const btnCloseSettings = document.getElementById("btnCloseSettings");
  const btnSaveSettings = document.getElementById("btnSaveSettings");
  const btnResetSettings = document.getElementById("btnResetSettings");
  const btnTestOllama = document.getElementById("btnTestOllama");
  const ollamaUrlInput = document.getElementById("ollamaUrlInput");
  const ollamaTestFeedback = document.getElementById("ollamaTestFeedback");
  const temperatureInput = document.getElementById("temperatureInput");
  const tempValueDisplay = document.getElementById("tempValueDisplay");
  const topKInput = document.getElementById("topKInput");
  const topKDisplay = document.getElementById("topKDisplay");
  const thresholdInput = document.getElementById("thresholdInput");
  const thresholdDisplay = document.getElementById("thresholdDisplay");
  const systemPromptInput = document.getElementById("systemPromptInput");

  // Share Modal
  const shareModal = document.getElementById("shareModal");
  const btnCloseShareModal = document.getElementById("btnCloseShareModal");
  const publicShareUrlInput = document.getElementById("publicShareUrlInput");
  const btnCopyPublicUrl = document.getElementById("btnCopyPublicUrl");
  const copyPublicBtnText = document.getElementById("copyPublicBtnText");
  const localShareUrlInput = document.getElementById("localShareUrlInput");
  const btnCopyLocalUrl = document.getElementById("btnCopyLocalUrl");
  const copyLocalBtnText = document.getElementById("copyLocalBtnText");
  const summaryPublicIp = document.getElementById("summaryPublicIp");
  const summaryLocalIp = document.getElementById("summaryLocalIp");
  const guideLocalIp = document.getElementById("guideLocalIp");
  const btnCopyPinggyCmd = document.getElementById("btnCopyPinggyCmd");
  const btnCopyCloudflaredCmd = document.getElementById("btnCopyCloudflaredCmd");
  const btnCopyNgrokCmd = document.getElementById("btnCopyNgrokCmd");

  // Document Reader Modal
  const readerModal = document.getElementById("readerModal");
  const btnCloseReaderModal = document.getElementById("btnCloseReaderModal");
  const readerDocTitle = document.getElementById("readerDocTitle");
  const readerSubjectBadge = document.getElementById("readerSubjectBadge");
  const readerDocStats = document.getElementById("readerDocStats");
  const readerDocDate = document.getElementById("readerDocDate");
  const readerContentBody = document.getElementById("readerContentBody");
  const readerSearchInput = document.getElementById("readerSearchInput");
  const btnReaderDownload = document.getElementById("btnReaderDownload");
  const btnReaderStudyThis = document.getElementById("btnReaderStudyThis");

  let activeReaderDoc = null;
  let rawReaderText = "";

  // Configure marked.js for safe markdown rendering
  if (typeof marked !== "undefined") {
    marked.setOptions({
      breaks: true,
      gfm: true,
      highlight: function (code, lang) {
        if (typeof hljs !== "undefined" && lang && hljs.getLanguage(lang)) {
          try {
            return hljs.highlight(code, { language: lang }).value;
          } catch (e) {}
        }
        return code;
      }
    });
  }

  // Load Settings from LocalStorage
  function loadPersistedSettings() {
    try {
      const saved = localStorage.getItem("study_buddy_settings");
      if (saved) {
        const parsed = JSON.parse(saved);
        if (parsed.selectedModel) {
          if (parsed.selectedModel === "gemini-3.8-flash" || parsed.selectedModel === "gemini-2.5-flash") {
            state.selectedModel = "gemini-3.5-flash-lite";
          } else {
            state.selectedModel = parsed.selectedModel;
          }
        }
        if (parsed.topK) state.topK = parseInt(parsed.topK, 10);
        if (parsed.threshold !== undefined) state.threshold = parseFloat(parsed.threshold);
        if (parsed.temperature !== undefined) state.temperature = parseFloat(parsed.temperature);
        if (parsed.systemPrompt !== undefined) state.systemPrompt = parsed.systemPrompt;
        if (parsed.ragEnabled !== undefined) state.ragEnabled = parsed.ragEnabled;
        if (parsed.studyMode !== undefined) state.studyMode = parsed.studyMode;
      }
    } catch (e) {
      console.warn("Failed to parse saved settings:", e);
    }
  }

  function savePersistedSettings() {
    try {
      const data = {
        selectedModel: state.selectedModel,
        topK: state.topK,
        threshold: state.threshold,
        temperature: state.temperature,
        systemPrompt: state.systemPrompt,
        ragEnabled: state.ragEnabled,
        studyMode: state.studyMode
      };
      localStorage.setItem("study_buddy_settings", JSON.stringify(data));
    } catch (e) {
      console.warn("Failed to persist settings:", e);
    }
  }

  // Setup Light Dismiss for Native Dialogs
  function setupDialogLightDismiss(dialog) {
    if (!dialog) return;
    dialog.addEventListener("click", (e) => {
      const rect = dialog.getBoundingClientRect();
      const isInDialog = (
        rect.top <= e.clientY &&
        e.clientY <= rect.top + rect.height &&
        rect.left <= e.clientX &&
        e.clientX <= rect.left + rect.width
      );
      if (!isInDialog) {
        dialog.close();
      }
    });
  }

  [settingsModal, shareModal, readerModal].forEach(setupDialogLightDismiss);

  // Network Sharing Info
  async function fetchNetworkInfo() {
    try {
      const res = await fetch("/api/network-info");
      if (res.ok) {
        const data = await res.json();
        state.networkInfo = data;
        
        // Header displays Public IP if detected, else Local IP
        if (headerIpText) {
          headerIpText.textContent = data.public_ip ? data.public_ip : data.local_ip;
        }

        // Public Share Input & Summary
        if (publicShareUrlInput) {
          publicShareUrlInput.value = data.public_url || `http://${data.public_ip || "your-public-ip"}:${data.port || 8000}`;
        }
        if (summaryPublicIp) {
          summaryPublicIp.textContent = data.public_ip || "Not detected";
        }
        if (summaryLocalIp) {
          summaryLocalIp.textContent = data.local_ip;
        }
        if (guideLocalIp) {
          guideLocalIp.textContent = data.local_ip;
        }

        // Local Wi-Fi Input
        if (localShareUrlInput) {
          localShareUrlInput.value = data.local_url || `http://${data.local_ip}:${data.port || 8000}`;
        }
      }
    } catch (e) {
      console.warn("Error fetching network info:", e);
    }
  }

  // Open & Close Share Modal
  if (btnShareModalOpen && shareModal) {
    btnShareModalOpen.addEventListener("click", () => {
      fetchNetworkInfo();
      shareModal.showModal();
    });
  }

  if (btnCloseShareModal && shareModal) {
    btnCloseShareModal.addEventListener("click", () => {
      shareModal.close();
    });
  }

  // Share Modal Tab Switching
  const shareTabButtons = document.querySelectorAll(".share-tab-btn");
  shareTabButtons.forEach(btn => {
    btn.addEventListener("click", () => {
      const targetTabId = btn.getAttribute("data-tab");
      shareTabButtons.forEach(b => b.classList.remove("active"));
      btn.classList.add("active");

      document.querySelectorAll(".share-tab-panel").forEach(panel => {
        if (panel.id === targetTabId) {
          panel.classList.add("active");
        } else {
          panel.classList.remove("active");
        }
      });
    });
  });

  // Universal clipboard helper
  async function copyToClipboard(text, feedbackEl, originalText = "Copy Link") {
    try {
      await navigator.clipboard.writeText(text);
      if (feedbackEl) {
        feedbackEl.textContent = "Copied! ✓";
        setTimeout(() => {
          feedbackEl.textContent = originalText;
        }, 2200);
      }
    } catch (err) {
      const fallbackInput = document.createElement("input");
      fallbackInput.value = text;
      document.body.appendChild(fallbackInput);
      fallbackInput.select();
      document.execCommand("copy");
      document.body.removeChild(fallbackInput);
      if (feedbackEl) {
        feedbackEl.textContent = "Copied! ✓";
        setTimeout(() => {
          feedbackEl.textContent = originalText;
        }, 2200);
      }
    }
  }

  // Copy Public Link
  if (btnCopyPublicUrl && publicShareUrlInput) {
    btnCopyPublicUrl.addEventListener("click", () => {
      copyToClipboard(publicShareUrlInput.value, copyPublicBtnText, "Copy Link");
    });
  }

  // Copy Local Wi-Fi Link
  if (btnCopyLocalUrl && localShareUrlInput) {
    btnCopyLocalUrl.addEventListener("click", () => {
      copyToClipboard(localShareUrlInput.value, copyLocalBtnText, "Copy Link");
    });
  }

  // Copy Tunnel Commands
  if (btnCopyPinggyCmd) {
    btnCopyPinggyCmd.addEventListener("click", () => {
      const cmd = document.getElementById("pinggyCmdText")?.textContent || "ssh -p 443 -R0:localhost:8000 a.pinggy.io";
      copyToClipboard(cmd, btnCopyPinggyCmd, "Copy Command");
    });
  }

  if (btnCopyCloudflaredCmd) {
    btnCopyCloudflaredCmd.addEventListener("click", () => {
      const cmd = document.getElementById("cloudflaredCmdText")?.textContent || "cloudflared tunnel --url http://localhost:8000";
      copyToClipboard(cmd, btnCopyCloudflaredCmd, "Copy Command");
    });
  }

  if (btnCopyNgrokCmd) {
    btnCopyNgrokCmd.addEventListener("click", () => {
      const cmd = document.getElementById("ngrokCmdText")?.textContent || "ngrok http 8000";
      copyToClipboard(cmd, btnCopyNgrokCmd, "Copy Command");
    });
  }

  // Pomodoro Focus Timer
  function updatePomodoroDisplay() {
    const mins = Math.floor(state.pomodoro.timeRemaining / 60);
    const secs = state.pomodoro.timeRemaining % 60;
    pomodoroTime.textContent = `${String(mins).padStart(2, "0")}:${String(secs).padStart(2, "0")}`;
    pomodoroMode.textContent = state.pomodoro.mode;
  }

  function togglePomodoro() {
    if (state.pomodoro.isRunning) {
      // Pause
      clearInterval(state.pomodoro.intervalId);
      state.pomodoro.isRunning = false;
      pomodoroPlayIcon.innerHTML = `<polygon points="5 3 19 12 5 21 5 3"></polygon>`;
    } else {
      // Start
      state.pomodoro.isRunning = true;
      pomodoroPlayIcon.innerHTML = `<rect x="6" y="4" width="4" height="16"></rect><rect x="14" y="4" width="4" height="16"></rect>`;
      state.pomodoro.intervalId = setInterval(() => {
        if (state.pomodoro.timeRemaining > 0) {
          state.pomodoro.timeRemaining--;
          updatePomodoroDisplay();
        } else {
          // Switch Focus / Break
          clearInterval(state.pomodoro.intervalId);
          state.pomodoro.isRunning = false;
          if (state.pomodoro.mode === "Focus") {
            state.pomodoro.mode = "Break";
            state.pomodoro.timeRemaining = 5 * 60;
            alert("⏰ Great focus session! Time for a 5-minute break.");
          } else {
            state.pomodoro.mode = "Focus";
            state.pomodoro.timeRemaining = 25 * 60;
            alert("⏰ Break complete! Ready to study?");
          }
          pomodoroPlayIcon.innerHTML = `<polygon points="5 3 19 12 5 21 5 3"></polygon>`;
          updatePomodoroDisplay();
        }
      }, 1000);
    }
  }

  function resetPomodoro() {
    clearInterval(state.pomodoro.intervalId);
    state.pomodoro.isRunning = false;
    state.pomodoro.mode = "Focus";
    state.pomodoro.timeRemaining = 25 * 60;
    pomodoroPlayIcon.innerHTML = `<polygon points="5 3 19 12 5 21 5 3"></polygon>`;
    updatePomodoroDisplay();
  }

  if (btnPomodoroToggle) btnPomodoroToggle.addEventListener("click", togglePomodoro);
  if (btnPomodoroReset) btnPomodoroReset.addEventListener("click", resetPomodoro);
  updatePomodoroDisplay();

  // Study Modes
  function setStudyMode(mode) {
    state.studyMode = mode;
    studyModeButtons.forEach((btn) => {
      if (btn.dataset.mode === mode) {
        btn.classList.add("active");
      } else {
        btn.classList.remove("active");
      }
    });

    const modeLabels = {
      general: "Discuss",
      explain: "Explain Concept",
      quiz: "Quiz Me",
      flashcards: "Flashcards",
      summarize: "Summarize"
    };
    if (footerStudyMode) {
      footerStudyMode.textContent = `Mode: ${modeLabels[mode] || "Discuss"}`;
    }

    // Update input placeholder hint
    const placeholders = {
      general: "Ask your StudyBuddy anything... (Shift+Enter for new line)",
      explain: "What concept or topic should I explain intuitively?",
      quiz: "What topic or lecture should I generate a practice quiz on?",
      flashcards: "What subject or chapter should I make flashcards for?",
      summarize: "What material or notes should I synthesize a cram sheet for?"
    };
    messageInput.placeholder = placeholders[mode] || placeholders.general;
    savePersistedSettings();
  }

  studyModeButtons.forEach((btn) => {
    btn.addEventListener("click", () => {
      setStudyMode(btn.dataset.mode);
    });
  });

  // Focus Document Badge
  function setFocusDocument(docId, docTitle) {
    state.focusDocId = docId;
    state.focusDocName = docTitle;
    if (focusDocBadge && focusDocName) {
      focusDocName.textContent = docTitle;
      focusDocBadge.classList.remove("hidden");
    }
    renderDocumentsList();
  }

  function clearFocusDocument() {
    state.focusDocId = null;
    state.focusDocName = "";
    if (focusDocBadge) {
      focusDocBadge.classList.add("hidden");
    }
    renderDocumentsList();
  }

  if (btnResetFocusDoc) {
    btnResetFocusDoc.addEventListener("click", clearFocusDocument);
  }

  // System Status & Ollama Connection
  async function checkSystemStatus() {
    try {
      const res = await fetch("/api/status");
      if (res.ok) {
        const data = await res.json();
        const connected = data.ollama?.connected || false;
        state.ollamaConnected = connected;

        if (connected) {
          statusDot.className = "status-dot connected";
          statusText.textContent = `AI Online (${data.ollama.version || "active"})`;
        } else {
          statusDot.className = "status-dot";
          statusText.textContent = "AI Offline (ollama serve)";
        }

        // Update vault stats
        const kb = data.study_library || {};
        if (statDocCount) statDocCount.textContent = kb.document_count || 0;
        if (statChunkCount) statChunkCount.textContent = kb.chunk_count || 0;
        if (statWordCount) statWordCount.textContent = formatWordCount(kb.total_words || 0);
        if (docCountBadge) docCountBadge.textContent = `${kb.document_count || 0} files`;
      }
    } catch (e) {
      statusDot.className = "status-dot";
      statusText.textContent = "Server Offline";
    }
  }

  // Fetch Local & Cloud Models
  async function fetchModels() {
    try {
      const res = await fetch("/api/models");
      if (res.ok) {
        const data = await res.json();
        state.models = data;
        state.cloudKeysConfigured = data.cloud_keys_configured || { gemini: false, openai: false, anthropic: false };
        populateModelDropdowns();
      }
    } catch (e) {
      console.warn("Could not fetch models:", e);
    }
  }

  function populateModelDropdowns() {
    const selects = [headerModelSelect, modalModelSelect];
    selects.forEach((select) => {
      if (!select) return;
      select.innerHTML = "";

      // 1. Local (Ollama) OptGroup
      const localGroup = document.createElement("optgroup");
      localGroup.label = "🏠 Local Models (Ollama Offline)";
      const ollamaList = state.models?.ollama_models || [];
      if (ollamaList.length > 0) {
        ollamaList.forEach((m) => {
          const opt = document.createElement("option");
          opt.value = m.id;
          opt.textContent = m.name;
          opt.dataset.provider = "ollama";
          if (m.id === state.selectedModel) opt.selected = true;
          localGroup.appendChild(opt);
        });
      } else {
        const opt = document.createElement("option");
        opt.value = "qwen2.5:3b";
        opt.textContent = "qwen2.5:3b (Ollama Default)";
        opt.dataset.provider = "ollama";
        localGroup.appendChild(opt);
      }
      select.appendChild(localGroup);

      // 2. Google Gemini OptGroup
      const geminiGroup = document.createElement("optgroup");
      geminiGroup.label = "🌟 Google Gemini (Cloud)";
      const geminiList = state.models?.gemini_models || [];
      geminiList.forEach((m) => {
        const opt = document.createElement("option");
        opt.value = m.id;
        opt.textContent = m.name;
        opt.dataset.provider = "gemini";
        if (m.id === state.selectedModel) opt.selected = true;
        geminiGroup.appendChild(opt);
      });
      select.appendChild(geminiGroup);

      // 3. OpenAI ChatGPT OptGroup
      const openaiGroup = document.createElement("optgroup");
      openaiGroup.label = "⚡ OpenAI / ChatGPT (Cloud)";
      const openaiList = state.models?.openai_models || [];
      openaiList.forEach((m) => {
        const opt = document.createElement("option");
        opt.value = m.id;
        opt.textContent = m.name;
        opt.dataset.provider = "openai";
        if (m.id === state.selectedModel) opt.selected = true;
        openaiGroup.appendChild(opt);
      });
      select.appendChild(openaiGroup);

      // 4. Anthropic Claude OptGroup
      const anthropicGroup = document.createElement("optgroup");
      anthropicGroup.label = "🧠 Anthropic Claude (Cloud)";
      const anthropicList = state.models?.anthropic_models || [];
      anthropicList.forEach((m) => {
        const opt = document.createElement("option");
        opt.value = m.id;
        opt.textContent = m.name;
        opt.dataset.provider = "anthropic";
        if (m.id === state.selectedModel) opt.selected = true;
        anthropicGroup.appendChild(opt);
      });
      select.appendChild(anthropicGroup);
    });

    if (footerActiveModel) {
      footerActiveModel.textContent = `Model: ${state.selectedModel}`;
    }
  }

  function preloadModel(model) {
    if (!model) return;
    const mLower = model.toLowerCase();
    if (mLower.includes("gemini") || mLower.includes("gpt") || mLower.includes("claude")) return;
    fetch("/api/models/preload", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ model: model })
    }).catch(() => {});
  }

  if (headerModelSelect) {
    headerModelSelect.addEventListener("change", (e) => {
      state.selectedModel = e.target.value;
      if (modalModelSelect) modalModelSelect.value = e.target.value;
      if (footerActiveModel) footerActiveModel.textContent = `Model: ${state.selectedModel}`;
      savePersistedSettings();
      preloadModel(state.selectedModel);
    });
  }

  // Fetch & Render Study Documents
  async function fetchDocuments() {
    try {
      const res = await fetch("/api/documents");
      if (res.ok) {
        const data = await res.json();
        state.documents = data.documents || [];
        renderDocumentsList();
        checkSystemStatus();
      }
    } catch (e) {
      console.warn("Could not fetch documents:", e);
    }
  }

  function getSubjectClass(subject) {
    const sub = (subject || "General").toLowerCase();
    if (sub.includes("computer") || sub.includes("cs")) return "cs";
    if (sub.includes("bio")) return "bio";
    if (sub.includes("phys")) return "phys";
    if (sub.includes("math")) return "math";
    if (sub.includes("chem")) return "chem";
    return "gen";
  }

  function getFileIcon(filename) {
    const ext = filename.split(".").pop().toLowerCase();
    if (ext === "pdf") return "📕";
    if (ext === "md" || ext === "markdown") return "📝";
    if (ext === "csv") return "📊";
    if (ext === "json") return "🗂️";
    return "📄";
  }

  function renderDocumentsList() {
    if (!documentsList) return;
    const filterText = (docFilterInput?.value || "").toLowerCase();
    const filterSubject = state.selectedSubjectFilter.toLowerCase();

    const filtered = state.documents.filter((d) => {
      const matchesSearch = (d.filename || "").toLowerCase().includes(filterText) ||
        (d.subject || "").toLowerCase().includes(filterText);
      const matchesSubject = filterSubject === "all" ||
        (d.subject || "General").toLowerCase() === filterSubject;
      return matchesSearch && matchesSubject;
    });

    if (filtered.length === 0) {
      documentsList.innerHTML = `
        <li class="empty-state-item" style="color: var(--text-dim); text-align: center; padding: 24px 12px; font-size: 0.82rem;">
          ${state.documents.length === 0 ? "No documents in the vault yet. Drag & drop or upload notes, PDFs, or slides above to get started!" : "No documents match current filters."}
        </li>
      `;
      return;
    }

    documentsList.innerHTML = "";
    filtered.forEach((doc) => {
      const isFocused = state.focusDocId === doc.id;
      const subClass = getSubjectClass(doc.subject);
      const icon = getFileIcon(doc.filename);
      const formattedSize = formatBytes(doc.file_size || 0);

      const li = document.createElement("li");
      li.className = `doc-item-card ${isFocused ? "focused" : ""}`;
      li.innerHTML = `
        <div class="doc-card-top">
          <div class="doc-title-group">
            <span class="doc-file-icon">${icon}</span>
            <div style="overflow: hidden;">
              <div class="doc-name" title="${escapeHtml(doc.filename)}">${escapeHtml(doc.filename)}</div>
              <div class="doc-meta-row">
                <span>${formattedSize}</span>
                <span>&bull;</span>
                <span>${doc.word_count || 0} words</span>
              </div>
            </div>
          </div>
          <span class="subject-badge ${subClass}">${escapeHtml(doc.subject || "General")}</span>
        </div>
        <div class="doc-card-actions">
          <button type="button" class="card-action-btn btn-read-doc" data-id="${doc.id}" title="Read entire document in browser">
            👁️ Read
          </button>
          <a href="/api/documents/${doc.id}/download" class="card-action-btn" download="${escapeHtml(doc.filename)}" title="Direct download original file to your device">
            ⬇️ Download
          </a>
          <button type="button" class="card-action-btn study-focus btn-focus-doc" data-id="${doc.id}" data-title="${escapeHtml(doc.filename)}" title="Focus StudyBuddy on this document">
            ${isFocused ? "✓ Focused" : "🎯 Study This"}
          </button>
          <button type="button" class="card-action-btn delete btn-delete-doc" data-id="${doc.id}" title="Delete document">
            🗑️
          </button>
        </div>
      `;
      documentsList.appendChild(li);
    });

    // Attach card event listeners
    documentsList.querySelectorAll(".btn-read-doc").forEach((btn) => {
      btn.addEventListener("click", () => openDocumentReader(btn.dataset.id));
    });

    documentsList.querySelectorAll(".btn-focus-doc").forEach((btn) => {
      btn.addEventListener("click", () => {
        if (state.focusDocId === btn.dataset.id) {
          clearFocusDocument();
        } else {
          setFocusDocument(btn.dataset.id, btn.dataset.title);
        }
      });
    });

    documentsList.querySelectorAll(".btn-delete-doc").forEach((btn) => {
      btn.addEventListener("click", () => deleteDocument(btn.dataset.id));
    });
  }

  // Subject Filter Pill Click Handlers
  if (subjectFilterPills) {
    subjectFilterPills.querySelectorAll(".subject-pill").forEach((pill) => {
      pill.addEventListener("click", () => {
        subjectFilterPills.querySelectorAll(".subject-pill").forEach((p) => p.classList.remove("active"));
        pill.classList.add("active");
        state.selectedSubjectFilter = pill.dataset.subject;
        renderDocumentsList();
      });
    });
  }

  if (docFilterInput) {
    docFilterInput.addEventListener("input", renderDocumentsList);
  }

  // In-App Document Reader Modal
  async function openDocumentReader(docId) {
    if (!readerModal) return;
    try {
      readerDocTitle.textContent = "Loading note...";
      readerContentBody.textContent = "Fetching complete document content from vault...";
      readerModal.showModal();

      const res = await fetch(`/api/documents/${docId}/preview`);
      if (res.ok) {
        const data = await res.json();
        activeReaderDoc = data;
        rawReaderText = data.text || "";

        readerDocTitle.textContent = data.filename;
        const subClass = getSubjectClass(data.subject);
        readerSubjectBadge.className = `subject-badge ${subClass}`;
        readerSubjectBadge.textContent = data.subject || "General";
        readerDocStats.textContent = `${data.word_count || 0} words • ${formatBytes(data.file_size || 0)}`;
        readerDocDate.textContent = `Uploaded: ${data.uploaded_at ? data.uploaded_at.substring(0, 10) : "recently"}`;
        
        btnReaderDownload.href = `/api/documents/${docId}/download`;
        btnReaderDownload.setAttribute("download", data.filename);

        renderReaderText(rawReaderText);
      } else {
        readerContentBody.textContent = "Error loading document content from server.";
      }
    } catch (e) {
      readerContentBody.textContent = `Failed to preview document: ${e.message}`;
    }
  }

  function renderReaderText(text) {
    if (!readerContentBody) return;
    const searchVal = (readerSearchInput?.value || "").trim().toLowerCase();
    if (!searchVal) {
      readerContentBody.textContent = text;
      return;
    }

    // Highlight search matches
    const escaped = escapeHtml(text);
    const regex = new RegExp(`(${escapeRegex(searchVal)})`, "gi");
    const highlighted = escaped.replace(regex, `<mark style="background: rgba(245, 158, 11, 0.4); color: #fff; padding: 0 2px; border-radius: 2px;">$1</mark>`);
    readerContentBody.innerHTML = highlighted;
  }

  if (readerSearchInput) {
    readerSearchInput.addEventListener("input", () => {
      renderReaderText(rawReaderText);
    });
  }

  if (btnReaderStudyThis) {
    btnReaderStudyThis.addEventListener("click", () => {
      if (activeReaderDoc) {
        setFocusDocument(activeReaderDoc.id, activeReaderDoc.filename);
        if (readerModal) readerModal.close();
      }
    });
  }

  if (btnCloseReaderModal && readerModal) {
    btnCloseReaderModal.addEventListener("click", () => {
      readerModal.close();
    });
  }

  // Upload Handling with Subject Tagging
  async function handleFileUpload(files) {
    if (!files || files.length === 0) return;
    const selectedSubject = uploadSubjectSelect?.value === "Auto" ? "" : (uploadSubjectSelect?.value || "");

    const formData = new FormData();
    for (let i = 0; i < files.length; i++) {
      formData.append("files", files[i]);
    }
    if (selectedSubject) {
      formData.append("subject", selectedSubject);
    }

    if (uploadProgressContainer) {
      uploadProgressContainer.classList.remove("hidden");
      uploadProgressBar.style.width = "35%";
      uploadProgressText.textContent = "Uploading & extracting text...";
    }

    try {
      uploadProgressBar.style.width = "65%";
      const res = await fetch("/api/upload", {
        method: "POST",
        body: formData
      });

      uploadProgressBar.style.width = "95%";
      if (res.ok) {
        const result = await res.json();
        uploadProgressText.textContent = `Indexed ${result.uploaded?.length || 0} document(s) successfully!`;
        setTimeout(() => {
          if (uploadProgressContainer) uploadProgressContainer.classList.add("hidden");
          uploadProgressBar.style.width = "0%";
        }, 1500);
        await fetchDocuments();
      } else {
        uploadProgressText.textContent = "Upload failed. Please check file format.";
      }
    } catch (e) {
      uploadProgressText.textContent = `Upload error: ${e.message}`;
    }
  }

  if (fileInput) {
    fileInput.addEventListener("change", (e) => {
      handleFileUpload(e.target.files);
      fileInput.value = "";
    });
  }

  if (btnQuickUpload && fileInput) {
    btnQuickUpload.addEventListener("click", () => fileInput.click());
  }

  if (uploadDropzone) {
    uploadDropzone.addEventListener("dragover", (e) => {
      e.preventDefault();
      uploadDropzone.classList.add("dragover");
    });
    uploadDropzone.addEventListener("dragleave", () => {
      uploadDropzone.classList.remove("dragover");
    });
    uploadDropzone.addEventListener("drop", (e) => {
      e.preventDefault();
      uploadDropzone.classList.remove("dragover");
      if (e.dataTransfer.files) {
        handleFileUpload(e.dataTransfer.files);
      }
    });
  }

  // Pre-load Study Packs
  if (btnLoadSamples) {
    btnLoadSamples.addEventListener("click", async () => {
      btnLoadSamples.disabled = true;
      btnLoadSamples.textContent = "⏳ Loading Packs...";
      try {
        const res = await fetch("/api/documents/load-samples", { method: "POST" });
        if (res.ok) {
          await fetchDocuments();
        }
      } catch (e) {
        console.error("Load samples error:", e);
      } finally {
        btnLoadSamples.disabled = false;
        btnLoadSamples.textContent = "✨ Load Study Packs";
      }
    });
  }

  // Clear Vault
  if (btnClearAllDocs) {
    btnClearAllDocs.addEventListener("click", async () => {
      if (!confirm("Are you sure you want to clear all shared documents from the vault?")) return;
      try {
        await fetch("/api/documents/clear", { method: "POST" });
        clearFocusDocument();
        await fetchDocuments();
      } catch (e) {
        console.error("Clear vault error:", e);
      }
    });
  }

  // Delete Document
  async function deleteDocument(docId) {
    if (!confirm("Delete this document from the shared library?")) return;
    try {
      const res = await fetch(`/api/documents/${docId}`, { method: "DELETE" });
      if (res.ok) {
        if (state.focusDocId === docId) clearFocusDocument();
        await fetchDocuments();
      }
    } catch (e) {
      console.error("Delete doc error:", e);
    }
  }

  // Library Grounding Toggle
  if (ragToggle) {
    ragToggle.addEventListener("change", (e) => {
      state.ragEnabled = e.target.checked;
      if (ragToggleTitle) {
        ragToggleTitle.innerHTML = state.ragEnabled
          ? `Library Grounding: <span class="highlight-green">ON</span>`
          : `Library Grounding: <span style="color: var(--text-dim);">OFF</span>`;
      }
      savePersistedSettings();
    });
  }

  // Quick prompt chips
  document.querySelectorAll(".quick-chip").forEach((chip) => {
    chip.addEventListener("click", () => {
      const prefix = chip.dataset.prefix;
      messageInput.value = prefix;
      messageInput.focus();
    });
  });

  // Sample Query Cards
  document.querySelectorAll(".sample-query-card").forEach((card) => {
    card.addEventListener("click", () => {
      const query = card.dataset.query;
      const mode = card.dataset.mode;
      if (mode) setStudyMode(mode);
      if (query) {
        messageInput.value = query;
        sendMessage();
      }
    });
  });

  // Auto-resize Message Input
  if (messageInput) {
    messageInput.addEventListener("input", () => {
      messageInput.style.height = "auto";
      messageInput.style.height = Math.min(messageInput.scrollHeight, 140) + "px";
    });

    messageInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
      }
    });
  }

  if (chatForm) {
    chatForm.addEventListener("submit", (e) => {
      e.preventDefault();
      sendMessage();
    });
  }

  if (btnStopGeneration) {
    btnStopGeneration.addEventListener("click", () => {
      if (state.abortController) {
        state.abortController.abort();
      }
    });
  }

  if (btnClearChat) {
    btnClearChat.addEventListener("click", () => {
      if (confirm("Clear study conversation history?")) {
        chatMessages.innerHTML = "";
        if (welcomeHero) chatMessages.appendChild(welcomeHero);
      }
    });
  }

  // Chat Streaming & Message Handling
  async function sendMessage() {
    const text = messageInput.value.trim();
    if (!text || state.isGenerating) return;

    // Remove welcome hero if present
    if (welcomeHero && welcomeHero.parentNode === chatMessages) {
      welcomeHero.remove();
    }

    // Append User Message
    appendMessage("user", text);
    messageInput.value = "";
    messageInput.style.height = "auto";

    // Prepare Assistant Message Placeholder
    const assistantBubble = appendMessage("assistant", "");
    state.isGenerating = true;
    updateGeneratingState(true);

    state.abortController = new AbortController();

    try {
      // Detect provider
      const mLower = (state.selectedModel || "").toLowerCase();
      let provider = "ollama";
      if (mLower.includes("gemini")) provider = "gemini";
      else if (mLower.includes("gpt-") || mLower.includes("chatgpt")) provider = "openai";
      else if (mLower.includes("claude")) provider = "anthropic";

      const payload = {
        message: text,
        model: state.selectedModel,
        provider: provider,
        study_mode: state.studyMode,
        focus_doc_id: state.focusDocId,
        rag_enabled: state.ragEnabled,
        top_k: state.topK,
        threshold: state.threshold,
        temperature: state.temperature,
        system_prompt: state.systemPrompt
      };

      const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
        signal: state.abortController.signal
      });

      if (!response.ok) {
        throw new Error(`Server returned status ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");
      let fullText = "";
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          const trimmed = line.trim();
          if (!trimmed.startsWith("data:")) continue;
          const jsonStr = trimmed.substring(5).trim();
          if (!jsonStr) continue;

          try {
            const data = JSON.parse(jsonStr);

            if (data.type === "sources") {
              if (data.sources && data.sources.length > 0) {
                renderSourcesDrawer(assistantBubble, data.sources);
              }
            } else if (data.type === "token") {
              fullText += data.token;
              updateAssistantMessage(assistantBubble, fullText);
              chatMessages.scrollTop = chatMessages.scrollHeight;
            } else if (data.type === "done") {
              finalizeAssistantMessage(assistantBubble, fullText);
            }
          } catch (jsonErr) {
            console.warn("SSE JSON parse error:", jsonErr);
          }
        }
      }

      finalizeAssistantMessage(assistantBubble, fullText);
    } catch (e) {
      if (e.name === "AbortError") {
        updateAssistantMessage(assistantBubble, (assistantBubble.dataset.rawText || "") + "\n\n*(Generation stopped by student)*");
      } else {
        updateAssistantMessage(assistantBubble, `⚠️ **Error communicating with StudyBuddy:** ${e.message}\nPlease verify that Ollama is running ('ollama serve') and model is available.`);
      }
    } finally {
      state.isGenerating = false;
      updateGeneratingState(false);
    }
  }

  function updateGeneratingState(isGen) {
    btnSendMessage.classList.toggle("hidden", isGen);
    btnStopGeneration.classList.toggle("hidden", !isGen);
    btnSendMessage.disabled = isGen;
  }

  function appendMessage(sender, content) {
    const msgDiv = document.createElement("div");
    msgDiv.className = `chat-message ${sender}`;

    const avatar = document.createElement("div");
    avatar.className = "message-avatar";
    avatar.textContent = sender === "user" ? "🎓" : "✨";

    const bodyDiv = document.createElement("div");
    bodyDiv.className = "message-body";

    const bubble = document.createElement("div");
    bubble.className = "message-bubble";
    bubble.innerHTML = sender === "user"
      ? escapeHtml(content)
      : `<div class="loading-token-state"><span class="pulsing-spinner">⚡</span> <span>Thinking & generating response...</span></div>`;
    bubble.dataset.rawText = content;

    bodyDiv.appendChild(bubble);
    msgDiv.appendChild(avatar);
    msgDiv.appendChild(bodyDiv);

    chatMessages.appendChild(msgDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    return bubble;
  }

  function updateAssistantMessage(bubble, text) {
    bubble.dataset.rawText = text;
    if (typeof marked !== "undefined") {
      bubble.innerHTML = marked.parse(text);
    } else {
      bubble.textContent = text;
    }
  }

  function finalizeAssistantMessage(bubble, text) {
    updateAssistantMessage(bubble, text);
    if (typeof hljs !== "undefined") {
      bubble.querySelectorAll("pre code").forEach((block) => {
        hljs.highlightElement(block);
      });
    }

    // Add Copy / Quick Action buttons
    const parentBody = bubble.closest(".message-body");
    if (parentBody && !parentBody.querySelector(".msg-action-row")) {
      const actionRow = document.createElement("div");
      actionRow.className = "msg-action-row";
      actionRow.style.display = "flex";
      actionRow.style.gap = "8px";
      actionRow.style.marginTop = "4px";

      const copyBtn = document.createElement("button");
      copyBtn.type = "button";
      copyBtn.className = "card-action-btn";
      copyBtn.style.fontSize = "0.72rem";
      copyBtn.innerHTML = "📋 Copy Answer";
      copyBtn.addEventListener("click", () => {
        navigator.clipboard.writeText(text);
        copyBtn.innerHTML = "✓ Copied!";
        setTimeout(() => (copyBtn.innerHTML = "📋 Copy Answer"), 2000);
      });

      actionRow.appendChild(copyBtn);
      parentBody.appendChild(actionRow);
    }
  }

  function renderSourcesDrawer(bubble, sources) {
    const parentBody = bubble.closest(".message-body");
    if (!parentBody || parentBody.querySelector(".referenced-sources-card")) return;

    const drawer = document.createElement("div");
    drawer.className = "referenced-sources-card";

    const toggleBtn = document.createElement("button");
    toggleBtn.type = "button";
    toggleBtn.className = "sources-toggle-btn";
    toggleBtn.innerHTML = `📚 <span>Referenced ${sources.length} Shared Note(s)</span> <span style="font-size: 0.7rem;">▼</span>`;

    const listDiv = document.createElement("div");
    listDiv.className = "sources-content-list";

    sources.forEach((s) => {
      const chip = document.createElement("div");
      chip.className = "source-item-chip";
      const snippet = s.text.length > 140 ? s.text.substring(0, 140) + "..." : s.text;
      chip.innerHTML = `
        <div class="source-chip-header">
          <span>${escapeHtml(s.filename)} (Subject: ${escapeHtml(s.subject || "General")})</span>
          <span style="color: var(--accent-green); font-size: 0.7rem;">Match ${Math.round(s.score * 100)}%</span>
        </div>
        <div class="source-chip-text">"${escapeHtml(snippet)}"</div>
      `;
      listDiv.appendChild(chip);
    });

    toggleBtn.addEventListener("click", () => {
      const isHidden = listDiv.style.display === "none";
      listDiv.style.display = isHidden ? "flex" : "none";
      toggleBtn.querySelector("span:last-child").textContent = isHidden ? "▼" : "▶";
    });

    drawer.appendChild(toggleBtn);
    drawer.appendChild(listDiv);
    parentBody.insertBefore(drawer, bubble);
  }

  // Settings Modal Handlers
  if (btnOpenSettings && settingsModal) {
    btnOpenSettings.addEventListener("click", async () => {
      ollamaUrlInput.value = state.ollamaUrl;
      temperatureInput.value = state.temperature;
      tempValueDisplay.textContent = state.temperature;
      topKInput.value = state.topK;
      topKDisplay.textContent = state.topK;
      thresholdInput.value = state.threshold;
      thresholdDisplay.textContent = state.threshold;
      systemPromptInput.value = state.systemPrompt;

      // Fetch cloud providers status
      try {
        const res = await fetch("/api/settings");
        if (res.ok) {
          const cfg = await res.json();
          if (cfg.ollama_url) ollamaUrlInput.value = cfg.ollama_url;
          if (cfg.openai_base_url && openaiBaseUrlInput) openaiBaseUrlInput.value = cfg.openai_base_url;

          if (geminiStatusBadge) {
            geminiStatusBadge.textContent = cfg.gemini_configured ? "✓ Configured" : "Key Needed";
            geminiStatusBadge.className = `provider-status-badge ${cfg.gemini_configured ? "connected" : "missing"}`;
            if (cfg.gemini_masked) geminiApiKeyInput.placeholder = `Configured: ${cfg.gemini_masked}`;
          }
          if (openaiStatusBadge) {
            openaiStatusBadge.textContent = cfg.openai_configured ? "✓ Configured" : "Key Needed";
            openaiStatusBadge.className = `provider-status-badge ${cfg.openai_configured ? "connected" : "missing"}`;
            if (cfg.openai_masked) openaiApiKeyInput.placeholder = `Configured: ${cfg.openai_masked}`;
          }
          if (anthropicStatusBadge) {
            anthropicStatusBadge.textContent = cfg.anthropic_configured ? "✓ Configured" : "Key Needed";
            anthropicStatusBadge.className = `provider-status-badge ${cfg.anthropic_configured ? "connected" : "missing"}`;
            if (cfg.anthropic_masked) anthropicApiKeyInput.placeholder = `Configured: ${cfg.anthropic_masked}`;
          }
        }
      } catch (e) {
        console.warn("Could not fetch settings:", e);
      }

      settingsModal.showModal();
    });
  }

  if (btnCloseSettings && settingsModal) {
    btnCloseSettings.addEventListener("click", () => settingsModal.close());
  }

  if (temperatureInput) {
    temperatureInput.addEventListener("input", (e) => {
      tempValueDisplay.textContent = e.target.value;
    });
  }
  if (topKInput) {
    topKInput.addEventListener("input", (e) => {
      topKDisplay.textContent = e.target.value;
    });
  }
  if (thresholdInput) {
    thresholdInput.addEventListener("input", (e) => {
      thresholdDisplay.textContent = e.target.value;
    });
  }

  if (btnTestOllama) {
    btnTestOllama.addEventListener("click", async () => {
      btnTestOllama.disabled = true;
      ollamaTestFeedback.textContent = "Testing connection...";
      try {
        const res = await fetch("/api/settings", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ ollama_url: ollamaUrlInput.value.trim() })
        });
        if (res.ok) {
          const data = await res.json();
          if (data.health?.connected) {
            ollamaTestFeedback.textContent = `Connected! Ollama version: ${data.health.version}`;
            ollamaTestFeedback.style.color = "var(--accent-green)";
          } else {
            ollamaTestFeedback.textContent = `Unreachable: ${data.health?.error || "Check server address"}`;
            ollamaTestFeedback.style.color = "var(--accent-danger)";
          }
        }
      } catch (e) {
        ollamaTestFeedback.textContent = `Error: ${e.message}`;
        ollamaTestFeedback.style.color = "var(--accent-danger)";
      } finally {
        btnTestOllama.disabled = false;
      }
    });
  }

  // Test Cloud API Keys
  if (btnTestGemini) {
    btnTestGemini.addEventListener("click", async () => {
      btnTestGemini.disabled = true;
      if (geminiTestFeedback) {
        geminiTestFeedback.textContent = "Testing Gemini key & latency...";
        geminiTestFeedback.style.color = "var(--text-muted)";
      }
      try {
        const res = await fetch("/api/settings/test-key", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            provider: "gemini",
            api_key: geminiApiKeyInput ? geminiApiKeyInput.value.trim() : undefined
          })
        });
        const data = await res.json();
        if (data.success) {
          geminiTestFeedback.textContent = data.message;
          geminiTestFeedback.style.color = "var(--accent-green)";
          if (geminiStatusBadge) {
            geminiStatusBadge.textContent = "Active";
            geminiStatusBadge.className = "provider-status-badge configured";
          }
        } else {
          geminiTestFeedback.textContent = data.message;
          geminiTestFeedback.style.color = "var(--accent-danger)";
        }
      } catch (err) {
        if (geminiTestFeedback) {
          geminiTestFeedback.textContent = `Error: ${err.message}`;
          geminiTestFeedback.style.color = "var(--accent-danger)";
        }
      } finally {
        btnTestGemini.disabled = false;
      }
    });
  }

  if (btnTestOpenAI) {
    btnTestOpenAI.addEventListener("click", async () => {
      btnTestOpenAI.disabled = true;
      if (openaiTestFeedback) {
        openaiTestFeedback.textContent = "Testing OpenAI key & quota...";
        openaiTestFeedback.style.color = "var(--text-muted)";
      }
      try {
        const res = await fetch("/api/settings/test-key", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            provider: "openai",
            api_key: openaiApiKeyInput ? openaiApiKeyInput.value.trim() : undefined,
            base_url: openaiBaseUrlInput ? openaiBaseUrlInput.value.trim() : undefined
          })
        });
        const data = await res.json();
        if (data.success) {
          openaiTestFeedback.textContent = data.message;
          openaiTestFeedback.style.color = "var(--accent-green)";
          if (openaiStatusBadge) {
            openaiStatusBadge.textContent = "Active";
            openaiStatusBadge.className = "provider-status-badge configured";
          }
        } else {
          openaiTestFeedback.textContent = data.message;
          openaiTestFeedback.style.color = data.code === "credit_balance_exhausted" ? "#f59e0b" : "var(--accent-danger)";
        }
      } catch (err) {
        if (openaiTestFeedback) {
          openaiTestFeedback.textContent = `Error: ${err.message}`;
          openaiTestFeedback.style.color = "var(--accent-danger)";
        }
      } finally {
        btnTestOpenAI.disabled = false;
      }
    });
  }

  if (btnTestAnthropic) {
    btnTestAnthropic.addEventListener("click", async () => {
      btnTestAnthropic.disabled = true;
      if (anthropicTestFeedback) {
        anthropicTestFeedback.textContent = "Testing Claude key...";
        anthropicTestFeedback.style.color = "var(--text-muted)";
      }
      try {
        const res = await fetch("/api/settings/test-key", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            provider: "anthropic",
            api_key: anthropicApiKeyInput ? anthropicApiKeyInput.value.trim() : undefined
          })
        });
        const data = await res.json();
        if (data.success) {
          anthropicTestFeedback.textContent = data.message;
          anthropicTestFeedback.style.color = "var(--accent-green)";
          if (anthropicStatusBadge) {
            anthropicStatusBadge.textContent = "Active";
            anthropicStatusBadge.className = "provider-status-badge configured";
          }
        } else {
          anthropicTestFeedback.textContent = data.message;
          anthropicTestFeedback.style.color = "var(--accent-danger)";
        }
      } catch (err) {
        if (anthropicTestFeedback) {
          anthropicTestFeedback.textContent = `Error: ${err.message}`;
          anthropicTestFeedback.style.color = "var(--accent-danger)";
        }
      } finally {
        btnTestAnthropic.disabled = false;
      }
    });
  }

  if (btnSaveSettings) {
    btnSaveSettings.addEventListener("click", async () => {
      state.ollamaUrl = ollamaUrlInput.value.trim();
      state.selectedModel = modalModelSelect.value;
      headerModelSelect.value = state.selectedModel;
      state.temperature = parseFloat(temperatureInput.value);
      state.topK = parseInt(topKInput.value, 10);
      state.threshold = parseFloat(thresholdInput.value);
      state.systemPrompt = systemPromptInput.value.trim();

      const payload = {
        ollama_url: state.ollamaUrl
      };
      if (geminiApiKeyInput && geminiApiKeyInput.value.trim()) {
        payload.gemini_api_key = geminiApiKeyInput.value.trim();
      }
      if (openaiApiKeyInput && openaiApiKeyInput.value.trim()) {
        payload.openai_api_key = openaiApiKeyInput.value.trim();
      }
      if (openaiBaseUrlInput && openaiBaseUrlInput.value.trim()) {
        payload.openai_base_url = openaiBaseUrlInput.value.trim();
      }
      if (anthropicApiKeyInput && anthropicApiKeyInput.value.trim()) {
        payload.anthropic_api_key = anthropicApiKeyInput.value.trim();
      }

      try {
        const res = await fetch("/api/settings", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });
        if (res.ok) {
          const data = await res.json();
          state.cloudKeysConfigured = data.cloud_keys_configured || state.cloudKeysConfigured;
          await fetchModels();
        }
      } catch (e) {
        console.warn("Error saving settings:", e);
      }

      savePersistedSettings();
      if (footerActiveModel) footerActiveModel.textContent = `Model: ${state.selectedModel}`;
      settingsModal.close();
    });
  }

  if (btnResetSettings) {
    btnResetSettings.addEventListener("click", () => {
      ollamaUrlInput.value = "http://localhost:11434";
      temperatureInput.value = "0.7";
      tempValueDisplay.textContent = "0.7";
      topKInput.value = "4";
      topKDisplay.textContent = "4";
      thresholdInput.value = "0.05";
      thresholdDisplay.textContent = "0.05";
      systemPromptInput.value = "";
    });
  }

  // Utilities
  function escapeHtml(text) {
    if (!text) return "";
    return String(text)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  function escapeRegex(string) {
    return string.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  }

  function formatBytes(bytes) {
    if (!bytes || bytes === 0) return "0 B";
    const k = 1024;
    const sizes = ["B", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + " " + sizes[i];
  }

  function formatWordCount(words) {
    if (!words || words === 0) return "0";
    if (words >= 1000000) return (words / 1000000).toFixed(1) + "M";
    if (words >= 1000) return (words / 1000).toFixed(1) + "k";
    return words.toString();
  }

  // Initialization
  loadPersistedSettings();
  fetchNetworkInfo();
  checkSystemStatus();
  fetchModels();
  fetchDocuments();
  setStudyMode(state.studyMode);

  // Poll status periodically (every 15s)
  setInterval(() => {
    checkSystemStatus();
  }, 15000);
});
