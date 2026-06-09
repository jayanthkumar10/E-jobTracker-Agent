// Active Panel navigation tab state
let activeTab = "analytics";
let applications = [];
let funnelChart = null;

// Initialize Dashboard UI Components and data
document.addEventListener("DOMContentLoaded", async () => {
    // Check if token exists
    if (!localStorage.getItem("careeros_token")) {
        window.location.href = "/index.html";
        return;
    }

    // Initialize Lucide icons
    lucide.createIcons();

    // Check query params for Google OAuth Callback updates
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get("auth") === "success") {
        showFeedback("Google Account successfully linked!", true);
        // Clean URL params without page reload
        window.history.replaceState({}, document.title, window.location.pathname);
    }

    // Populate data
    await loadOAuthBadge();
    await loadAnalytics();
    await loadApplications();
    await loadFollowups();
    await loadSheetsConfig();
    bindTailorForms();
});

// Tab Switcher Logic
function switchTab(tabName) {
    // Hide all panels
    document.getElementById("panel-analytics").classList.add("hidden");
    document.getElementById("panel-apps").classList.add("hidden");
    document.getElementById("panel-tailor").classList.add("hidden");
    document.getElementById("panel-sheets-tracker").classList.add("hidden");
    document.getElementById("panel-chat").classList.add("hidden");
    document.getElementById("panel-settings").classList.add("hidden");

    // Remove active styles on all sidebar buttons
    document.getElementById("nav-analytics").className = "w-full flex items-center space-x-3 px-4 py-3 rounded-xl text-slate-400 hover:text-slate-200 hover:bg-slate-900 transition-all";
    document.getElementById("nav-apps").className = "w-full flex items-center space-x-3 px-4 py-3 rounded-xl text-slate-400 hover:text-slate-200 hover:bg-slate-900 transition-all";
    document.getElementById("nav-tailor").className = "w-full flex items-center space-x-3 px-4 py-3 rounded-xl text-slate-400 hover:text-slate-200 hover:bg-slate-900 transition-all";
    document.getElementById("nav-sheets-tracker").className = "w-full flex items-center space-x-3 px-4 py-3 rounded-xl text-slate-400 hover:text-slate-200 hover:bg-slate-900 transition-all";
    document.getElementById("nav-chat").className = "w-full flex items-center space-x-3 px-4 py-3 rounded-xl text-slate-400 hover:text-slate-200 hover:bg-slate-900 transition-all";
    document.getElementById("nav-settings").className = "w-full flex items-center space-x-3 px-4 py-3 rounded-xl text-slate-400 hover:text-slate-200 hover:bg-slate-900 transition-all";

    // Show active panel
    document.getElementById(`panel-${tabName}`).classList.remove("hidden");
    
    // Set active button style
    document.getElementById(`nav-${tabName}`).className = "w-full flex items-center space-x-3 px-4 py-3 rounded-xl text-white bg-brand-600/10 font-medium hover:bg-slate-900 transition-all";

    // Set page header title
    const titles = {
        analytics: "Dashboard Overview",
        apps: "Job Applications Tracker",
        tailor: "AI Resume Tailor & Optimizer",
        "sheets-tracker": "Live Google Sheet Tracker",
        chat: "CareerOS AI Chat Assistant",
        settings: "Integrations & Settings"
    };
    document.getElementById("page-title").innerText = titles[tabName];
    activeTab = tabName;

    // Trigger tab-specific loaders
    if (tabName === "sheets-tracker") {
        loadSheetsTrackerIframe();
    } else if (tabName === "tailor") {
        loadTailorData();
    }
}

// Display Toast alerts
function showFeedback(message, isSuccess = true) {
    const banner = document.getElementById("feedback-banner");
    const msgSpan = document.getElementById("feedback-message");
    msgSpan.innerText = message;
    
    if (isSuccess) {
        banner.className = "mb-6 p-4 rounded-2xl border bg-emerald-500/10 border-emerald-500/20 text-emerald-400 flex items-center justify-between";
    } else {
        banner.className = "mb-6 p-4 rounded-2xl border bg-rose-500/10 border-rose-500/20 text-rose-400 flex items-center justify-between";
    }
    banner.classList.remove("hidden");
    
    setTimeout(() => {
        banner.classList.add("hidden");
    }, 6000);
}

// Fetch Google OAuth linked status
async function loadOAuthBadge() {
    const badge = document.getElementById("gmail-badge");
    const linkBtn = document.getElementById("btn-link-google");
    
    try {
        const res = await gmailAPI.getSyncStatus();
        if (res && res.linked) {
            badge.innerText = "Gmail Connected";
            badge.className = "px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20";
            if (linkBtn) {
                linkBtn.innerHTML = `<span>Update Linked Google Account</span>`;
            }
        } else {
            badge.innerText = "Gmail Disconnected";
            badge.className = "px-2.5 py-1 rounded-full text-xs font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/20";
        }
    } catch (err) {
        badge.innerText = "Error checking OAuth";
    }
}

// Trigger Google OAuth authorization url redirection
function connectGoogleOAuth() {
    const token = getAuthToken();
    if (!token) return;
    
    // Call the FastAPI redirect endpoint passing user JWT token as state
    window.location.href = `/api/v1/oauth/google/login?state=${token}`;
}

// Fetch KPIs and render funnel chart
async function loadAnalytics() {
    // Set today's date badge
    const todayBadge = document.getElementById("today-date-badge");
    if (todayBadge) {
        const today = new Date();
        const options = { weekday: 'long', year: 'numeric', month: 'short', day: 'numeric' };
        todayBadge.innerText = `Today: ${today.toLocaleDateString('en-US', options)}`;
    }

    try {
        const summary = await appsAPI.getSummary();
        const funnel = await appsAPI.getFunnel();
        
        if (summary) {
            document.getElementById("stat-total").innerText = summary.total_applications;
            document.getElementById("stat-response").innerText = `${summary.response_rate}%`;
            document.getElementById("stat-interviews-done").innerText = summary.interviews_done;
            document.getElementById("stat-avg-days").innerText = `${summary.avg_days_to_interview} days`;
            document.getElementById("stat-streak").innerText = `${summary.daily_applied_streak} days`;
            
            const journeyStartText = summary.journey_start_date 
                ? `Journey Started: ${new Date(summary.journey_start_date).toLocaleDateString(undefined, {month: 'short', day: 'numeric', year: 'numeric'})}`
                : "Journey Started: N/A";
            document.getElementById("stat-journey-start").innerText = journeyStartText;
            document.getElementById("stat-journey-days").innerText = `${summary.journey_days_count} days`;
        }
        
        if (funnel) {
            renderFunnelChart(funnel);
        }
    } catch (err) {
        console.error("Failed to load analytics: ", err);
    }
}

// Render funnel analytics chart using Chart.js
function renderFunnelChart(data) {
    const ctx = document.getElementById('funnelChart').getContext('2d');
    
    if (funnelChart) {
        funnelChart.destroy();
    }
    
    funnelChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Applied', 'Interviewing'],
            datasets: [{
                label: 'Conversion',
                data: [data.applied, data.interviewing],
                backgroundColor: [
                    'rgba(99, 102, 241, 0.6)', // indigo
                    'rgba(16, 185, 129, 0.6)'  // emerald
                ],
                borderColor: [
                    '#6366f1', '#10b981'
                ],
                borderWidth: 1.5,
                borderRadius: 8
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: { color: 'rgba(255, 255, 255, 0.05)' },
                    ticks: { color: '#94a3b8' }
                },
                x: {
                    grid: { display: false },
                    ticks: { color: '#94a3b8' }
                }
            }
        }
    });
}

// Fetch list of Applications
async function loadApplications() {
    const tbody = document.getElementById("apps-tbody");
    try {
        applications = await appsAPI.list();
        renderApplicationsTable(applications);
    } catch (err) {
        tbody.innerHTML = `<tr><td colspan="6" class="text-center p-8 text-rose-400">Failed to fetch applications: ${err.message}</td></tr>`;
    }
}

// Render rows in table
function renderApplicationsTable(list) {
    const tbody = document.getElementById("apps-tbody");
    if (!list || list.length === 0) {
        tbody.innerHTML = `<tr><td colspan="6" class="text-center p-8 text-slate-500 text-sm">No applications found. Connect Gmail to start tracking.</td></tr>`;
        return;
    }
    
    tbody.innerHTML = "";
    list.forEach(app => {
        const tr = document.createElement("tr");
        tr.className = "border-b border-slate-850 hover:bg-slate-900/40 transition-all cursor-pointer";
        tr.onclick = () => openAppDetails(app.id);
        
        let statusBadgeClass = "bg-slate-900 text-slate-400";
        if (app.status === "APPLIED") statusBadgeClass = "bg-indigo-500/10 text-indigo-400 border border-indigo-500/20";
        else if (app.status === "SCREENING") statusBadgeClass = "bg-purple-500/10 text-purple-400 border border-purple-500/20";
        else if (app.status === "INTERVIEWING") statusBadgeClass = "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20";
        else if (app.status === "OFFERED") statusBadgeClass = "bg-amber-500/10 text-amber-400 border border-amber-500/20";
        else if (app.status === "REJECTED") statusBadgeClass = "bg-rose-500/10 text-rose-400 border border-rose-500/20";
        else if (app.status === "TAILORED") statusBadgeClass = "bg-sky-500/10 text-sky-400 border border-sky-500/20";

        const dateStr = app.created_at ? new Date(app.created_at).toLocaleDateString(undefined, {month: 'short', day: 'numeric', year: 'numeric'}) : 'N/A';
        tr.innerHTML = `
            <td class="p-4 pl-6 font-semibold text-white">${app.company_name}</td>
            <td class="p-4 text-slate-300 text-sm">${app.job_title}</td>
            <td class="p-4">
                <span class="px-2.5 py-1 rounded-full text-xs font-semibold ${statusBadgeClass}">
                    ${app.status}
                </span>
            </td>
            <td class="p-4 text-slate-400 text-sm">${dateStr}</td>
            <td class="p-4 text-slate-400 text-sm">
                <span class="px-2 py-0.5 rounded bg-slate-900 border border-slate-800 text-[11px] font-medium text-slate-300">
                    ${app.source || "Direct"}
                </span>
            </td>
            <td class="p-4 text-slate-400 text-sm">${app.location || "N/A"}</td>
            <td class="p-4 pr-6 text-right" onclick="event.stopPropagation()">
                <button onclick="openAppDetails('${app.id}')" class="text-brand-500 hover:text-brand-400 text-xs font-semibold transition-all">Details &rarr;</button>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

// Client Side Search and Status Filter
function filterApplications() {
    const query = document.getElementById("search-apps").value.toLowerCase();
    const statusFilter = document.getElementById("filter-status").value;
    
    const filtered = applications.filter(app => {
        const matchesQuery = (
            app.company_name.toLowerCase().includes(query) ||
            app.job_title.toLowerCase().includes(query) ||
            app.status.toLowerCase().includes(query)
        );
        
        const matchesStatus = (statusFilter === "ALL" || app.status === statusFilter);
        
        return matchesQuery && matchesStatus;
    });
    renderApplicationsTable(filtered);
}

// Trigger Gmail synchronization manually
async function triggerSync() {
    const icon = document.getElementById("sync-icon");
    icon.classList.add("animate-spin");
    
    try {
        await gmailAPI.triggerSync();
        showFeedback("Sync triggered successfully. Gmail inbox scanning in background...", true);
        setTimeout(async () => {
            await loadAnalytics();
            await loadApplications();
            await loadFollowups();
            icon.classList.remove("animate-spin");
        }, 5000); // Allow worker tasks a few seconds
    } catch (err) {
        showFeedback(`Sync failed: ${err.message}`, false);
        icon.classList.remove("animate-spin");
    }
}

// Open application timeline detailed Modal Drawer
async function openAppDetails(appId) {
    const modal = document.getElementById("modal-app-details");
    const container = document.getElementById("modal-content");
    
    modal.classList.remove("translate-x-full");
    container.innerHTML = `<p class="text-sm text-slate-400 text-center py-12">Loading details...</p>`;
    
    try {
        const details = await appsAPI.get(appId);
        if (details) {
            let statusBadgeClass = "bg-slate-900 text-slate-400";
            if (details.status === "APPLIED") statusBadgeClass = "bg-indigo-500/10 text-indigo-400 border border-indigo-500/20";
            else if (details.status === "SCREENING") statusBadgeClass = "bg-purple-500/10 text-purple-400 border border-purple-500/20";
            else if (details.status === "INTERVIEWING") statusBadgeClass = "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20";
            else if (details.status === "OFFERED") statusBadgeClass = "bg-amber-500/10 text-amber-400 border border-amber-500/20";
            else if (details.status === "REJECTED") statusBadgeClass = "bg-rose-500/10 text-rose-400 border border-rose-500/20";
            else if (details.status === "TAILORED") statusBadgeClass = "bg-sky-500/10 text-sky-400 border border-sky-500/20";

            let atsHTML = "";
            if (details.ats_match_details) {
                try {
                    const ats = typeof details.ats_match_details === 'string' ? JSON.parse(details.ats_match_details) : details.ats_match_details;
                    const hasKws = ats.candidate_has || [];
                    const needsKws = ats.candidate_needs_to_inject || [];
                    
                    atsHTML = `
                        <!-- ATS Match Analysis -->
                        <div class="space-y-3 bg-slate-900/40 border border-slate-850 p-4 rounded-2xl text-xs">
                            <h4 class="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-1.5">
                                <i data-lucide="cpu" class="w-3.5 h-3.5 text-brand-500"></i>
                                <span>ATS Optimization Insights</span>
                            </h4>
                            <div>
                                <span class="text-slate-500 block uppercase font-semibold text-[9px] tracking-wider mb-1">Target Title Mirror</span>
                                <span class="font-medium text-slate-200">${ats.ats_title_mirror || details.job_title}</span>
                            </div>
                            ${ats.summary_hook ? `
                            <div>
                                <span class="text-slate-500 block uppercase font-semibold text-[9px] tracking-wider mb-1">AI Summary Hook</span>
                                <p class="text-slate-350 italic">"${ats.summary_hook}"</p>
                            </div>
                            ` : ""}
                            <div class="space-y-2">
                                <span class="text-slate-500 block uppercase font-semibold text-[9px] tracking-wider">Keywords Matching</span>
                                <div class="flex flex-wrap gap-1.5">
                                    ${hasKws.map(kw => `<span class="bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 px-2 py-0.5 rounded text-[10px]">${kw}</span>`).join('')}
                                    ${needsKws.map(kw => `<span class="bg-amber-500/10 text-amber-400 border border-amber-500/20 px-2 py-0.5 rounded text-[10px]">${kw} (Injected)</span>`).join('')}
                                </div>
                            </div>
                            ${ats.keyword_placement_priority ? `
                            <div>
                                <span class="text-slate-500 block uppercase font-semibold text-[9px] tracking-wider mb-1">Optimisation Strategy</span>
                                <p class="text-slate-400 font-light">${ats.keyword_placement_priority}</p>
                            </div>
                            ` : ""}
                        </div>
                    `;
                } catch (e) {
                    console.error("Failed to parse ATS Match Details: ", e);
                }
            }

            container.innerHTML = `
                <div class="space-y-4">
                    <div>
                        <h3 class="text-2xl font-bold text-white leading-tight">${details.company_name}</h3>
                        <p class="text-slate-400 text-sm mb-2">${details.job_title}</p>
                        <span class="px-2.5 py-1 rounded-full text-xs font-semibold ${statusBadgeClass}">
                            ${details.status}
                        </span>
                    </div>

                    ${details.tailored_resume_url ? `
                    <div class="pt-2">
                        <a href="${details.tailored_resume_url}" target="_blank" class="w-full text-center bg-brand-600/15 hover:bg-brand-600 border border-brand-500/20 hover:border-brand-500 text-slate-200 hover:text-white font-bold py-3 rounded-xl text-xs transition-all flex items-center justify-center gap-2 shadow-sm">
                            <i data-lucide="external-link" class="w-4 h-4"></i>
                            <span>View Tailored Resume</span>
                        </a>
                    </div>
                    ` : ""}

                    ${details.status === "TAILORED" ? `
                    <div class="pt-1">
                        <button onclick="markAsApplied('${details.id}')" class="w-full bg-emerald-650 hover:bg-emerald-600 text-white font-bold py-3 rounded-xl text-xs transition-all flex items-center justify-center gap-1.5 shadow-md shadow-emerald-500/10">
                            <i data-lucide="check" class="w-4 h-4"></i>
                            <span>Mark as Applied & Sync Sheet</span>
                        </button>
                    </div>
                    ` : ""}

                    ${atsHTML}
                    
                    <div class="grid grid-cols-2 gap-4 bg-slate-900/50 p-4 border border-slate-850 rounded-2xl text-sm">
                        <div>
                            <span class="text-xs text-slate-500 block">Status</span>
                            <select id="update-status-select" onchange="updateAppStatus('${details.id}', this.value)" class="bg-slate-950 border border-slate-800 focus:border-brand-500 rounded px-2 py-1 text-xs text-slate-200 mt-1 focus:outline-none">
                                <option value="TAILORED" ${details.status === "TAILORED" ? "selected" : ""}>TAILORED</option>
                                <option value="APPLIED" ${details.status === "APPLIED" ? "selected" : ""}>APPLIED</option>
                                <option value="SCREENING" ${details.status === "SCREENING" ? "selected" : ""}>SCREENING</option>
                                <option value="INTERVIEWING" ${details.status === "INTERVIEWING" ? "selected" : ""}>INTERVIEWING</option>
                                <option value="OFFERED" ${details.status === "OFFERED" ? "selected" : ""}>OFFERED</option>
                                <option value="REJECTED" ${details.status === "REJECTED" ? "selected" : ""}>REJECTED</option>
                            </select>
                        </div>
                        <div>
                            <span class="text-xs text-slate-500 block">Work Mode</span>
                            <span class="font-medium text-slate-300">${details.work_mode || "N/A"}</span>
                        </div>
                        <div>
                            <span class="text-xs text-slate-500 block">Location</span>
                            <span class="font-medium text-slate-300">${details.location || "N/A"}</span>
                        </div>
                        <div>
                            <span class="text-xs text-slate-500 block">Salary Range</span>
                            <span class="font-medium text-slate-300">${details.salary_range || "N/A"}</span>
                        </div>
                        <div class="col-span-2">
                            <span class="text-xs text-slate-500 block">Recruiter Contact</span>
                            <span class="font-medium text-slate-300">${details.recruiter_name || "N/A"} (${details.recruiter_email || "N/A"})</span>
                        </div>
                    </div>

                    <!-- Notes Section -->
                    <div class="space-y-2">
                        <h4 class="text-sm font-bold text-white uppercase tracking-wider">Application Notes</h4>
                        <textarea onblur="updateAppNotes('${details.id}', this.value)" class="w-full bg-slate-900/50 border border-slate-850 focus:border-brand-500 rounded-xl p-3 text-sm text-slate-300 focus:outline-none h-24 transition-all" placeholder="Enter notes, questions, or updates...">${details.notes || ""}</textarea>
                    </div>

                    <!-- Timeline Section -->
                    <div class="space-y-4">
                        <h4 class="text-sm font-bold text-white uppercase tracking-wider">Application Timeline</h4>
                        <div class="space-y-3 pl-2 border-l border-slate-850 relative">
                            ${details.timeline.map(ev => `
                                <div class="relative pl-6 pb-2">
                                    <div class="absolute -left-[29px] top-1.5 w-3.5 h-3.5 rounded-full border border-slate-950 bg-brand-500"></div>
                                    <span class="text-xs text-slate-500 block">${ev.event_date}</span>
                                    <span class="text-sm font-semibold text-slate-200">${ev.stage}</span>
                                    <p class="text-xs text-slate-400 mt-0.5">${ev.notes || ""}</p>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                </div>
            `;
            lucide.createIcons();
        }
    } catch (err) {
        container.innerHTML = `<p class="text-sm text-rose-400 text-center py-12">Failed to load: ${err.message}</p>`;
    }
}

// Close Modal Drawer
function closeAppDetails() {
    document.getElementById("modal-app-details").classList.add("translate-x-full");
}

// Update application status manually
async function updateAppStatus(id, newStatus) {
    try {
        await appsAPI.update(id, { status: newStatus });
        showFeedback("Application status updated.", true);
        await loadAnalytics();
        await loadApplications();
        // Re-open details drawer to show new timeline event logs
        await openAppDetails(id);
    } catch (err) {
        showFeedback(`Failed to update status: ${err.message}`, false);
    }
}

// Update application notes manually on blur
async function updateAppNotes(id, text) {
    try {
        await appsAPI.update(id, { notes: text });
    } catch (err) {
        console.error("Failed to save notes: ", err);
    }
}

// Fetch suggested follow-ups
async function loadFollowups() {
    const container = document.getElementById("followups-container");
    try {
        const list = await gmailAPI.getFollowups();
        if (!list || list.length === 0) {
            container.innerHTML = `<p class="text-sm text-slate-500 text-center py-6">All caught up! No stagnant applications detected.</p>`;
            return;
        }
        
        container.innerHTML = "";
        list.forEach(item => {
            const card = document.createElement("div");
            card.className = "bg-amber-500/5 border border-amber-500/10 rounded-xl p-4 space-y-3 relative";
            card.innerHTML = `
                <div class="pr-6">
                    <span class="text-xs text-amber-500 font-semibold block uppercase tracking-wider">No response for 14+ days</span>
                    <h4 class="text-sm font-bold text-white mt-1">${item.company_name} - ${item.job_title}</h4>
                </div>
                
                <div class="flex space-x-2">
                    <button onclick="copyFollowupDraft('${escapeHtml(item.suggested_body)}')" class="bg-amber-500 hover:bg-amber-600 text-slate-950 font-bold px-3 py-1.5 rounded-lg text-xs transition-all flex items-center space-x-1">
                        <i data-lucide="copy" class="w-3.5 h-3.5"></i>
                        <span>Copy Draft</span>
                    </button>
                    <button onclick="resolveFollowup('${item.id}')" class="bg-slate-900 hover:bg-slate-800 text-slate-400 px-3 py-1.5 rounded-lg text-xs transition-all">
                        <span>Done</span>
                    </button>
                </div>
            `;
            container.appendChild(card);
        });
        lucide.createIcons();
    } catch (err) {
        container.innerHTML = `<p class="text-xs text-rose-400">Failed to load follow-ups: ${err.message}</p>`;
    }
}

// Copy prompt text to clipboard helper
function copyFollowupDraft(text) {
    navigator.clipboard.writeText(text);
    showFeedback("Follow-up email template draft copied to clipboard!", true);
}

// Complete follow-up suggestions
async function resolveFollowup(id) {
    try {
        await gmailAPI.completeFollowup(id);
        showFeedback("Follow-up task dismissed.", true);
        await loadFollowups();
    } catch (err) {
        showFeedback(`Failed to complete: ${err.message}`, false);
    }
}

// Helper to escape characters in dynamically generated html strings
function escapeHtml(text) {
    if (!text) return "";
    return text
         .replace(/&/g, "&amp;")
         .replace(/</g, "&lt;")
         .replace(/>/g, "&gt;")
         .replace(/"/g, "&quot;")
         .replace(/'/g, "&#039;");
}

// Fetch sheets synchronization configurations
async function loadSheetsConfig() {
    try {
        const config = await sheetsAPI.getConfig();
        if (config) {
            document.getElementById("sheet-id-input").value = config.spreadsheet_id || "";
            document.getElementById("sheet-name-input").value = config.sheet_name || "Applications";
            document.getElementById("sheet-enable-input").checked = config.is_enabled || false;
        }
    } catch (err) {
        console.error("Failed to load Google Sheet config: ", err);
    }
}

// Submit Sheets config configuration
document.getElementById("sheets-config-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const id = document.getElementById("sheet-id-input").value.trim();
    const name = document.getElementById("sheet-name-input").value.trim();
    const enabled = document.getElementById("sheet-enable-input").checked;
    
    try {
        await sheetsAPI.saveConfig(id, name, enabled);
        showFeedback("Google Sheets configuration saved.", true);
    } catch (err) {
        showFeedback(`Failed to save config: ${err.message}`, false);
    }
});

// Trigger Google Sheets manual sync override
async function triggerSheetsSync() {
    const btn = document.getElementById("btn-sync-sheets-now");
    btn.disabled = true;
    btn.innerText = "Syncing...";
    
    try {
        await sheetsAPI.triggerSync();
        showFeedback("Mirroring sync started in background.", true);
        setTimeout(async () => {
            btn.disabled = false;
            btn.innerText = "Force Sync Now";
            await loadSheetsConfig();
        }, 4000);
    } catch (err) {
        showFeedback(`Sync failed: ${err.message}`, false);
        btn.disabled = false;
        btn.innerText = "Force Sync Now";
    }
}

// Conversational Chat Submit orchestrator
const chatForm = document.getElementById("chat-form");
const chatMessages = document.getElementById("chat-messages");

chatForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const input = document.getElementById("chat-input");
    const query = input.value.trim();
    if (!query) return;
    
    input.value = "";
    
    // Append user message bubble to view
    appendChatMessage(query, true);
    
    // Append loading placeholder bubble
    const loadingId = appendChatLoadingPlaceholder();
    
    try {
        const res = await chatAPI.sendMessage(query);
        removeChatLoadingPlaceholder(loadingId);
        if (res && res.response) {
            appendChatMessage(res.response, false);
        } else {
            appendChatMessage("I received no response from my agent server.", false);
        }
    } catch (err) {
        removeChatLoadingPlaceholder(loadingId);
        appendChatMessage(`Error: ${err.message}`, false);
    }
});

// Send quick recommendation queries
function sendQuickQuery(text) {
    document.getElementById("chat-input").value = text;
    chatForm.dispatchEvent(new Event("submit"));
}

// Append bubble elements
function appendChatMessage(text, isUser = false) {
    const bubbleWrapper = document.createElement("div");
    bubbleWrapper.className = isUser 
        ? "flex justify-end max-w-2xl ml-auto" 
        : "flex space-x-3 max-w-2xl";
        
    if (isUser) {
        bubbleWrapper.innerHTML = `
            <div class="bg-brand-600 text-white rounded-2xl rounded-tr-none p-4 text-sm leading-relaxed shadow-md shadow-brand-500/5">
                ${escapeHtml(text).replace(/\n/g, "<br>")}
            </div>
        `;
    } else {
        // Convert markdown stars/bold elements to bold HTML tags
        const formattedText = text
            .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
            .replace(/\n/g, "<br>");

        bubbleWrapper.innerHTML = `
            <div class="w-8 h-8 rounded-lg bg-gradient-to-tr from-brand-600 to-violet-500 flex items-center justify-center shrink-0">
                <i data-lucide="cpu" class="w-4 h-4 text-white"></i>
            </div>
            <div class="bg-slate-900/80 rounded-2xl rounded-tl-none p-4 text-sm text-slate-200 border border-slate-850 leading-relaxed">
                ${formattedText}
            </div>
        `;
    }
    chatMessages.appendChild(bubbleWrapper);
    lucide.createIcons();
    
    // Auto Scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Append typing status bubbles
function appendChatLoadingPlaceholder() {
    const id = "loading-" + Math.random().toString(36).substring(2, 9);
    const bubbleWrapper = document.createElement("div");
    bubbleWrapper.id = id;
    bubbleWrapper.className = "flex space-x-3 max-w-2xl";
    bubbleWrapper.innerHTML = `
        <div class="w-8 h-8 rounded-lg bg-gradient-to-tr from-brand-600 to-violet-500 flex items-center justify-center shrink-0">
            <i data-lucide="cpu" class="w-4 h-4 text-white"></i>
        </div>
        <div class="bg-slate-900/40 rounded-2xl rounded-tl-none p-4 text-sm text-slate-450 border border-slate-850/50 flex items-center space-x-1.5">
            <span class="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce"></span>
            <span class="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce [animation-delay:0.2s]"></span>
            <span class="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce [animation-delay:0.4s]"></span>
        </div>
    `;
    chatMessages.appendChild(bubbleWrapper);
    lucide.createIcons();
    chatMessages.scrollTop = chatMessages.scrollHeight;
    return id;
}

// Remove loading indicators
function removeChatLoadingPlaceholder(id) {
    const element = document.getElementById(id);
    if (element) {
        element.remove();
    }
}

// ==========================================
// RESUME TAILORING WORKFLOW & FUNCTIONS
// ==========================================

let activeTailorSubTab = "single";

function switchTailorSubTab(mode) {
    if (mode === "single") {
        document.getElementById("single-tailor-form").classList.remove("hidden");
        document.getElementById("bulk-tailor-form").classList.add("hidden");
        document.getElementById("subnav-single").className = "px-4 py-2 border-b-2 border-brand-500 text-sm font-semibold text-white";
        document.getElementById("subnav-bulk").className = "px-4 py-2 border-b-2 border-transparent text-sm font-medium text-slate-400 hover:text-white";
    } else {
        document.getElementById("single-tailor-form").classList.add("hidden");
        document.getElementById("bulk-tailor-form").classList.remove("hidden");
        document.getElementById("subnav-single").className = "px-4 py-2 border-b-2 border-transparent text-sm font-medium text-slate-400 hover:text-white";
        document.getElementById("subnav-bulk").className = "px-4 py-2 border-b-2 border-brand-500 text-sm font-semibold text-white";
    }
    activeTailorSubTab = mode;
}

async function loadTailorData() {
    try {
        // Load history
        const history = await resumesAPI.getHistory();
        renderTailorHistory(history);

        // Load base resume HTML
        const res = await resumesAPI.getBaseResume();
        if (res && res.base_resume) {
            document.getElementById("base-resume-editor").value = res.base_resume;
        }
    } catch (err) {
        console.error("Failed to load tailoring data: ", err);
    }
}

function renderTailorHistory(list) {
    const tbody = document.getElementById("tailor-history-tbody");
    if (!list || list.length === 0) {
        tbody.innerHTML = `<tr><td colspan="5" class="text-center p-6 text-slate-500 text-sm">No tailoring history found.</td></tr>`;
        return;
    }

    tbody.innerHTML = "";
    list.forEach(run => {
        const tr = document.createElement("tr");
        tr.className = "border-b border-slate-850 hover:bg-slate-900/40 transition-all";
        
        let statusBadgeClass = "bg-slate-900 text-slate-450";
        if (run.status === "COMPLETED") statusBadgeClass = "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20";
        else if (run.status === "PROCESSING") statusBadgeClass = "bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 animate-pulse";
        else if (run.status === "FAILED") statusBadgeClass = "bg-rose-500/10 text-rose-400 border border-rose-500/20";

        const dateStr = run.created_at ? new Date(run.created_at).toLocaleDateString(undefined, {month: 'short', day: 'numeric', year: 'numeric', hour: '2-digit', minute:'2-digit'}) : 'N/A';
        const displayUrl = run.job_url.length > 50 ? run.job_url.substring(0, 50) + "..." : run.job_url;

        tr.innerHTML = `
            <td class="p-4 pl-6 text-slate-200 text-sm font-medium">
                ${run.job_url === "Single JD Optimization" 
                    ? `<span class="flex items-center gap-1.5"><i data-lucide="sparkles" class="w-3.5 h-3.5 text-brand-500"></i> Single JD Optimisation</span>`
                    : `<a href="${run.job_url}" target="_blank" class="text-brand-500 hover:text-brand-400 underline">${displayUrl}</a>`
                }
            </td>
            <td class="p-4 text-slate-450 text-sm">${run.count}</td>
            <td class="p-4">
                <span class="px-2.5 py-1 rounded-full text-[10px] font-bold ${statusBadgeClass}">
                    ${run.status}
                </span>
            </td>
            <td class="p-4 text-slate-300 text-sm font-semibold">${run.results_count}</td>
            <td class="p-4 pr-6 text-slate-450 text-xs">${dateStr}</td>
        `;
        tbody.appendChild(tr);
    });
    lucide.createIcons();
}

async function saveBaseResume() {
    const editor = document.getElementById("base-resume-editor");
    const saveBtn = document.getElementById("btn-save-base-resume");
    
    saveBtn.disabled = true;
    saveBtn.innerText = "Saving...";
    
    try {
        await resumesAPI.updateBaseResume(editor.value);
        showFeedback("Base HTML resume template saved successfully!", true);
    } catch (err) {
        showFeedback(`Failed to save base template: ${err.message}`, false);
    } finally {
        saveBtn.disabled = false;
        saveBtn.innerText = "Save Base Template";
    }
}

function bindTailorForms() {
    // Single Tailor Form
    const singleForm = document.getElementById("single-tailor-form");
    if (singleForm) {
        singleForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const btn = document.getElementById("btn-tailor-single");
            const title = document.getElementById("tailor-title").value.trim();
            const company = document.getElementById("tailor-company").value.trim();
            const url = document.getElementById("tailor-url").value.trim();
            const desc = document.getElementById("tailor-description").value.trim();

            btn.disabled = true;
            btn.innerHTML = `<i data-lucide="refresh-cw" class="w-4 h-4 animate-spin mr-1"></i> Optimising resume details, please wait...`;
            lucide.createIcons();

            try {
                const res = await resumesAPI.tailorSingle(title, company, desc, url || null);
                showFeedback("Resume tailored successfully!", true);
                
                // Clear fields
                document.getElementById("tailor-title").value = "";
                document.getElementById("tailor-company").value = "";
                document.getElementById("tailor-url").value = "";
                document.getElementById("tailor-description").value = "";

                // Open newly tailored details
                await loadApplications();
                await loadAnalytics();
                await openAppDetails(res.application_id);
            } catch (err) {
                showFeedback(`Tailoring failed: ${err.message}`, false);
            } finally {
                btn.disabled = false;
                btn.innerHTML = `<i data-lucide="sparkles" class="w-4 h-4 mr-1"></i> Start Resume Optimisation`;
                lucide.createIcons();
                await loadTailorData();
            }
        });
    }

    // Bulk Tailor Form
    const bulkForm = document.getElementById("bulk-tailor-form");
    if (bulkForm) {
        bulkForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const btn = document.getElementById("btn-tailor-bulk");
            const searchUrl = document.getElementById("bulk-search-url").value.trim();
            const count = parseInt(document.getElementById("bulk-count").value) || 1;

            btn.disabled = true;
            btn.innerHTML = `<i data-lucide="refresh-cw" class="w-4 h-4 animate-spin mr-1"></i> Launching scraping worker...`;
            lucide.createIcons();

            try {
                await resumesAPI.tailorBulk(searchUrl, count);
                showFeedback("Bulk scraping triggered. Processing in background...", true);
                document.getElementById("bulk-search-url").value = "";
            } catch (err) {
                showFeedback(`Failed to launch scraper: ${err.message}`, false);
            } finally {
                btn.disabled = false;
                btn.innerHTML = `<i data-lucide="refresh-cw" class="w-4 h-4 mr-1"></i> Launch Scrape & Bulk Tailor`;
                lucide.createIcons();
                await loadTailorData();
            }
        });
    }
}

async function markAsApplied(appId) {
    try {
        await appsAPI.update(appId, { status: "APPLIED" });
        showFeedback("Application status updated to APPLIED and synced to Google Sheets.", true);
        closeAppDetails();
        await loadApplications();
        await loadAnalytics();
    } catch (err) {
        showFeedback(`Failed to mark as applied: ${err.message}`, false);
    }
}

async function loadSheetsTrackerIframe() {
    const container = document.getElementById("sheets-iframe-container");
    container.innerHTML = `<p class="text-sm text-slate-450 text-center py-12">Loading Google Sheet...</p>`;
    try {
        const config = await sheetsAPI.getConfig();
        if (config && config.spreadsheet_id) {
            container.innerHTML = `
                <iframe class="w-full h-full border-none opacity-95 hover:opacity-100 transition-opacity duration-300 rounded-xl" src="https://docs.google.com/spreadsheets/d/${config.spreadsheet_id}/preview?widget=true&headers=false"></iframe>
            `;
        } else {
            container.innerHTML = `
                <div class="flex flex-col items-center justify-center p-12 text-center h-full space-y-4 bg-slate-900/20 border border-slate-850 rounded-2xl">
                    <i data-lucide="file-spreadsheet" class="w-16 h-16 text-slate-600 animate-pulse"></i>
                    <h3 class="text-lg font-bold text-white">Google Sheet Tracker not Configured</h3>
                    <p class="text-sm text-slate-400 max-w-md">Please navigate to the Settings panel and enter your Spreadsheet ID to synchronize and view your spreadsheet directly inside this dashboard.</p>
                    <button onclick="switchTab('settings')" class="bg-brand-600 hover:bg-brand-500 text-white font-semibold px-4 py-2 rounded-xl text-xs transition-all shadow-md shadow-brand-500/10">Configure Settings</button>
                </div>
            `;
            lucide.createIcons();
        }
    } catch (err) {
        container.innerHTML = `<p class="text-sm text-rose-450 text-center py-12">Failed to check Sheets configuration: ${err.message}</p>`;
    }
}
