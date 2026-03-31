/**
 * app.js — AarogyaBot Frontend Logic
 * Handles voice recording, API communication, chat display, and dashboard.
 */

// ═══════════════════════════════════════════════════════════════════════════
// STATE & REFERENCES
// ═══════════════════════════════════════════════════════════════════════════

// Session ID persists across interactions in the same page visit
const SESSION_ID = generateSessionId();

// DOM references
const chatContainer = document.getElementById("chat-container");
const recordBtn = document.getElementById("record-btn");
const statusDot = document.getElementById("status-dot");
const statusText = document.getElementById("status-text");
const languageSelect = document.getElementById("language-select");
const responseAudio = document.getElementById("response-audio");
const tabBtns = document.querySelectorAll(".tab-btn");

// Recording state
let mediaRecorder = null;
let audioChunks = [];
let isRecording = false;


// ═══════════════════════════════════════════════════════════════════════════
// SESSION ID GENERATOR
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Generate a simple unique session ID.
 * Format: "sess_" + random hex string
 */
function generateSessionId() {
    const arr = new Uint8Array(6);
    crypto.getRandomValues(arr);
    return "sess_" + Array.from(arr, b => b.toString(16).padStart(2, "0")).join("");
}


// ═══════════════════════════════════════════════════════════════════════════
// TAB NAVIGATION
// ═══════════════════════════════════════════════════════════════════════════

tabBtns.forEach(btn => {
    btn.addEventListener("click", () => {
        // Update active tab button
        tabBtns.forEach(b => b.classList.remove("active"));
        btn.classList.add("active");

        // Show corresponding content
        const tabName = btn.dataset.tab;
        document.querySelectorAll(".tab-content").forEach(section => {
            section.classList.remove("active");
        });
        document.getElementById(`${tabName}-section`).classList.add("active");

        // Load dashboard data when switching to dashboard tab
        if (tabName === "dashboard") {
            loadDashboard();
        }
    });
});


// ═══════════════════════════════════════════════════════════════════════════
// VOICE RECORDING
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Toggle recording on/off when the mic button is clicked.
 */
recordBtn.addEventListener("click", async () => {
    if (isRecording) {
        stopRecording();
    } else {
        await startRecording();
    }
});

/**
 * Start recording audio from the user's microphone.
 */
async function startRecording() {
    try {
        // Request microphone access
        const stream = await navigator.mediaDevices.getUserMedia({
            audio: {
                channelCount: 1,        // Mono audio is sufficient
                sampleRate: 16000,      // 16kHz works well with Whisper
            }
        });

        // Create MediaRecorder — try webm/opus first (best browser support)
        const mimeType = MediaRecorder.isTypeSupported("audio/webm;codecs=opus")
            ? "audio/webm;codecs=opus"
            : "audio/webm";

        mediaRecorder = new MediaRecorder(stream, { mimeType });
        audioChunks = [];

        // Collect audio data chunks
        mediaRecorder.ondataavailable = (event) => {
            if (event.data.size > 0) {
                audioChunks.push(event.data);
            }
        };

        // When recording stops, process the audio
        mediaRecorder.onstop = () => {
            const audioBlob = new Blob(audioChunks, { type: mimeType });
            stream.getTracks().forEach(track => track.stop()); // Release mic
            sendAudioToServer(audioBlob);
        };

        mediaRecorder.start();
        isRecording = true;

        // Update UI to recording state
        recordBtn.classList.add("recording");
        statusDot.className = "recording";
        statusText.textContent = "🔴 Recording... Tap to stop";

    } catch (err) {
        console.error("Microphone error:", err);
        statusText.textContent = "❌ Microphone access denied. Please allow mic access.";
    }
}

/**
 * Stop the current recording.
 */
function stopRecording() {
    if (mediaRecorder && mediaRecorder.state !== "inactive") {
        mediaRecorder.stop();
        isRecording = false;

        // Update UI
        recordBtn.classList.remove("recording");
        statusDot.className = "processing";
        statusText.textContent = "⏳ Processing your voice...";
    }
}


// ═══════════════════════════════════════════════════════════════════════════
// API COMMUNICATION
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Send the recorded audio to the backend /chat endpoint.
 * @param {Blob} audioBlob - The recorded audio data
 */
async function sendAudioToServer(audioBlob) {
    try {
        // Disable record button while processing
        recordBtn.classList.add("disabled");

        // Show loading message in chat
        const loadingId = addLoadingMessage();

        // Prepare form data
        const formData = new FormData();
        formData.append("audio", audioBlob, "recording.webm");
        formData.append("session_id", SESSION_ID);

        const selectedLang = languageSelect.value;
        if (selectedLang) {
            formData.append("language", selectedLang);
        }

        // Send to backend
        const response = await fetch("/chat", {
            method: "POST",
            body: formData,
        });

        // Remove loading message
        removeLoadingMessage(loadingId);

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || "Server error");
        }

        const data = await response.json();

        // Display user's transcribed text
        addMessage("user", data.user_text);

        // Display bot response with urgency and tool calls
        addBotResponse(data.bot_response, data.urgency, data.tool_calls);

        // Play audio response
        if (data.audio_url) {
            playAudioResponse(data.audio_url);
        }

        // Reset status
        statusDot.className = "";
        statusText.textContent = "Ready — Tap mic to speak";

    } catch (err) {
        console.error("Chat error:", err);
        statusDot.className = "";
        statusText.textContent = `❌ Error: ${err.message}`;
        addMessage("bot", `Sorry, an error occurred: ${err.message}. Please try again. 🙏`);
    } finally {
        recordBtn.classList.remove("disabled");
    }
}


// ═══════════════════════════════════════════════════════════════════════════
// CHAT DISPLAY
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Add a message bubble to the chat.
 * @param {"user"|"bot"} role
 * @param {string} text
 */
function addMessage(role, text) {
    const msgDiv = document.createElement("div");
    msgDiv.className = `message ${role}-message`;

    const avatar = role === "user" ? "🗣️" : "🤖";

    msgDiv.innerHTML = `
        <div class="message-avatar">${avatar}</div>
        <div class="message-content">
            <p>${escapeHtml(text)}</p>
        </div>
    `;

    chatContainer.appendChild(msgDiv);
    scrollToBottom();
}

/**
 * Add a bot response with urgency badge and optional tool call results.
 */
function addBotResponse(text, urgency, toolCalls) {
    const msgDiv = document.createElement("div");
    msgDiv.className = "message bot-message";

    let toolHtml = "";
    if (toolCalls && toolCalls.length > 0) {
        toolHtml = toolCalls.map(tc => formatToolResult(tc)).join("");
    }

    const urgencyLabels = {
        low: "Low Urgency",
        medium: "Medium Urgency",
        high: "⚠️ High Urgency"
    };

    msgDiv.innerHTML = `
        <div class="message-avatar">🤖</div>
        <div class="message-content">
            <p>${escapeHtml(text)}</p>
            ${toolHtml}
            <span class="urgency-badge ${urgency}">${urgencyLabels[urgency] || urgency}</span>
        </div>
    `;

    chatContainer.appendChild(msgDiv);
    scrollToBottom();
}

/**
 * Format a tool call result for display.
 */
function formatToolResult(toolCall) {
    if (toolCall.tool === "find_nearby_clinics" && toolCall.result && toolCall.result.clinics) {
        const clinics = toolCall.result.clinics.map(c => `
            <div class="clinic-item">
                <div class="clinic-name">🏥 ${escapeHtml(c.name)}</div>
                <div class="clinic-details">
                    ${escapeHtml(c.specialty)} · ${escapeHtml(c.address)}<br>
                    📞 ${escapeHtml(c.phone)} · ⭐ ${c.rating}
                </div>
            </div>
        `).join("");

        return `<div class="tool-result"><h4>📍 Nearby Clinics</h4>${clinics}</div>`;
    }

    if (toolCall.tool === "send_sms_alert") {
        return `<div class="tool-result"><h4>📱 SMS Alert Sent</h4>
            <p>To: ${escapeHtml(toolCall.result.to || "N/A")}</p>
            <p style="font-size:0.75rem;color:var(--text-muted);">(Simulated)</p>
        </div>`;
    }

    if (toolCall.tool === "escalate_emergency") {
        return `<div class="tool-result"><h4>🚨 Emergency Escalated</h4>
            <p>Ambulance: ${escapeHtml(toolCall.result.ambulance_id || "N/A")}</p>
            <p>ETA: ${toolCall.result.eta_minutes || "?"} minutes</p>
            <p>📞 Emergency: ${escapeHtml(toolCall.result.emergency_number || "108")}</p>
            <p style="font-size:0.75rem;color:var(--text-muted);">(Simulated)</p>
        </div>`;
    }

    return "";
}

/**
 * Add a loading indicator while processing.
 */
function addLoadingMessage() {
    const id = "loading-" + Date.now();
    const msgDiv = document.createElement("div");
    msgDiv.id = id;
    msgDiv.className = "message bot-message loading-message";
    msgDiv.innerHTML = `
        <div class="message-avatar">🤖</div>
        <div class="message-content">
            <span>Processing</span>
            <div class="loading-dots">
                <span></span><span></span><span></span>
            </div>
        </div>
    `;
    chatContainer.appendChild(msgDiv);
    scrollToBottom();
    return id;
}

/**
 * Remove the loading indicator.
 */
function removeLoadingMessage(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
}

/**
 * Play the TTS audio response.
 */
function playAudioResponse(audioUrl) {
    responseAudio.src = audioUrl;
    responseAudio.play().catch(err => {
        console.warn("Audio autoplay blocked:", err);
    });
}

/**
 * Scroll chat to the bottom.
 */
function scrollToBottom() {
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

/**
 * Escape HTML to prevent XSS.
 */
function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text || "";
    return div.innerHTML;
}


// ═══════════════════════════════════════════════════════════════════════════
// DASHBOARD
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Load dashboard stats from the /logs endpoint.
 */
async function loadDashboard() {
    try {
        const response = await fetch("/logs");
        if (!response.ok) throw new Error("Failed to load logs");

        const data = await response.json();

        // Update stat cards
        document.getElementById("stat-sessions-value").textContent = data.total_sessions || 0;
        document.getElementById("stat-interactions-value").textContent = data.total_interactions || 0;
        document.getElementById("stat-high-value").textContent = data.urgency_distribution?.high || 0;
        document.getElementById("stat-medium-value").textContent = data.urgency_distribution?.medium || 0;
        document.getElementById("stat-low-value").textContent = data.urgency_distribution?.low || 0;

        // Language stats
        const langs = data.language_distribution || {};
        const langLabels = { hi: "Hindi", ta: "Tamil", en: "English" };
        const langStr = Object.entries(langs)
            .map(([code, count]) => `${langLabels[code] || code}: ${count}`)
            .join(", ") || "—";
        document.getElementById("stat-languages-value").textContent = langStr;

        // Recent activity log
        const logEntries = document.getElementById("log-entries");
        const recent = data.recent_interactions || [];

        if (recent.length === 0) {
            logEntries.innerHTML = '<p class="empty-log">No activity yet. Start a conversation!</p>';
        } else {
            logEntries.innerHTML = recent.map(entry => {
                const time = new Date(entry.timestamp).toLocaleTimeString();
                return `
                    <div class="log-entry">
                        <div class="log-urgency ${entry.urgency || 'low'}"></div>
                        <div class="log-text">
                            <strong>User:</strong> ${escapeHtml(truncate(entry.user, 60))}<br>
                            <strong>Bot:</strong> ${escapeHtml(truncate(entry.bot, 80))}
                        </div>
                        <div class="log-time">${time}</div>
                    </div>
                `;
            }).join("");
        }

    } catch (err) {
        console.error("Dashboard error:", err);
    }
}

/**
 * Truncate text to a max length.
 */
function truncate(text, maxLen) {
    if (!text) return "";
    return text.length > maxLen ? text.substring(0, maxLen) + "…" : text;
}


// ═══════════════════════════════════════════════════════════════════════════
// KEYBOARD SHORTCUT
// ═══════════════════════════════════════════════════════════════════════════

// Press Space to toggle recording (when not typing in an input)
document.addEventListener("keydown", (e) => {
    if (e.code === "Space" && e.target.tagName !== "INPUT" && e.target.tagName !== "SELECT") {
        e.preventDefault();
        recordBtn.click();
    }
});
