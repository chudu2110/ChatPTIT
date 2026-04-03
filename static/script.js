const chatBox = document.getElementById("chat-box")
const scrollArea = document.getElementById("chat-scroll-area")
const emptyState = document.getElementById("empty-state")
const emptyTitleEl = document.getElementById("empty-title")
const emptySubtitleEl = document.getElementById("empty-subtitle")
const emptyComposerSlot = document.getElementById("empty-composer-slot")
const activeChatTitleEl = document.getElementById("active-chat-title")

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

function renderMessageItem(msg, { animate = false } = {}) {
  if (!chatBox) return null
  const wrapper = document.createElement("div")

  if (msg.role === "user") {
    wrapper.className = "flex justify-end"
    const bubble = document.createElement("div")
    bubble.className = "max-w-[85%] whitespace-pre-wrap rounded-2xl border border-gray-200 bg-gray-100 px-4 py-2 text-sm text-gray-900"
    bubble.textContent = msg.content || ""
    wrapper.appendChild(bubble)
    chatBox.appendChild(wrapper)
    return { wrapper, bubble }
  }

  wrapper.className = "flex justify-start"

  const bubble = document.createElement("div")
  bubble.className = "markdown max-w-[85%] whitespace-pre-wrap px-1 py-1 text-sm text-gray-900"
  const text = msg.content || ""

  wrapper.appendChild(bubble)
  chatBox.appendChild(wrapper)

  if (!animate) {
    bubble.innerHTML = marked.parse(text)
    return { wrapper, bubble }
  }

  bubble.innerHTML = ""
  let i = 0
  const chunk = 3
  const tick = 10
  function type() {
    if (i < text.length) {
      const partial = text.slice(0, i)
      bubble.innerHTML = marked.parse(partial)
      i += chunk
      scrollBottom()
      setTimeout(type, tick)
      return
    }
    bubble.innerHTML = marked.parse(text)
    scrollBottom()
  }
  type()

  return { wrapper, bubble }
}

function renderTypingAssistant() {
  const msg = { role: "assistant", content: "" }
  const item = renderMessageItem(msg, { animate: false })
  if (!item?.bubble) return null
  item.bubble.innerHTML = `
    <div class="flex items-center gap-2 text-gray-400">
      <span class="spinner" aria-hidden="true"></span>
    </div>
  `
  return item
}

function renderActiveChat() {
  if (!chatBox) return
  chatBox.innerHTML = ""
  const messages = getActiveMessages()
  setEmptyStateVisible(messages.length === 0)
  for (const msg of messages) renderMessageItem(msg, { animate: false })
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
  if (sendBtn) sendBtn.disabled = sending
  if (messageInput) messageInput.disabled = sending
}

function autoResizeTextarea() {
  if (!messageInput) return
  messageInput.style.height = "0px"
  messageInput.style.height = Math.min(messageInput.scrollHeight, 192) + "px"
}

async function sendMessage() {
  if (isSending) return
  const message = (messageInput?.value || "").trim()
  if (!message) return

  setSending(true)
  updateChatTitleFromFirstMessage(message)

  const messages = getActiveMessages()
  messages.push({ role: "user", content: message, createdAt: nowIso() })
  setActiveMessages(messages)

  renderMessageItem({ role: "user", content: message }, { animate: false })
  setEmptyStateVisible(false)
  scrollBottom()

  if (messageInput) {
    messageInput.value = ""
    autoResizeTextarea()
  }

  const typingItem = renderTypingAssistant()
  scrollBottom()
  const loadingStart = typeof performance !== "undefined" && typeof performance.now === "function" ? performance.now() : Date.now()
  await new Promise((r) => requestAnimationFrame(r))
  await sleep(150)

  try {
    const session_id = getSessionIdForServer()
    const res = await fetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, session_id }),
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
    renderMessageItem(finalMsg, { animate: true })
    scrollBottom()
  } catch (e) {
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
    setSending(false)
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
