// API Server URL (Base path for routing requests)
const API_BASE = window.location.origin;

// State management
let sessionInterval = null;
let currentToken = localStorage.getItem("access_token") || null;

// Initialize elements
document.addEventListener("DOMContentLoaded", () => {
    // Render initial Lucide Icons
    lucide.createIcons();
    
    // Check initial state
    checkServerConnection();
    
    if (currentToken) {
        setupAuthenticatedState(currentToken);
    } else {
        setupGuestState();
    }
    
    // Wire up events
    document.getElementById("login-form").addEventListener("submit", handleLogin);
    document.getElementById("logout-btn").addEventListener("click", handleLogout);
    document.getElementById("btn-call-dashboard").addEventListener("click", callDashboardAPI);
    document.getElementById("btn-call-admin").addEventListener("click", callAdminAPI);
});

// =========================================================
// SERVICE AVAILABILITY PING
// =========================================================
async function checkServerConnection() {
    const statusDiv = document.getElementById("header-status");
    try {
        const response = await fetch(`${API_BASE}/`);
        if (response.ok) {
            statusDiv.className = "header-status online";
            statusDiv.querySelector(".status-label").textContent = "Connected";
        } else {
            throw new Error();
        }
    } catch (e) {
        statusDiv.className = "header-status offline";
        statusDiv.querySelector(".status-label").textContent = "Disconnected";
    }
}

// =========================================================
// AUTHENTICATION: LOGIN FLOW
// =========================================================
async function handleLogin(e) {
    e.preventDefault();
    
    const usernameInput = document.getElementById("username");
    const passwordInput = document.getElementById("password");
    const submitBtn = document.getElementById("submit-btn");
    
    const originalBtnHTML = submitBtn.innerHTML;
    submitBtn.disabled = true;
    submitBtn.innerHTML = `<span>Signing in...</span>`;
    
    // OAuth2PasswordRequestForm expects application/x-www-form-urlencoded
    const formData = new URLSearchParams();
    formData.append("username", usernameInput.value);
    formData.append("password", passwordInput.value);
    
    try {
        const response = await fetch(`${API_BASE}/api/login`, {
            method: "POST",
            headers: {
                "Content-Type": "application/x-www-form-urlencoded"
            },
            body: formData
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.detail || "Authentication failed");
        }
        
        // Save JWT to LocalStorage
        currentToken = data.access_token;
        localStorage.setItem("access_token", currentToken);
        
        showToast("Success", "Welcome to NextGen Secure Portal!", "success");
        
        // Transition UI state
        setupAuthenticatedState(currentToken);
        
        // Clear login form fields
        usernameInput.value = "";
        passwordInput.value = "";
        
    } catch (error) {
        showToast("Access Denied", error.message, "error");
    } finally {
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalBtnHTML;
        lucide.createIcons();
    }
}

// =========================================================
// AUTHENTICATION: LOGOUT FLOW
// =========================================================
function handleLogout() {
    currentToken = null;
    localStorage.removeItem("access_token");
    
    if (sessionInterval) {
        clearInterval(sessionInterval);
        sessionInterval = null;
    }
    
    showToast("Signed Out", "Your session has been terminated safely.", "success");
    setupGuestState();
}

// =========================================================
// STATE CONFIGURES (GUEST vs AUTHENTICATED)
// =========================================================
function setupGuestState() {
    document.getElementById("login-section").classList.remove("hidden");
    document.getElementById("dashboard-section").classList.add("hidden");
    
    // Reset responses
    document.getElementById("response-status").textContent = "No Request Sent";
    document.getElementById("response-status").className = "response-code";
    document.getElementById("console-output").textContent = "// Click a button above to execute request...";
}

function setupAuthenticatedState(token) {
    document.getElementById("login-section").classList.add("hidden");
    document.getElementById("dashboard-section").classList.remove("hidden");
    
    // Parse JWT claims
    const claims = decodeJwt(token);
    if (!claims) {
        handleLogout();
        return;
    }
    
    // Update User Profile UI
    const username = claims.sub;
    const role = claims.role;
    
    document.getElementById("profile-name").textContent = username.toUpperCase();
    document.getElementById("profile-email").textContent = `${username}@jwtportal.io`;
    document.getElementById("user-avatar").textContent = username.charAt(0).toUpperCase();
    
    const roleBadge = document.getElementById("role-badge");
    roleBadge.textContent = role;
    roleBadge.className = `badge ${role === 'admin' ? 'admin-role' : 'employee-role'}`;
    
    // Update visual token inspector
    document.getElementById("jwt-payload-display").textContent = JSON.stringify(claims, null, 2);
    
    // Start session timer
    startCountdown(claims.exp);
    
    // Ping to update status header
    checkServerConnection();
    lucide.createIcons();
}

// =========================================================
// JWT DECODER HELPER
// =========================================================
function decodeJwt(token) {
    try {
        const parts = token.split('.');
        if (parts.length !== 3) return null;
        
        // Decode base64 URL
        let base64Url = parts[1];
        let base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
        let jsonPayload = decodeURIComponent(atob(base64).split('').map(function(c) {
            return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
        }).join(''));
        
        return JSON.parse(jsonPayload);
    } catch (e) {
        console.error("JWT Decode error", e);
        return null;
    }
}

// =========================================================
// EXPIRATION TIMER
// =========================================================
function startCountdown(expiryTime) {
    if (sessionInterval) {
        clearInterval(sessionInterval);
    }
    
    const expiryTimer = document.getElementById("token-expiry-timer");
    
    function updateTimer() {
        const now = Math.floor(Date.now() / 1000);
        const timeRemaining = expiryTime - now;
        
        if (timeRemaining <= 0) {
            clearInterval(sessionInterval);
            expiryTimer.textContent = "00:00";
            showToast("Session Expired", "Your security token has expired. Please log in again.", "error");
            handleLogout();
            return;
        }
        
        const minutes = Math.floor(timeRemaining / 60);
        const seconds = timeRemaining % 60;
        
        expiryTimer.textContent = `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
    }
    
    updateTimer();
    sessionInterval = setInterval(updateTimer, 1000);
}

// =========================================================
// API CONSOLE EXECUTIONS
// =========================================================
async function callDashboardAPI() {
    await fetchAndRenderConsole("/api/dashboard");
}

async function callAdminAPI() {
    await fetchAndRenderConsole("/api/admin");
}

async function fetchAndRenderConsole(path) {
    const statusSpan = document.getElementById("response-status");
    const outputCode = document.getElementById("console-output");
    
    statusSpan.textContent = "Requesting...";
    statusSpan.className = "response-code";
    
    try {
        const headers = {};
        if (currentToken) {
            headers["Authorization"] = `Bearer ${currentToken}`;
        }
        
        const response = await fetch(`${API_BASE}${path}`, {
            method: "GET",
            headers: headers
        });
        
        const data = await response.json();
        
        statusSpan.textContent = `HTTP ${response.status} ${response.statusText || ""}`;
        statusSpan.className = `response-code status-${response.status}`;
        outputCode.textContent = JSON.stringify(data, null, 2);
        
    } catch (error) {
        statusSpan.textContent = "Connection Failure";
        statusSpan.className = "response-code status-401";
        outputCode.textContent = JSON.stringify({ error: "Could not connect to the authentication server." }, null, 2);
    }
}

// =========================================================
// TOAST NOTIFICATIONS
// =========================================================
function showToast(title, message, type = "success") {
    const container = document.getElementById("toast-container");
    
    const toast = document.createElement("div");
    toast.className = `toast toast-${type}`;
    
    const iconName = type === "success" ? "check-circle" : "alert-triangle";
    
    toast.innerHTML = `
        <i data-lucide="${iconName}" class="toast-icon"></i>
        <div class="toast-content">
            <div class="toast-title">${title}</div>
            <div class="toast-message">${message}</div>
        </div>
    `;
    
    container.appendChild(toast);
    lucide.createIcons();
    
    // Auto-remove
    setTimeout(() => {
        toast.style.animation = "toast-in 0.3s reverse forwards";
        setTimeout(() => {
            toast.remove();
        }, 300);
    }, 4000);
}

// =========================================================
// UTILITY: DEMO CREDS AUTO-FILL
// =========================================================
window.fillCredentials = function(username, password) {
    document.getElementById("username").value = username;
    document.getElementById("password").value = password;
    showToast("Filled", `Credentials for ${username} populated!`, "success");
};
