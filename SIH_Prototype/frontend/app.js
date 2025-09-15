// This is the "glue" that connects your frontend to your backend
const API_BASE_URL = "http://127.0.0.1:8000";

// --- STATE VARIABLES ---
let PRESET_JOBS = [];
let FORM_DATA = {};
let CURRENT_RANKED_LIST = [];   // Stores the full, unfiltered list from the API
let CURRENT_INTERNSHIP = {};    // Stores the details of the job being ranked
let FILTERED_CANDIDATE_LIST = []; // Stores the visible, filtered/sorted list

// --- NEW STATE for TomSelect (Dropdown Checklist) ---
let tsDegree, tsBranch, tsSkills; 

// --- NEW STATE for Allotment ---
let SELECTED_ALLOTMENT_JOBS = new Set();
let CURRENT_ALLOTMENT_LIST = []; // Stores the master allotment list
let FILTERED_ALLOTMENT_LIST = []; // Stores the visible/filtered allotment list


// --- Wait for the entire webpage (HTML) to load before running any JavaScript ---
document.addEventListener("DOMContentLoaded", () => {
    
    // --- Get references to all the important HTML elements ---
    const uploadForm = document.getElementById("upload-form");
    const csvFileInput = document.getElementById("csv-file");
    const uploadStatus = document.getElementById("upload-status");
    
    const tabButtons = document.querySelectorAll(".tab-button");
    const tabContents = document.querySelectorAll(".tab-content");
    
    const presetContainer = document.getElementById("preset-cards-container");
    const customForm = document.getElementById("custom-internship-form");
    const resultsContainer = document.getElementById("results-container");

    // --- NEW: Allotment element references ---
    const allotmentContainer = document.getElementById("allotment-cards-container");
    const generateAllotmentBtn = document.getElementById("generate-allotment-btn");
    const allotmentResultsContainer = document.getElementById("allotment-results-container");


    // --- 1. INITIALIZATION ---
    
    async function initializeApp() {
        try {
            const [presetsRes, formDataRes] = await Promise.all([
                fetch(`${API_BASE_URL}/api/presets`),
                fetch(`${API_BASE_URL}/api/form-data`)
            ]);
            if (!presetsRes.ok || !formDataRes.ok) throw new Error("Failed to load initial data from API.");

            PRESET_JOBS = await presetsRes.json();
            FORM_DATA = await formDataRes.json();

            populateFormDropdowns();
            renderPresetCards();
            renderAllotmentCards(); // NEW: Render cards for allotment tab

        } catch (error) {
            console.error("Failed to initialize app:", error);
            resultsContainer.innerHTML = `<p class="error">Error: Could not connect to backend at ${API_BASE_URL}. Is the server running?</p>`;
        }
    }

    /**
     * UPDATED: Now populates all dropdowns AND initializes TomSelect
     * for the multi-select dropdown checklists.
     */
    function populateFormDropdowns() {
        // Helper to populate a <select>
        const populateSelect = (selectId, optionsList, defaultSelection = null) => {
            const select = document.getElementById(selectId);
            if (!select) return;
            select.innerHTML = ''; // Clear existing options
            optionsList.forEach(option => {
                const optElement = document.createElement('option');
                optElement.value = option;
                optElement.textContent = option;
                if (Array.isArray(defaultSelection) && defaultSelection.includes(option)) {
                    optElement.selected = true;
                } else if (option === defaultSelection) {
                    optElement.selected = true;
                }
                select.appendChild(optElement);
            });
        };

        // Populate ALL dropdowns first (including the ones TomSelect will hide)
        populateSelect('state', FORM_DATA.indian_states, 'Telangana');
        populateSelect('degree', FORM_DATA.bachelors_degrees, ['B.TECH']);
        populateSelect('branch', FORM_DATA.all_branches, ['CS', 'IT']);
        populateSelect('skills', FORM_DATA.all_skills_list, ['PYTHON', 'AIML', 'SQL']);

        // NOW, initialize TomSelect on the multi-select inputs
        // This enhances the <select> elements into dropdown checklists
        tsDegree = new TomSelect('#degree', { plugins: ['remove_button'], placeholder: 'Select required degrees...' });
        tsBranch = new TomSelect('#branch', { plugins: ['remove_button'], placeholder: 'Select required branches...' });
        tsSkills = new TomSelect('#skills', { plugins: ['remove_button'], placeholder: 'Select required skills...' });
    }

    function renderPresetCards() {
        presetContainer.innerHTML = ""; // Clear old data
        PRESET_JOBS.forEach(job => {
            const card = document.createElement("div");
            card.className = "card";
            card.innerHTML = `
                <div>
                    <h3>${job.post}</h3>
                    <p><b>${job.company}</b> • ${job.city}, ${job.state}</p>
                    <div class="card-details">
                        <b>Offers:</b> ${job.offers} | <b>Degree:</b> ${job.degree.join(', ')}<br>
                        <b>Branch:</b> ${job.branch.length ? job.branch.join(', ') : 'Any'}<br>
                        <b>Skills:</b> ${job.skills.slice(0, 3).join(', ')}...
                    </div>
                </div>
                <button class="button-primary rank-button" data-key="${job.key}">Rank Candidates</button>
            `;
            presetContainer.appendChild(card);
        });

        document.querySelectorAll('.rank-button').forEach(button => {
            button.addEventListener('click', handlePresetRankClick);
        });
    }

    // --- 2. EVENT LISTENERS & HANDLERS ---

    uploadForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const file = csvFileInput.files[0];
        if (!file) return;
        const formData = new FormData();
        formData.append("file", file);

        uploadStatus.textContent = "Uploading...";
        uploadStatus.className = "status-message info";
        try {
            const response = await fetch(`${API_BASE_URL}/api/upload-csv`, { method: "POST", body: formData });
            const result = await response.json();
            if (!response.ok) throw new Error(result.detail || "Upload failed");
            
            uploadStatus.textContent = `Success! Loaded ${result.rows_loaded} candidates.`;
            uploadStatus.className = "status-message success";
        } catch (error) {
            console.error("Upload error:", error);
            uploadStatus.textContent = `Error: ${error.message}`;
            uploadStatus.className = "status-message error";
        }
    });

    tabButtons.forEach(button => {
        button.addEventListener("click", () => {
            tabButtons.forEach(btn => btn.classList.remove("active"));
            tabContents.forEach(content => content.classList.remove("active"));
            button.classList.add("active");
            document.getElementById(button.dataset.tab).classList.add("active");
            // Clear single-ranking results when switching tabs
            resultsContainer.innerHTML = "";
            allotmentResultsContainer.innerHTML = "";
        });
    });

    function handlePresetRankClick(e) {
        const jobKey = e.target.dataset.key;
        const jobData = PRESET_JOBS.find(j => j.key === jobKey);
        if (jobData) {
            rankCandidates(jobData);
        }
    }

    /**
     * UPDATED: Now reads values directly from TomSelect instances
     * using .getValue() instead of parsing selectedOptions.
     */
    customForm.addEventListener("submit", (e) => {
        e.preventDefault();
        
        const customJobData = {
            post: document.getElementById("post").value,
            company: document.getElementById("company").value,
            offers: parseInt(document.getElementById("offers").value, 10),
            city: document.getElementById("city").value,
            state: document.getElementById("state").value,
            // Read values from the TomSelect JS instances
            degree: tsDegree.getValue(),
            branch: tsBranch.getValue(),
            skills: tsSkills.getValue(),
            priority: [
                document.getElementById("p1").value,
                document.getElementById("p2").value,
                document.getElementById("p3").value,
                document.getElementById("p4").value,
            ]
        };
        rankCandidates(customJobData);
    });


    // --- 3. CORE API CALL (Single Ranking) ---

    async function rankCandidates(internshipData) {
        resultsContainer.innerHTML = `<p class="info">Ranking candidates for ${internshipData.post}...</p>`;
        resultsContainer.scrollIntoView({ behavior: 'smooth' });
        
        try {
            const response = await fetch(`${API_BASE_URL}/api/rank-custom`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(internshipData),
            });
            const result = await response.json();
            if (!response.ok) throw new Error(result.detail || "Ranking failed");
            
            CURRENT_RANKED_LIST = result.ranking;
            CURRENT_INTERNSHIP = internshipData;
            FILTERED_CANDIDATE_LIST = [...CURRENT_RANKED_LIST];
            
            displayFullResultsUI(internshipData);
            applyFiltersAndRedrawTable();

        } catch (error) {
            console.error("Ranking error:", error);
            resultsContainer.innerHTML = `<p class="error">Error: ${error.message}. Did you upload a candidate CSV?</p>`;
        }
    }


    // --- 4. SINGLE RANKING RESULTS UI (Unchanged) ---
    // (This whole section is unchanged from your original file)
    function displayFullResultsUI(internship) {
        const uniqueGenders = ["ALL", ...new Set(CURRENT_RANKED_LIST.map(c => c.Gender).filter(g => g))];
        const uniqueCategories = ["ALL", ...new Set(CURRENT_RANKED_LIST.map(c => c.Category).filter(c => c && !['GENERAL', ''].includes(c))), "GENERAL"];

        resultsContainer.innerHTML = `
            <div class="results-header">
                <h2>Ranking for: ${internship.post} at ${internship.company}</h2>
                <p>Highlighting top <strong>${internship.offers}</strong> potential matches. Use filters to refine the list.</p>
            </div>
            <div class="filter-grid" id="filter-controls">
                <div class="form-group">
                    <label for="filter-category">Filter by Category</label>
                    <select id="filter-category">
                        ${uniqueCategories.map(c => `<option value="${c}">${c}</option>`).join('')}
                    </select>
                </div>
                <div class="form-group">
                    <label for="filter-gender">Filter by Gender</label>
                    <select id="filter-gender">
                        ${uniqueGenders.map(g => `<option value="${g}">${g}</option>`).join('')}
                    </select>
                </div>
                <div class="form-group">
                    <label for="sort-by">Sort by</label>
                    <select id="sort-by">
                        <option value="Overall Match %" selected>Overall Match %</option>
                        <option value="Skills %">Skills %</option>
                        <option value="Education %">Education %</option>
                        <option value="Location %">Location %</option>
                        <option value="Interest %">Interest %</option>
                    </select>
                </div>
            </div>
            <div class="results-table-container" id="results-table-container"></div>
            <div class="submission-panel" id="submission-panel">
                <div id="selection-feedback"></div>
                <div class="metric-display" id="selection-metric">0 / ${internship.offers}</div>
                <button class="button-primary" id="submit-selection-btn">Submit Selections</button>
            </div>
            <div id="final-submission-message"></div>
        `;
        document.getElementById('filter-category').addEventListener('change', applyFiltersAndRedrawTable);
        document.getElementById('filter-gender').addEventListener('change', applyFiltersAndRedrawTable);
        document.getElementById('sort-by').addEventListener('change', applyFiltersAndRedrawTable);
        document.getElementById('submit-selection-btn').addEventListener('click', handleSubmitSelection);
        document.getElementById('results-table-container').addEventListener('change', (e) => {
            if (e.target.classList.contains('candidate-select-checkbox')) {
                updateSelectionCount();
            }
        });
    }
    function applyFiltersAndRedrawTable() {
        const category = document.getElementById('filter-category').value;
        const gender = document.getElementById('filter-gender').value;
        const sortBy = document.getElementById('sort-by').value;
        let filteredList = [...CURRENT_RANKED_LIST];
        if (category && category !== 'ALL') {
            filteredList = filteredList.filter(c => c.Category === category);
        }
        if (gender && gender !== 'ALL') {
            filteredList = filteredList.filter(c => c.Gender === gender);
        }
        filteredList.sort((a, b) => b[sortBy] - a[sortBy]);
        filteredList.forEach((item, index) => { item.Rank = index + 1; });
        FILTERED_CANDIDATE_LIST = filteredList;
        renderTable(FILTERED_CANDIDATE_LIST);
        updateSelectionCount();
    }
    function renderTable(candidates) {
        const tableContainer = document.getElementById('results-table-container');
        const offers = CURRENT_INTERNSHIP.offers;
        const headers = Object.keys(candidates[0] || {}).filter(h => h !== 'Gender' && h !== 'Category');
        let headerHtml = "<tr>" + headers.map(h => `<th>${h}</th>`).join("") + "</tr>";
        let rowsHtml = candidates.map((candidate) => {
            const isTopPick = candidate['Rank'] <= offers;
            const rowClass = isTopPick ? 'class="top-pick"' : '';
            const cellsHtml = headers.map(header => {
                let value = candidate[header];
                if (header === 'Select') {
                    return `<td><input type="checkbox" class="candidate-select-checkbox" data-name="${candidate.Name}" ${candidate.Select ? 'checked' : ''}></td>`;
                }
                if (header.includes('%')) { value = `${value}%`; }
                return `<td>${value}</td>`;
            }).join("");
            return `<tr ${rowClass}>${cellsHtml}</tr>`;
        }).join("");
        tableContainer.innerHTML = `
            <table class="results-table">
                <thead>${headerHtml}</thead>
                <tbody>${rowsHtml || `<tr><td colspan="${headers.length}">No candidates match the current filters.</td></tr>`}</tbody>
            </table>
        `;
    }
    function updateSelectionCount() {
        const checkedBoxes = document.querySelectorAll('#results-table-container .candidate-select-checkbox:checked');
        const numSelected = checkedBoxes.length;
        const offersLimit = CURRENT_INTERNSHIP.offers;
        document.getElementById('selection-metric').innerHTML = `${numSelected} / ${offersLimit}`;
        const feedbackEl = document.getElementById('selection-feedback');
        if (numSelected > offersLimit) {
            feedbackEl.innerHTML = `⚠️ Too many selected! Limit: ${offersLimit}`;
            feedbackEl.className = 'feedback-message error';
        } else if (numSelected === 0) {
            feedbackEl.innerHTML = `ℹ️ No candidates selected yet`;
            feedbackEl.className = 'feedback-message info';
        } else {
            feedbackEl.innerHTML = `✅ ${numSelected} candidates selected`;
            feedbackEl.className = 'feedback-message success';
        }
    }
    function handleSubmitSelection() {
        const checkedBoxes = document.querySelectorAll('#results-table-container .candidate-select-checkbox:checked');
        const numSelected = checkedBoxes.length;
        const offersLimit = CURRENT_INTERNSHIP.offers;
        const finalMessageEl = document.getElementById('final-submission-message');
        if (numSelected > offersLimit) {
            finalMessageEl.innerHTML = `<p class="feedback-message error">Error: You can only select up to ${offersLimit} candidates. Please uncheck some.</p>`;
            return;
        }
        if (numSelected === 0) {
            finalMessageEl.innerHTML = `<p class="feedback-message info">Please select at least one candidate.</p>`;
            return;
        }
        let selectedCandidateHtml = "";
        checkedBoxes.forEach(box => {
            const name = box.dataset.name;
            const candidate = FILTERED_CANDIDATE_LIST.find(c => c.Name === name);
            if (candidate) {
                selectedCandidateHtml += `<li><b>${candidate.Name}</b> (Match: ${candidate['Overall Match %']}%)</li>`;
            }
        });
        alert("Selections Submitted! 🎈🎈🎈");
        finalMessageEl.innerHTML = `
            <div class="submit-success-popup">
                <h3>✅ Selections Submitted!</h3>
                <p><b>Selected Candidates for ${CURRENT_INTERNSHIP.post}:</b></p>
                <ul>${selectedCandidateHtml}</ul>
            </div>
        `;
        finalMessageEl.scrollIntoView({ behavior: 'smooth' });
    }

    // --- 5. *** NEW SMART ALLOTMENT UI & LOGIC *** ---

    /**
     * Renders the preset job cards into the Allotment tab,
     * making them selectable instead of having a button.
     */
    function renderAllotmentCards() {
        allotmentContainer.innerHTML = ""; // Clear old data
        PRESET_JOBS.forEach(job => {
            const card = document.createElement("div");
            // Add 'selectable' class and a data-key
            card.className = "card selectable";
            card.dataset.key = job.key;
            card.innerHTML = `
                <div>
                    <h3>${job.post}</h3>
                    <p><b>${job.company}</b> • ${job.city}</p>
                    <div class="card-details">
                        <b>Offers: ${job.offers}</b><br>
                        <b>Degree:</b> ${job.degree.join(', ')}<br>
                        <b>Skills:</b> ${job.skills.slice(0, 3).join(', ')}...
                    </div>
                </div>
            `; // No button
            card.addEventListener('click', handleAllotmentCardClick);
            allotmentContainer.appendChild(card);
        });
    }

    /**
     * Handles clicking a job card in the Allotment tab.
     * Toggles its selection state and updates the global Set.
     */
    function handleAllotmentCardClick(e) {
        const card = e.currentTarget;
        const jobKey = card.dataset.key;
        if (SELECTED_ALLOTMENT_JOBS.has(jobKey)) {
            card.classList.remove("selected");
            SELECTED_ALLOTMENT_JOBS.delete(jobKey);
        } else {
            card.classList.add("selected");
            SELECTED_ALLOTMENT_JOBS.add(jobKey);
        }
    }

    // Add listener to the main "Generate Allotment" button
    generateAllotmentBtn.addEventListener('click', handleGenerateAllotment);

    /**
     * Main function to trigger the new backend allotment API.
     */
    async function handleGenerateAllotment() {
        if (SELECTED_ALLOTMENT_JOBS.size === 0) {
            allotmentResultsContainer.innerHTML = `<p class="feedback-message error">Please select at least one internship role to generate an allotment.</p>`;
            return;
        }

        const jobKeys = Array.from(SELECTED_ALLOTMENT_JOBS);
        allotmentResultsContainer.innerHTML = `<p class="feedback-message info">Generating smart allotment for ${jobKeys.length} roles... This may take a moment.</p>`;
        allotmentResultsContainer.scrollIntoView({ behavior: 'smooth' });

        try {
            const response = await fetch(`${API_BASE_URL}/api/generate-allotment`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ job_keys: jobKeys }),
            });
            const result = await response.json();
            if (!response.ok) throw new Error(result.detail || "Allotment failed");

            // Store results globally
            CURRENT_ALLOTMENT_LIST = result.allotment_list;
            FILTERED_ALLOTMENT_LIST = [...CURRENT_ALLOTMENT_LIST];
            
            // Render the results UI
            renderAllotmentResultsUI();
            
        } catch (error) {
            console.error("Allotment error:", error);
            allotmentResultsContainer.innerHTML = `<p class="feedback-message error">Error: ${error.message}. Did you upload a candidate CSV?</p>`;
        }
    }

    /**
     * Renders the *entire* allotment results UI, including filters and table.
     * This is separate from the single-job ranking UI.
     */
    function renderAllotmentResultsUI() {
        // Get unique filter values from the allotment list
        const uniqueGenders = ["ALL", ...new Set(CURRENT_ALLOTMENT_LIST.map(c => c.Gender).filter(g => g))];
        const uniqueCategories = ["ALL", ...new Set(CURRENT_ALLOTMENT_LIST.map(c => c.Category).filter(c => c && !['GENERAL', ''].includes(c))), "GENERAL"];
        const uniqueStatuses = ["ALL", "Allotted", "Waitlisted"];

        allotmentResultsContainer.innerHTML = `
            <div class="results-header">
                <h2>Master Allotment List</h2>
                <p>Showing all candidates. "Allotted" candidates are assigned to their best-fit job, respecting quotas. Others are "Waitlisted".</p>
            </div>
            
            <div class="filter-grid" id="allotment-filter-controls">
                <div class="form-group">
                    <label for="filter-allot-status">Filter by Status</label>
                    <select id="filter-allot-status">
                         ${uniqueStatuses.map(s => `<option value="${s}">${s}</option>`).join('')}
                    </select>
                </div>
                 <div class="form-group">
                    <label for="filter-allot-category">Filter by Category</label>
                    <select id="filter-allot-category">
                        ${uniqueCategories.map(c => `<option value="${c}">${c}</option>`).join('')}
                    </select>
                </div>
                <div class="form-group">
                    <label for="filter-allot-gender">Filter by Gender</label>
                    <select id="filter-allot-gender">
                        ${uniqueGenders.map(g => `<option value="${g}">${g}</option>`).join('')}
                    </select>
                </div>
            </div>
            
            <div class="results-table-container" id="allotment-table-container">
                </div>
        `;

        // Add listeners to the new filter dropdowns
        document.getElementById('filter-allot-status').addEventListener('change', applyAllotmentFiltersAndRedraw);
        document.getElementById('filter-allot-category').addEventListener('change', applyAllotmentFiltersAndRedraw);
        document.getElementById('filter-allot-gender').addEventListener('change', applyAllotmentFiltersAndRedraw);

        // Initial table render
        applyAllotmentFiltersAndRedraw();
    }

    /**
     * Reads allotment filters, filters the master list, and calls renderAllotmentTable().
     */
    function applyAllotmentFiltersAndRedraw() {
        const status = document.getElementById('filter-allot-status').value;
        const category = document.getElementById('filter-allot-category').value;
        const gender = document.getElementById('filter-allot-gender').value;

        let filteredList = [...CURRENT_ALLOTMENT_LIST]; // Start from master list

        if (status && status !== 'ALL') {
            filteredList = filteredList.filter(c => c.Status === status);
        }
        if (category && category !== 'ALL') {
            filteredList = filteredList.filter(c => c.Category === category);
        }
        if (gender && gender !== 'ALL') {
            filteredList = filteredList.filter(c => c.Gender === gender);
        }
        
        // Note: The list is already pre-sorted by the backend (Allotted first, then by score)
        FILTERED_ALLOTMENT_LIST = filteredList;
        renderAllotmentTable(FILTERED_ALLOTMENT_LIST);
    }

    /**
     * Renders *only* the HTML table for the allotment list.
     */
    function renderAllotmentTable(candidates) {
        const tableContainer = document.getElementById('allotment-table-container');
        if (!tableContainer) return; // Guard clause

        // Define headers (excluding hidden ones)
        const headers = Object.keys(candidates[0] || {}).filter(h => h !== 'Gender' && h !== 'Category');
        
        let headerHtml = "<tr>" + headers.map(h => `<th>${h}</th>`).join("") + "</tr>";

        let rowsHtml = candidates.map((candidate) => {
            // Highlight allotted rows
            const rowClass = candidate.Status === 'Allotted' ? 'class="top-pick"' : '';
            
            const cellsHtml = headers.map(header => {
                let value = candidate[header];
                if (header.includes('%')) {
                    value = `${value}%`; // Add % sign
                }
                 if (header === 'Status' && value === 'Waitlisted') {
                    return `<td style="color: var(--text-light);">${value}</td>`; // Style waitlisted text
                }
                 if (header === 'Allotted Job' && value === 'N/A') {
                     return `<td style="color: var(--text-light);">${value}</td>`;
                 }
                return `<td>${value}</td>`;
            }).join("");

            return `<tr ${rowClass}>${cellsHtml}</tr>`;
        }).join("");

        tableContainer.innerHTML = `
            <table class="results-table">
                <thead>${headerHtml}</thead>
                <tbody>${rowsHtml || `<tr><td colspan="${headers.length}">No candidates match the current filters.</td></tr>`}</tbody>
            </table>
        `;
    }

    // --- Finally, start the app! ---
    initializeApp();
});