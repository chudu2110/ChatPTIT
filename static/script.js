const chatBox = document.getElementById("chat-box")
const scrollArea = document.getElementById("chat-scroll-area")
const emptyState = document.getElementById("empty-state")
const emptyTitleEl = document.getElementById("empty-title")
const emptySubtitleEl = document.getElementById("empty-subtitle")
const emptyComposerSlot = document.getElementById("empty-composer-slot")
const activeChatTitleEl = document.getElementById("active-chat-title")

const ICONS = {
  copy: `<svg width="14" height="14" viewBox="0 0 24 24" fill="none"><path d="M8 4v12a2 2 0 002 2h8a2 2 0 002-2V7.242a2 2 0 00-.602-1.43L17.43 4.602A2 2 0 0016 4H8z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><path d="M16 4H8a2 2 0 00-2 2v12a2 2 0 002 2M16 4V4a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>`,
  good: `<svg width="14" height="14" viewBox="0 0 24 24" fill="none"><path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>`,
  bad: `<svg width="14" height="14" viewBox="0 0 24 24" fill="none"><path d="M10 15v4a3 3 0 0 0 3 3l4-9V2H5.72a2 2 0 0 0-2 1.7l-1.38 9a2 2 0 0 0 2 2.3zM17 2h3a2 2 0 0 1 2 2v7a2 2 0 0 1-2 2h-3" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>`,
  share: `<svg width="14" height="14" viewBox="0 0 24 24" fill="none"><path d="M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8M16 6l-4-4-4 4M12 2v13" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>`,
  retry: `<svg width="14" height="14" viewBox="0 0 24 24" fill="none"><path d="M1 4v6h6M23 20v-6h-6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><path d="M20.49 9A9 9 0 0 0 5.64 5.64L1 10m22 4l-4.64 4.36A9 9 0 0 1 3.51 15" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>`,
  more: `<svg width="14" height="14" viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="1" fill="currentColor"/><circle cx="19" cy="12" r="1" fill="currentColor"/><circle cx="5" cy="12" r="1" fill="currentColor"/></svg>`,
  branch: `<svg width="14" height="14" viewBox="0 0 24 24" fill="none"><path d="M6 3v12M18 9a3 3 0 1 0 0-6 3 3 0 0 0 0 6zM6 21a3 3 0 1 0 0-6 3 3 0 0 0 0 6zM18 21a3 3 0 1 0 0-6 3 3 0 0 0 0 6z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><path d="M18 15V9a9 9 0 0 0-9 9" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>`,
  speaker: `<svg width="14" height="14" viewBox="0 0 24 24" fill="none"><path d="M11 5L6 9H2v6h4l5 4V5z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>`,
  pause: `<svg width="14" height="14" viewBox="0 0 24 24" fill="none"><rect x="6" y="4" width="4" height="16" rx="1" fill="currentColor"/><rect x="14" y="4" width="4" height="16" rx="1" fill="currentColor"/></svg>`,
  stop: `<svg width="14" height="14" viewBox="0 0 24 24" fill="none"><rect x="7" y="7" width="10" height="10" rx="1.5" fill="currentColor"/></svg>`,
}

let currentSpeechMsgIndex = -1
let isSpeechPaused = false

const sidebar = document.getElementById("sidebar")
const mobileOverlay = document.getElementById("mobile-overlay")
const sidebarToggleBtn = document.getElementById("sidebar-toggle")
const sidebarCollapseBtn = document.getElementById("sidebar-collapse-btn")
const sidebarLogoBtn = document.getElementById("sidebar-logo-btn")

const chatList = document.getElementById("chat-list")
const chatSearch = document.getElementById("chat-search")
const chatSearchToggleBtn = document.getElementById("chat-search-toggle")
const chatSearchPanel = document.getElementById("chat-search-panel")
const newChatBtn = document.getElementById("new-chat-btn")
const clearChatBtn = document.getElementById("clear-chat-btn")

const messageInput = document.getElementById("message")
const sendBtn = document.getElementById("send-btn")
const footerEl = document.getElementById("footer")
const footerComposerSlot = document.getElementById("footer-composer-slot")
const composerEl = document.getElementById("composer")

const STORAGE_KEY_CHATS = "ptit_chat_chats_v1"
const STORAGE_KEY_ACTIVE = "ptit_chat_active_id_v1"
const STORAGE_KEY_SIDEBAR_COLLAPSED = "ptit_sidebar_collapsed_v1"
const LEGACY_SESSION_KEY = "ptit_chat_session_id"
const MSG_KEY_PREFIX = "ptit_chat_messages_v1_"

const APP_TITLE = "ChatPTIT"
const NEW_CHAT_TITLE = "Cuộc trò chuyện mới"
const TEMP_MODE_TITLE = "Trò chuyện tạm thời"
const TEMP_MODE_DESC =
  "Cuộc trò chuyện này sẽ không xuất hiện trong lịch sử trò chuyện của bạn và sẽ không được sử dụng để huấn luyện mô hình của chúng tôi."

let chats = []
let activeChatId = null
let isSending = false
let tempMode = false
let tempChatId = null
let tempMessages = []
let sidebarCollapsed = false
let editingMessageIndex = -1

let abortController = null
let currentTypewriterTimeout = null

function setClasses(el, add = [], remove = []) {
  if (!el) return
  for (const c of remove) el.classList.remove(c)
  for (const c of add) el.classList.add(c)
}

function runTempAnnouncementAnimation() {
  if (!emptyTitleEl) return
  const els = [emptyTitleEl, emptySubtitleEl].filter(Boolean)
  for (const el of els) el.classList.remove("temp-announce")
  void emptyTitleEl.offsetWidth
  for (const el of els) el.classList.add("temp-announce")
}

function updateComposerTheme() {
  const dark = tempMode
  setClasses(
    composerEl,
    dark ? ["bg-black/90", "border-gray-800", "shadow-none", "focus-within:ring-gray-600"] : ["bg-white/95", "border-gray-200", "shadow-lg", "shadow-gray-200/60", "focus-within:ring-gray-300", "hover:shadow-xl"],
    dark ? ["bg-white/95", "border-gray-200", "shadow-lg", "shadow-gray-200/60", "focus-within:ring-gray-300", "hover:shadow-xl"] : ["bg-black/90", "border-gray-800", "shadow-none", "focus-within:ring-gray-600"]
  )

  setClasses(
    messageInput,
    dark ? ["text-gray-100", "placeholder:text-gray-500"] : [],
    dark ? ["placeholder:text-gray-400"] : ["text-gray-100", "placeholder:text-gray-500"]
  )
  if (!dark && messageInput) messageInput.classList.add("placeholder:text-gray-400")

  if (document?.body) document.body.classList.toggle("temp-mode", dark)

  if (composerEl) {
    composerEl.style.backgroundColor = dark ? "rgba(0,0,0,0.94)" : ""
    composerEl.style.borderColor = dark ? "#1f2937" : ""
    composerEl.style.boxShadow = dark ? "none" : ""
  }

  if (sendBtn) {
    sendBtn.style.backgroundColor = dark ? "#ffffff" : ""
    sendBtn.style.color = dark ? "#000000" : ""
  }

  const sendSvg = sendBtn?.querySelector("svg")
  if (sendSvg) {
    sendSvg.style.color = dark ? "#000000" : ""
  }

  const sendPaths = sendBtn?.querySelectorAll("path") || []
  for (const p of sendPaths) {
    p.style.setProperty("stroke", dark ? "#000000" : "", "important")
    p.style.setProperty("fill", dark ? "none" : "", "important")
  }
}

function updateEmptyStateText() {
  if (!emptyTitleEl) return
  if (tempMode) {
    emptyTitleEl.textContent = TEMP_MODE_TITLE
    if (emptySubtitleEl) {
      emptySubtitleEl.textContent = TEMP_MODE_DESC
      emptySubtitleEl.classList.remove("hidden")
    }
    runTempAnnouncementAnimation()
    return
  }
  if (emptySubtitleEl) {
    emptySubtitleEl.textContent = ""
    emptySubtitleEl.classList.add("hidden")
  }
  setRandomEmptyGreeting()
}

function safeParseJson(raw, fallback) {
  try {
    const v = JSON.parse(raw)
    return v ?? fallback
  } catch {
    return fallback
  }
}

function loadJson(key, fallback) {
  return safeParseJson(localStorage.getItem(key), fallback)
}

function saveJson(key, value) {
  localStorage.setItem(key, JSON.stringify(value))
}

function nowIso() {
  return new Date().toISOString()
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

function genId() {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") return crypto.randomUUID()
  return Math.random().toString(36).slice(2) + Math.random().toString(36).slice(2)
}

function getMessagesKey(chatId) {
  return `${MSG_KEY_PREFIX}${chatId}`
}

function loadMessages(chatId) {
  return loadJson(getMessagesKey(chatId), [])
}

function saveMessages(chatId, messages) {
  saveJson(getMessagesKey(chatId), messages)
}

function updateTempModeUI() {
  if (clearChatBtn) {
    clearChatBtn.setAttribute("aria-pressed", tempMode ? "true" : "false")
    clearChatBtn.setAttribute("aria-label", tempMode ? TEMP_MODE_TITLE : "Bật trò chuyện tạm thời")
    clearChatBtn.style.setProperty("--dasharray", tempMode ? "4 3" : "0")
    clearChatBtn.classList.toggle("bg-gray-100", tempMode)
    clearChatBtn.title = tempMode ? TEMP_MODE_TITLE : "Bật trò chuyện tạm thời"
  }
  updateComposerTheme()
  if (emptyState && !emptyState.classList.contains("hidden")) updateEmptyStateText()
}

function getActiveMessages() {
  if (tempMode) return tempMessages
  return loadMessages(activeChatId)
}

function setActiveMessages(messages) {
  if (tempMode) {
    tempMessages = messages
    return
  }
  saveMessages(activeChatId, messages)
}

function getSessionIdForServer() {
  if (tempMode) return tempChatId
  return activeChatId
}

function loadChats() {
  chats = loadJson(STORAGE_KEY_CHATS, [])
  activeChatId = localStorage.getItem(STORAGE_KEY_ACTIVE)
  let changed = false
  for (const c of chats) {
    if (!c) continue
    if (!c.title || c.title === "New chat") {
      c.title = NEW_CHAT_TITLE
      changed = true
    }
  }
  if (changed) saveJson(STORAGE_KEY_CHATS, chats)
}

function saveChats() {
  saveJson(STORAGE_KEY_CHATS, chats)
  if (activeChatId) localStorage.setItem(STORAGE_KEY_ACTIVE, activeChatId)
}

function normalizeTitle(title) {
  const t = (title || "").trim()
  return t ? t : NEW_CHAT_TITLE
}

function truncateTitle(title, maxLen = 36) {
  const t = normalizeTitle(title)
  if (t.length <= maxLen) return t
  return t.slice(0, maxLen - 1) + "…"
}

function ensureInitialChat() {
  if (chats.length > 0 && activeChatId && chats.some(c => c.id === activeChatId)) return

  if (chats.length > 0) {
    activeChatId = chats[0].id
    saveChats()
    return
  }

  const legacy = localStorage.getItem(LEGACY_SESSION_KEY)
  const chatId = legacy || genId()

  const chat = {
    id: chatId,
    title: NEW_CHAT_TITLE,
    createdAt: nowIso(),
    updatedAt: nowIso(),
  }
  chats = [chat]
  activeChatId = chat.id
  saveChats()
}

function setRandomEmptyGreeting() {
  if (!emptyTitleEl) return
  const greetings = [
    "Bạn muốn làm gì tiếp theo?",
    "Bạn cần trao đổi về vấn đề gì?",
    "Bạn đang tìm thông tin gì?",
    "Sẵn sàng khi bạn cần hỗ trợ.",
    "Chúng ta nên bắt đầu từ đâu nhỉ?",
  ]
  emptyTitleEl.textContent = greetings[Math.floor(Math.random() * greetings.length)]
}

function updateComposerPlacement(showInEmpty) {
  if (!composerEl) return

  if (showInEmpty) {
    if (emptyComposerSlot && composerEl.parentElement !== emptyComposerSlot) emptyComposerSlot.appendChild(composerEl)
    if (footerEl) footerEl.classList.add("hidden")
    if (messageInput) messageInput.rows = 1
  } else {
    if (footerComposerSlot && composerEl.parentElement !== footerComposerSlot) footerComposerSlot.appendChild(composerEl)
    if (footerEl) footerEl.classList.remove("hidden")
    if (messageInput) messageInput.rows = 1
  }
  autoResizeTextarea()
}

function setEmptyStateVisible(visible) {
  if (!emptyState) return
  emptyState.classList.toggle("hidden", !visible)
  updateComposerPlacement(visible)
  if (visible) updateEmptyStateText()
}

function scrollBottom() {
  if (!scrollArea) return
  scrollArea.scrollTop = scrollArea.scrollHeight
}

function formatAnswer(text) {
  const t = text || ""
  if (!t.includes("Nguồn:")) return t
  const parts = t.split("Nguồn:")
  const answer = parts[0].trimEnd()
  const sources = (parts[1] || "").split(",").map(s => s.trim()).filter(Boolean)

  let md = answer + "\n\n---\n**Nguồn tham khảo:**\n"
  for (const s of sources) md += `- ${s}\n`
  return md
}

function closeMobileSidebar() {
  if (!sidebar || !mobileOverlay) return
  if (window.matchMedia("(min-width: 768px)").matches) return
  sidebar.classList.add("hidden")
  sidebar.classList.remove("flex")
  mobileOverlay.classList.add("hidden")
}

function openMobileSidebar() {
  if (!sidebar || !mobileOverlay) return
  if (window.matchMedia("(min-width: 768px)").matches) return
  sidebar.classList.remove("hidden")
  sidebar.classList.add("flex")
  mobileOverlay.classList.remove("hidden")
}

function isDesktopSidebar() {
  return window.matchMedia("(min-width: 768px)").matches
}

function setSearchPanelOpen(open) {
  if (!chatSearchPanel || !chatSearchToggleBtn) return
  chatSearchPanel.classList.toggle("hidden", !open)
  chatSearchToggleBtn.setAttribute("aria-expanded", open ? "true" : "false")
}

function openSearchPanel() {
  setSearchPanelOpen(true)
  chatSearch?.focus()
}

function closeSearchPanelIfEmpty() {
  const q = (chatSearch?.value || "").trim()
  if (q) return
  setSearchPanelOpen(false)
}

function updateSidebarCollapseButton() {
  if (!sidebarCollapseBtn) return
  const label = sidebarCollapsed ? "Mở rộng sidebar" : "Thu gọn sidebar"
  sidebarCollapseBtn.setAttribute("aria-label", label)
  sidebarCollapseBtn.title = label
  const svg = sidebarCollapseBtn.querySelector("svg")
  if (svg) {
    svg.innerHTML = sidebarCollapsed
      ? `<path d="M9 18l6-6-6-6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>`
      : `<path d="M15 18 9 12l6-6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>`
  }
}

function updateSidebarLogoButton() {
  if (!sidebarLogoBtn) return
  const label = sidebarCollapsed && isDesktopSidebar() ? "Mở rộng sidebar" : "PTIT"
  sidebarLogoBtn.setAttribute("aria-label", label)
  sidebarLogoBtn.title = label
}

function applySidebarCollapsedState() {
  if (!sidebar) return
  if (!isDesktopSidebar()) {
    sidebar.classList.remove("sidebar-collapsed")
    updateSidebarCollapseButton()
    updateSidebarLogoButton()
    return
  }
  sidebar.classList.toggle("sidebar-collapsed", sidebarCollapsed)
  updateSidebarCollapseButton()
  updateSidebarLogoButton()
}

function setSidebarCollapsed(collapsed) {
  sidebarCollapsed = !!collapsed
  localStorage.setItem(STORAGE_KEY_SIDEBAR_COLLAPSED, sidebarCollapsed ? "1" : "0")
  setSearchPanelOpen(false)
  applySidebarCollapsedState()
}

function loadSidebarState() {
  sidebarCollapsed = localStorage.getItem(STORAGE_KEY_SIDEBAR_COLLAPSED) === "1"
  applySidebarCollapsedState()
}

function renderChatList(filterText = "") {
  if (!chatList) return
  chatList.innerHTML = ""

  const q = (filterText || "").trim().toLowerCase()
  const filtered = q
    ? chats.filter(c => (c.title || "").toLowerCase().includes(q))
    : chats

  if (filtered.length === 0) {
    const empty = document.createElement("div")
    empty.className = "px-3 py-3 text-xs text-gray-500"
    empty.textContent = "Không có hội thoại phù hợp."
    chatList.appendChild(empty)
    return
  }

  const sectionTitle = document.createElement("div")
  sectionTitle.className = "sidebar-text px-3 pb-1 pt-2 text-xs font-semibold text-gray-500"
  sectionTitle.textContent = "Lịch sử chat"
  chatList.appendChild(sectionTitle)

  for (const chat of filtered) {
    const row = document.createElement("div")
    row.className = "group flex cursor-pointer items-center gap-2 rounded-xl px-3 py-2 hover:bg-gray-100"
    if (!tempMode && chat.id === activeChatId) row.classList.add("bg-gray-100")
    row.title = truncateTitle(chat.title)
    row.onclick = () => {
      if (tempMode) exitTempMode()
      setActiveChat(chat.id)
      closeMobileSidebar()
    }

    const icon = document.createElement("div")
    icon.className = "grid h-8 w-8 place-items-center rounded-lg text-gray-500 group-hover:text-gray-800"
    icon.setAttribute("aria-hidden", "true")
    icon.innerHTML = `
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
        <path d="M21 15a4 4 0 0 1-4 4H8l-5 3V7a4 4 0 0 1 4-4h10a4 4 0 0 1 4 4v8Z" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/>
      </svg>
    `

    const titleBtn = document.createElement("button")
    titleBtn.className = "sidebar-text min-w-0 flex-1 truncate text-left text-sm"
    titleBtn.textContent = truncateTitle(chat.title)
    titleBtn.type = "button"
    titleBtn.onclick = (e) => {
      e.stopPropagation()
      row.onclick?.()
    }

    const delBtn = document.createElement("button")
    delBtn.className = "chat-delete-btn hidden rounded-lg p-1 text-gray-500 hover:bg-white hover:text-gray-900 group-hover:block"
    delBtn.setAttribute("aria-label", "Delete chat")
    delBtn.innerHTML = `
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
        <path d="M6 7h12M10 7V5h4v2m-7 0 1 14h8l1-14" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
    `
    delBtn.onclick = (e) => {
      e.stopPropagation()
      deleteChat(chat.id)
    }

    row.appendChild(icon)
    row.appendChild(titleBtn)
    row.appendChild(delBtn)
    chatList.appendChild(row)
  }
}

function setHeaderTitle() {
  if (!activeChatTitleEl) return
  activeChatTitleEl.textContent = APP_TITLE
}

function renderMessageItem(msg, { animate = false, onComplete = null, index = -1 } = {}) {
  if (!chatBox) return null
  const wrapper = document.createElement("div")
  if (index !== -1) wrapper.dataset.index = String(index)

  if (msg.role === "user") {
    if (index !== -1 && index === editingMessageIndex) {
      wrapper.className = "flex w-full flex-col items-end mb-4"
      
      const editBubble = document.createElement("div")
      editBubble.className = "edit-bubble w-full max-w-[85%]"
      
      const textarea = document.createElement("textarea")
      textarea.className = "edit-textarea"
      textarea.value = msg.content
      
      const actions = document.createElement("div")
      actions.className = "edit-actions"
      
      const cancelBtn = document.createElement("button")
      cancelBtn.className = "btn-pill btn-pill-white"
      cancelBtn.textContent = "Cancel"
      cancelBtn.onclick = cancelEdit
      
      const sendBtn = document.createElement("button")
      sendBtn.className = "btn-pill btn-pill-black"
      sendBtn.textContent = "Send"
      sendBtn.onclick = () => saveEdit(textarea.value)
      
      actions.appendChild(cancelBtn)
      actions.appendChild(sendBtn)
      editBubble.appendChild(textarea)
      editBubble.appendChild(actions)
      wrapper.appendChild(editBubble)
      chatBox.appendChild(wrapper)
      
      setTimeout(() => {
        textarea.focus()
        textarea.setSelectionRange(textarea.value.length, textarea.value.length)
        textarea.style.height = "auto"
        textarea.style.height = textarea.scrollHeight + "px"
      }, 0)
      
      textarea.oninput = () => {
        textarea.style.height = "auto"
        textarea.style.height = textarea.scrollHeight + "px"
      }

      textarea.onkeydown = (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
          e.preventDefault()
          saveEdit(textarea.value)
        }
        if (e.key === "Escape") cancelEdit()
      }

      if (onComplete) onComplete()
      return { wrapper, bubble: textarea }
    }

    wrapper.className = "user-msg-wrapper flex flex-col items-end gap-1"
    
    const bubble = document.createElement("div")
    bubble.className = "max-w-[85%] whitespace-pre-wrap rounded-2xl border border-gray-200 bg-gray-100 px-4 py-2 text-sm text-gray-900"
    bubble.textContent = msg.content || ""
    
    const actions = document.createElement("div")
    actions.className = "user-msg-actions flex items-center gap-1 pr-1"
    
    const copyBtn = document.createElement("button")
    copyBtn.className = "rounded-lg p-1 text-gray-400 transition hover:bg-gray-100 hover:text-gray-600"
    copyBtn.title = "Sao chép"
    copyBtn.innerHTML = `
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
        <path d="M8 4v12a2 2 0 002 2h8a2 2 0 002-2V7.242a2 2 0 00-.602-1.43L17.43 4.602A2 2 0 0016 4H8z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        <path d="M16 4H8a2 2 0 00-2 2v12a2 2 0 002 2M16 4V4a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
    `
    copyBtn.onclick = () => copyToClipboard(msg.content, copyBtn)

    const editBtn = document.createElement("button")
    editBtn.className = "rounded-lg p-1 text-gray-400 transition hover:bg-gray-100 hover:text-gray-600"
    editBtn.title = "Sửa"
    editBtn.innerHTML = `
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
        <path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
    `
    editBtn.onclick = () => enterEditMode(index)

    actions.appendChild(copyBtn)
    actions.appendChild(editBtn)
    
    wrapper.appendChild(bubble)
    wrapper.appendChild(actions)
    chatBox.appendChild(wrapper)
    
    if (onComplete) onComplete()
    return { wrapper, bubble }
  }

  wrapper.className = "assistant-msg-wrapper flex flex-col items-start gap-1"

  const bubble = document.createElement("div")
  bubble.className = "markdown max-w-[85%] whitespace-pre-wrap px-1 py-1 text-sm text-gray-900"
  const text = msg.content || ""

  const actions = document.createElement("div")
  actions.className = "assistant-msg-actions flex items-center gap-1 pl-1"
  if (animate) actions.classList.add("is-typing")

  const copyBtn = document.createElement("button")
  copyBtn.className = "rounded-lg p-1 text-gray-400 transition hover:bg-gray-100 hover:text-gray-600"
  copyBtn.title = "Sao chép"
  copyBtn.innerHTML = ICONS.copy
  copyBtn.onclick = () => copyToClipboard(msg.content, copyBtn)

  const goodBtn = document.createElement("button")
  goodBtn.className = "rating-btn rounded-lg p-1 text-gray-400 transition hover:bg-gray-100 hover:text-gray-600"
  goodBtn.title = "Tốt"
  goodBtn.innerHTML = ICONS.good
  if (msg.rating === "good") goodBtn.classList.add("active")
  goodBtn.onclick = () => rateMessage(index, "good", goodBtn)

  const badBtn = document.createElement("button")
  badBtn.className = "rating-btn rounded-lg p-1 text-gray-400 transition hover:bg-gray-100 hover:text-gray-600"
  badBtn.title = "Xấu"
  badBtn.innerHTML = ICONS.bad
  if (msg.rating === "bad") badBtn.classList.add("active")
  badBtn.onclick = () => rateMessage(index, "bad", badBtn)

  const shareBtn = document.createElement("button")
  shareBtn.className = "rounded-lg p-1 text-gray-400 transition hover:bg-gray-100 hover:text-gray-600"
  shareBtn.title = "Chia sẻ"
  shareBtn.innerHTML = ICONS.share
  shareBtn.onclick = () => shareMessage(index)

  const retryBtn = document.createElement("button")
  retryBtn.className = "rounded-lg p-1 text-gray-400 transition hover:bg-gray-100 hover:text-gray-600"
  retryBtn.title = "Thử lại"
  retryBtn.innerHTML = ICONS.retry
  retryBtn.onclick = () => retryGeneration(index)

  const moreContainer = document.createElement("div")
  moreContainer.className = "relative"

  const moreBtn = document.createElement("button")
  moreBtn.className = "rounded-lg p-1 text-gray-400 transition hover:bg-gray-100 hover:text-gray-600"
  moreBtn.title = "Thêm"
  moreBtn.innerHTML = ICONS.more
  
  const moreMenu = document.createElement("div")
  moreMenu.className = "dropdown-menu"
  
  const branchItem = document.createElement("button")
  branchItem.className = "dropdown-item"
  branchItem.innerHTML = `${ICONS.branch}<span>Sang trang mới</span>`
  branchItem.onclick = (e) => {
    e.stopPropagation()
    branchInNewChat(index)
    moreMenu.classList.remove("show")
  }

  const readAloudItem = document.createElement("button")
  readAloudItem.className = "dropdown-item"
  const isReadingThis = currentSpeechMsgIndex === index
  if (isReadingThis) {
    readAloudItem.classList.add("is-reading")
    const label = isSpeechPaused ? "Tiếp tục đọc" : "Tạm dừng đọc"
    const icon = isSpeechPaused ? ICONS.speaker : ICONS.stop
    readAloudItem.innerHTML = `${icon}<span>${label}</span>`
  } else {
    readAloudItem.innerHTML = `${ICONS.speaker}<span>Đọc tin nhắn</span>`
  }
  
  readAloudItem.onclick = (e) => {
    e.stopPropagation()
    const wrapperEl = readAloudItem.closest(".assistant-msg-wrapper")
    const bubbleEl = wrapperEl?.querySelector(".markdown")
    const displayed = (bubbleEl?.innerText || "").trim()
    readAloud(displayed || msg.content, index)
    moreMenu.classList.remove("show")
  }

  moreMenu.appendChild(branchItem)
  moreMenu.appendChild(readAloudItem)
  moreContainer.appendChild(moreBtn)
  moreContainer.appendChild(moreMenu)

  moreBtn.onclick = (e) => {
    e.stopPropagation()
    const isShown = moreMenu.classList.contains("show")
    document.querySelectorAll(".dropdown-menu.show").forEach(m => m.classList.remove("show"))
    if (!isShown) moreMenu.classList.add("show")
  }

  actions.appendChild(copyBtn)
  actions.appendChild(goodBtn)
  actions.appendChild(badBtn)
  actions.appendChild(shareBtn)
  actions.appendChild(retryBtn)
  actions.appendChild(moreContainer)

  wrapper.appendChild(bubble)
  wrapper.appendChild(actions)
  chatBox.appendChild(wrapper)

  if (!animate) {
    bubble.innerHTML = marked.parse(text)
    if (onComplete) onComplete()
    return { wrapper, bubble }
  }

  bubble.innerHTML = ""
  let i = 0
  const chunk = 3
  const tick = 10
  function type() {
    if (currentTypewriterTimeout === "STOPPED") {
      actions.classList.remove("is-typing")
      currentTypewriterTimeout = null
      if (onComplete) onComplete()
      return
    }

    if (i < text.length) {
      const partial = text.slice(0, i)
      bubble.innerHTML = marked.parse(partial)
      i += chunk
      scrollBottom()
      currentTypewriterTimeout = setTimeout(type, tick)
      return
    }
    bubble.innerHTML = marked.parse(text)
    currentTypewriterTimeout = null
    actions.classList.remove("is-typing")
    scrollBottom()
    if (onComplete) onComplete()
  }
  type()

  return { wrapper, bubble }
}

function renderTypingAssistant() {
  if (!chatBox) return null
  const wrapper = document.createElement("div")
  wrapper.className = "assistant-msg-wrapper flex flex-col items-start gap-1"
  
  const loadingContainer = document.createElement("div")
  loadingContainer.className = "px-4 py-2"
  loadingContainer.innerHTML = `
    <div class="flex items-center gap-2 text-gray-400">
      <span class="spinner" aria-hidden="true"></span>
    </div>
  `
  wrapper.appendChild(loadingContainer)
  chatBox.appendChild(wrapper)
  return { wrapper }
}

function renderActiveChat() {
  if (!chatBox) return
  chatBox.innerHTML = ""
  const messages = getActiveMessages()
  setEmptyStateVisible(messages.length === 0)
  messages.forEach((msg, idx) => {
    renderMessageItem(msg, { animate: false, index: idx })
  })
  setHeaderTitle()
  requestAnimationFrame(scrollBottom)
}

function setActiveChat(chatId) {
  if (!chatId) return
  if (!chats.some(c => c.id === chatId)) return
  activeChatId = chatId
  saveChats()
  renderChatList(chatSearch?.value || "")
  renderActiveChat()
}

function createNewChat() {
  if (tempMode) exitTempMode()
  const chat = { id: genId(), title: NEW_CHAT_TITLE, createdAt: nowIso(), updatedAt: nowIso() }
  chats = [chat, ...chats]
  activeChatId = chat.id
  saveChats()
  renderChatList(chatSearch?.value || "")
  renderActiveChat()
  closeMobileSidebar()
  focusInput()
}

function enterTempMode() {
  if (tempMode) return
  tempMode = true
  tempChatId = `temp_${genId()}`
  tempMessages = []
  updateTempModeUI()
  renderChatList(chatSearch?.value || "")
  renderActiveChat()
  focusInput()
}

function exitTempMode() {
  if (!tempMode) return
  tempMode = false
  tempChatId = null
  tempMessages = []
  updateTempModeUI()
  renderChatList(chatSearch?.value || "")
  renderActiveChat()
  focusInput()
}

function toggleTempMode() {
  if (tempMode) exitTempMode()
  else enterTempMode()
}

function deleteChat(chatId) {
  const idx = chats.findIndex(c => c.id === chatId)
  if (idx === -1) return

  chats.splice(idx, 1)
  localStorage.removeItem(getMessagesKey(chatId))

  if (activeChatId === chatId) {
    if (chats.length > 0) activeChatId = chats[0].id
    else createNewChat()
  }

  saveChats()
  renderChatList(chatSearch?.value || "")
  renderActiveChat()
}

function clearActiveChat() {
  if (!activeChatId) return
  saveMessages(activeChatId, [])
  const chat = chats.find(c => c.id === activeChatId)
  if (chat) {
    chat.title = NEW_CHAT_TITLE
    chat.updatedAt = nowIso()
    saveChats()
  }
  renderChatList(chatSearch?.value || "")
  renderActiveChat()
  focusInput()
}

function focusInput() {
  if (!messageInput) return
  messageInput.focus()
}

function updateChatTitleFromFirstMessage(text) {
  if (tempMode) return
  const chat = chats.find(c => c.id === activeChatId)
  if (!chat) return
  const current = normalizeTitle(chat.title)
  if (current !== NEW_CHAT_TITLE && current !== APP_TITLE && current !== "New chat") return
  chat.title = truncateTitle(text.replace(/\s+/g, " ").trim(), 36)
  chat.updatedAt = nowIso()
  saveChats()
  renderChatList(chatSearch?.value || "")
  setHeaderTitle()
}

function setSending(sending) {
  isSending = sending
  if (sendBtn) {
    if (sending) {
      sendBtn.classList.add("is-loading")
      sendBtn.setAttribute("aria-label", "Dừng")
    } else {
      sendBtn.classList.remove("is-loading")
      sendBtn.setAttribute("aria-label", "Gửi")
    }
    // Không disable nút khi đang gửi để có thể nhấn dừng
    sendBtn.disabled = false
  }
  if (messageInput) messageInput.disabled = sending
}

function autoResizeTextarea() {
  if (!messageInput) return
  messageInput.style.height = "0px"
  messageInput.style.height = Math.min(messageInput.scrollHeight, 192) + "px"
}

function stopGeneration() {
  if (abortController) {
    abortController.abort()
    abortController = null
  }
  // We don't clearTimeout here, because we want the next 'type' tick 
  // to see the "STOPPED" state and call onComplete to resolve the Promise.
  currentTypewriterTimeout = "STOPPED"
  const typingActions = document.querySelector(".assistant-msg-actions.is-typing")
  const typingWrapper = typingActions?.closest(".assistant-msg-wrapper")
  const typingIndexRaw = typingWrapper?.dataset?.index
  const typingIndex = typingIndexRaw ? Number(typingIndexRaw) : -1
  if (typingWrapper && Number.isInteger(typingIndex) && typingIndex >= 0) {
    const bubbleEl = typingWrapper.querySelector(".markdown")
    const displayed = (bubbleEl?.innerText || "").trim()
    if (displayed) {
      const messages = getActiveMessages()
      const msg = messages[typingIndex]
      if (msg && msg.role === "assistant") {
        msg.content = displayed
        setActiveMessages(messages)
      }
    }
  }
  document.querySelectorAll(".assistant-msg-actions.is-typing").forEach(el => el.classList.remove("is-typing"))
  document.querySelectorAll(".assistant-msg-wrapper .spinner").forEach(sp => sp.closest(".assistant-msg-wrapper")?.remove())
  setSending(false)
}

function copyToClipboard(text, btn) {
  navigator.clipboard.writeText(text).then(() => {
    if (!btn) return
    const originalSvg = btn.innerHTML
    btn.innerHTML = `
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
        <path d="M5 13l4 4L19 7" stroke="#10b981" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
    `
    setTimeout(() => {
      btn.innerHTML = originalSvg
    }, 2000)
  })
}

function enterEditMode(index) {
  editingMessageIndex = index
  renderActiveChat()
}

function rateMessage(index, rating, btn) {
  const messages = getActiveMessages()
  if (index < 0 || index >= messages.length) return
  
  const msg = messages[index]
  const isSelected = msg.rating === rating
  
  // Reset all ratings in this message's actions
  const wrapper = btn.closest(".assistant-msg-actions")
  if (wrapper) {
    wrapper.querySelectorAll(".rating-btn").forEach(b => b.classList.remove("active"))
  }
  
  if (isSelected) {
    msg.rating = null
  } else {
    msg.rating = rating
    btn.classList.add("active")
  }
  
  setActiveMessages(messages)
}

function shareMessage(index) {
  const messages = getActiveMessages()
  if (index < 0 || index >= messages.length) return
  const text = messages[index].content
  
  if (navigator.share) {
    navigator.share({
      title: "PTIT Chat Answer",
      text: text,
      url: window.location.href
    }).catch(console.error)
  } else {
    // Fallback to copy link
    copyToClipboard(window.location.href, null)
    alert("Đã sao chép liên kết vào bộ nhớ tạm.")
  }
}

async function retryGeneration(index) {
  const messages = getActiveMessages()
  if (index < 0 || index >= messages.length) return
  
  const assistantMsg = messages[index]
  const rating = assistantMsg.rating || null
  
  // Find the user message before this assistant message
  let userMsgIndex = -1
  for (let i = index - 1; i >= 0; i--) {
    if (messages[i].role === "user") {
      userMsgIndex = i
      break
    }
  }
  
  if (userMsgIndex === -1) return
  
  const userText = messages[userMsgIndex].content
  
  // Remove everything from the assistant message onwards
  messages.splice(index)
  setActiveMessages(messages)
  
  renderActiveChat()
  await sendMessage(userText, true, rating)
}

function branchInNewChat(index) {
  const messages = getActiveMessages()
  if (index < 0 || index >= messages.length) return
  
  const msg = messages[index]
  const newChatId = genId()
  const newChat = {
    id: newChatId,
    title: truncateTitle(msg.content.slice(0, 30)),
    createdAt: nowIso(),
    updatedAt: nowIso()
  }
  
  chats = [newChat, ...chats]
  saveChats()
  
  // Add the message to the new chat
  saveMessages(newChatId, [{
    role: "assistant",
    content: msg.content,
    createdAt: nowIso()
  }])
  
  setActiveChat(newChatId)
  closeMobileSidebar()
}

function readAloud(text, index) {
  if (!window.speechSynthesis) return
  
  // Nếu đang đọc chính tin nhắn này, nhấn lại để tạm dừng/tiếp tục
  if (window.speechSynthesis.speaking && currentSpeechMsgIndex === index) {
    if (isSpeechPaused) {
      window.speechSynthesis.resume()
      isSpeechPaused = false
    } else {
      window.speechSynthesis.pause()
      isSpeechPaused = true
    }
    renderActiveChat()
    return
  }

  // Nếu đọc tin nhắn khác hoặc chưa đọc, hủy cái cũ và bắt đầu mới
  window.speechSynthesis.cancel()
  isSpeechPaused = false
  
  const utterance = new SpeechSynthesisUtterance(text)
  utterance.lang = "vi-VN"
  
  utterance.onstart = () => {
    currentSpeechMsgIndex = index
    renderActiveChat()
  }
  
  utterance.onend = () => {
    currentSpeechMsgIndex = -1
    isSpeechPaused = false
    renderActiveChat()
  }
  
  utterance.onerror = () => {
    currentSpeechMsgIndex = -1
    isSpeechPaused = false
    renderActiveChat()
  }
  
  window.speechSynthesis.speak(utterance)
}

function cancelEdit() {
  editingMessageIndex = -1
  renderActiveChat()
}

async function saveEdit(newText) {
  newText = (newText || "").trim()
  if (!newText || editingMessageIndex === -1) {
    cancelEdit()
    return
  }

  const messages = getActiveMessages()
  
  // Xóa tất cả tin nhắn từ vị trí đang sửa trở đi
  messages.splice(editingMessageIndex)
  setActiveMessages(messages)
  
  editingMessageIndex = -1
  
  // Re-render chat to remove deleted messages from UI
  renderActiveChat()
  
  // Gửi tin nhắn mới với animation
  await sendMessage(newText, true)
}

async function sendMessage(overrideMessage = null, isEdit = false, rating = null) {
  if (isSending) {
    stopGeneration()
    return
  }
  const message = overrideMessage !== null ? overrideMessage : (messageInput?.value || "").trim()
  if (!message) return

  setSending(true)
  updateChatTitleFromFirstMessage(message)

  const messages = getActiveMessages()
  messages.push({ role: "user", content: message, createdAt: nowIso() })
  setActiveMessages(messages)

  const { wrapper } = renderMessageItem({ role: "user", content: message }, { 
    animate: false, 
    index: messages.length - 1 
  })
  
  if (isEdit && wrapper) {
    wrapper.classList.add("animate-fly-in")
  }
  
  setEmptyStateVisible(false)
  scrollBottom()

  if (!overrideMessage && messageInput) {
    messageInput.value = ""
    autoResizeTextarea()
  }

  const typingItem = renderTypingAssistant()
  scrollBottom()
  const loadingStart = typeof performance !== "undefined" && typeof performance.now === "function" ? performance.now() : Date.now()
  await new Promise((r) => requestAnimationFrame(r))
  await sleep(150)

  try {
    abortController = new AbortController()
    const session_id = getSessionIdForServer()
    const res = await fetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, session_id, rating }),
      signal: abortController.signal
    })

    const data = await res.json()
    const text = formatAnswer(data?.response || "")

    const finalMsg = { role: "assistant", content: text, createdAt: nowIso() }
    const updated = getActiveMessages()
    updated.push(finalMsg)
    setActiveMessages(updated)

    const now = typeof performance !== "undefined" && typeof performance.now === "function" ? performance.now() : Date.now()
    const remaining = 650 - (now - loadingStart)
    if (remaining > 0) await sleep(remaining)

    if (typingItem?.wrapper) typingItem.wrapper.remove()
    
    // Check if stopped before starting animation
    if (!isSending) return

    currentTypewriterTimeout = null // Reset before starting new typewriter
    
    await new Promise(resolve => {
      renderMessageItem(finalMsg, { 
        animate: true, 
        onComplete: resolve,
        index: updated.length - 1 // Truyền index vào đây
      })
    })
    scrollBottom()
  } catch (e) {
    if (e.name === "AbortError") {
      if (typingItem?.wrapper) typingItem.wrapper.remove()
      return
    }
    const errText = "Có lỗi khi kết nối server. Vui lòng thử lại."
    const finalMsg = { role: "assistant", content: errText, createdAt: nowIso() }
    const updated = getActiveMessages()
    updated.push(finalMsg)
    setActiveMessages(updated)

    const now = typeof performance !== "undefined" && typeof performance.now === "function" ? performance.now() : Date.now()
    const remaining = 650 - (now - loadingStart)
    if (remaining > 0) await sleep(remaining)

    if (typingItem?.wrapper) typingItem.wrapper.remove()
    renderMessageItem(finalMsg, { animate: false })
    scrollBottom()
  } finally {
    if (isSending) setSending(false)
    abortController = null
    focusInput()
  }
}

function bindEvents() {
  if (sidebarToggleBtn) sidebarToggleBtn.addEventListener("click", openMobileSidebar)
  if (mobileOverlay) mobileOverlay.addEventListener("click", closeMobileSidebar)
  if (sidebarCollapseBtn) {
    sidebarCollapseBtn.addEventListener("click", () => setSidebarCollapsed(!sidebarCollapsed))
  }
  if (sidebarLogoBtn) {
    sidebarLogoBtn.addEventListener("click", () => {
      if (!isDesktopSidebar()) return
      if (!sidebarCollapsed) return
      setSidebarCollapsed(false)
    })
  }
  window.addEventListener("resize", applySidebarCollapsedState)

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") closeMobileSidebar()
    if (e.key === "Escape") closeSearchPanelIfEmpty()
    if (e.key === "Escape") document.querySelectorAll(".dropdown-menu.show").forEach(m => m.classList.remove("show"))
  })

  document.addEventListener("click", (e) => {
    if (!e.target.closest(".relative")) {
      document.querySelectorAll(".dropdown-menu.show").forEach(m => m.classList.remove("show"))
    }
  })

  if (newChatBtn) newChatBtn.addEventListener("click", createNewChat)
  if (clearChatBtn) clearChatBtn.addEventListener("click", toggleTempMode)

  if (chatSearchToggleBtn) {
    chatSearchToggleBtn.addEventListener("click", () => {
      if (sidebarCollapsed && isDesktopSidebar()) {
        setSidebarCollapsed(false)
        requestAnimationFrame(openSearchPanel)
        return
      }
      const open = chatSearchPanel ? chatSearchPanel.classList.contains("hidden") : true
      setSearchPanelOpen(open)
      if (open) chatSearch?.focus()
    })
  }

  if (chatSearch) {
    chatSearch.addEventListener("input", () => renderChatList(chatSearch.value))
    chatSearch.addEventListener("focus", () => setSearchPanelOpen(true))
    chatSearch.addEventListener("blur", () => setTimeout(closeSearchPanelIfEmpty, 120))
  }

  if (sendBtn) sendBtn.addEventListener("click", sendMessage)
  if (messageInput) {
    messageInput.addEventListener("input", autoResizeTextarea)
    messageInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault()
        sendMessage()
      }
    })
  }
}

function init() {
  loadChats()
  ensureInitialChat()
  loadSidebarState()
  setRandomEmptyGreeting()
  updateTempModeUI()
  bindEvents()
  renderChatList("")
  renderActiveChat()
  autoResizeTextarea()
  focusInput()
}

init()
