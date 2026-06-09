const API_URL = ""; // Relative URL handles Docker/hosting environments automatically

// Helper to retrieve token from LocalStorage
function getAuthToken() {
    return localStorage.getItem("careeros_token");
}

// Set auth token
function setAuthToken(token) {
    localStorage.setItem("careeros_token", token);
}

// Clear auth token and log out
function logout() {
    localStorage.removeItem("careeros_token");
    window.location.href = "/index.html";
}

// Unified fetch request wrapper with authorization headers
async function apiRequest(endpoint, method = "GET", body = null) {
    const headers = {};
    const token = getAuthToken();
    
    if (token) {
        headers["Authorization"] = `Bearer ${token}`;
    }
    
    const config = {
        method,
        headers
    };
    
    if (body) {
        if (body instanceof FormData) {
            config.body = body;
        } else {
            headers["Content-Type"] = "application/json";
            config.body = JSON.stringify(body);
        }
    }
    
    try {
        const response = await fetch(`${API_URL}/api/v1${endpoint}`, config);
        
        if (response.status === 401) {
            // Redirect to login if token is expired or invalid
            localStorage.removeItem("careeros_token");
            if (!window.location.pathname.endsWith("index.html")) {
                window.location.href = "/index.html";
            }
            return null;
        }
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || "Something went wrong");
        }
        
        return await response.json();
    } catch (error) {
        console.error(`API Error on ${endpoint}:`, error);
        throw error;
    }
}

// Authentication API Requests
const authAPI = {
    async register(email, password, fullName) {
        return await apiRequest("/auth/register", "POST", { email, password, full_name: fullName });
    },
    async login(email, password) {
        const formData = new FormData();
        formData.append("username", email);
        formData.append("password", password);
        const res = await apiRequest("/auth/token", "POST", formData);
        if (res && res.access_token) {
            setAuthToken(res.access_token);
            return true;
        }
        return false;
    }
};

// Applications API Requests
const appsAPI = {
    async list() {
        return await apiRequest("/applications");
    },
    async get(id) {
        return await apiRequest(`/applications/${id}`);
    },
    async update(id, data) {
        return await apiRequest(`/applications/${id}`, "PUT", data);
    },
    async getSummary() {
        return await apiRequest("/applications/analytics/summary");
    },
    async getFunnel() {
        return await apiRequest("/applications/analytics/funnel");
    }
};

// Gmail API Requests
const gmailAPI = {
    async getSyncStatus() {
        return await apiRequest("/gmail/sync/status");
    },
    async triggerSync() {
        return await apiRequest("/gmail/sync", "POST");
    },
    async getFollowups() {
        return await apiRequest("/gmail/followups");
    },
    async completeFollowup(id) {
        return await apiRequest(`/gmail/followups/${id}/complete`, "PUT");
    }
};

// Google Sheets Exporter API Requests
const sheetsAPI = {
    async getConfig() {
        return await apiRequest("/sync/sheets");
    },
    async saveConfig(spreadsheetId, sheetName, isEnabled) {
        return await apiRequest("/sync/sheets", "POST", {
            spreadsheet_id: spreadsheetId,
            sheet_name: sheetName,
            is_enabled: isEnabled
        });
    },
    async triggerSync() {
        return await apiRequest("/sync/sheets/trigger", "POST");
    }
};

// Chat Agent API Requests
const chatAPI = {
    async sendMessage(message) {
        return await apiRequest("/chat", "POST", { message });
    }
};

// Resume Tailoring API Requests
const resumesAPI = {
    async tailorSingle(jobTitle, companyName, jobDescription, jobUrl) {
        return await apiRequest("/resumes/tailor-single", "POST", {
            job_title: jobTitle,
            company_name: companyName,
            job_description: jobDescription,
            job_url: jobUrl
        });
    },
    async tailorBulk(searchUrl, count) {
        return await apiRequest("/resumes/tailor-bulk", "POST", {
            search_url: searchUrl,
            count
        });
    },
    async getHistory() {
        return await apiRequest("/resumes/history");
    },
    async getBaseResume() {
        return await apiRequest("/resumes/base");
    },
    async updateBaseResume(baseResume) {
        return await apiRequest("/resumes/base", "PUT", {
            base_resume: baseResume
        });
    }
};
