// This is the "glue" that connects your frontend to your backend
const API_BASE_URL = "http://127.0.0.1:8000";

// --- STATE VARIABLES ---
// We must store data globally to manage filters and selections, just like Streamlit
let PRESET_JOBS = [];
let FORM_DATA = {};
let CURRENT_RANKED_LIST = [];   // Stores the full, unfiltered list from the API
let CURRENT_INTERNSHIP = {};    // Stores the details of the job being ranked
let FILTERED_CANDIDATE_LIST = []; // Stores the visible, filtered/sorted list


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

            renderPresetCards();
            populateFormDropdowns();

        } catch (error) {
            console.error("Failed to initialize app:", error);
            resultsContainer.innerHTML = `<p class="error">Error: Could not connect to backend at ${API_BASE_URL}. Is the server running?</p>`;
        }
    }

    function populateFormDropdowns() {
        // Helper to populate a <select>
        const populateSelect = (selectId, optionsList, defaultSelection = null) => {
            const select = document.getElementById(selectId);
            if (!select) return;
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

        populateSelect('state', FORM_DATA.indian_states, 'Telangana');
        populateSelect('degree', FORM_DATA.bachelors_degrees, ['B.TECH']);
        populateSelect('branch', FORM_DATA.all_branches, ['CS', 'IT']);
        populateSelect('skills', FORM_DATA.all_skills_list, ['PYTHON', 'AIML', 'SQL', 'COMMUNICATION']);
    }

    function renderPresetCards() {
        presetContainer.innerHTML = ""; // Clear old data
        PRESET_JOBS.forEach(job => {
            const card = document.createElement("div");
            card.className = "card";
            // Updated card HTML to match new Streamlit style
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
        });
    });

    function handlePresetRankClick(e) {
        const jobKey = e.target.dataset.key;
        const jobData = PRESET_JOBS.find(j => j.key === jobKey);
        if (jobData) {
            rankCandidates(jobData);
        }
    }

    customForm.addEventListener("submit", (e) => {
        e.preventDefault();
        const getMultiSelectValues = (id) => Array.from(document.getElementById(id).selectedOptions).map(opt => opt.value);
        
        const customJobData = {
            post: document.getElementById("post").value,
            company: document.getElementById("company").value,
            offers: parseInt(document.getElementById("offers").value, 10),
            city: document.getElementById("city").value,
            state: document.getElementById("state").value,
            degree: getMultiSelectValues("degree"),
            branch: getMultiSelectValues("branch"),
            skills: getMultiSelectValues("skills"),
            priority: [
                document.getElementById("p1").value,
                document.getElementById("p2").value,
                document.getElementById("p3").value,
                document.getElementById("p4").value,
            ]
        };
        rankCandidates(customJobData);
    });


    // --- 3. CORE API CALL ---

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
            
            // --- NEW: Store data globally and render the full results UI ---
            CURRENT_RANKED_LIST = result.ranking;
            CURRENT_INTERNSHIP = internshipData;
            FILTERED_CANDIDATE_LIST = [...CURRENT_RANKED_LIST]; // At first, filtered list is the full list
            
            displayFullResultsUI(internshipData);
            applyFiltersAndRedrawTable(); // Draw the initial table

        } catch (error) {
            console.error("Ranking error:", error);
            resultsContainer.innerHTML = `<p class="error">Error: ${error.message}. Did you upload a candidate CSV?</p>`;
        }
    }


    // --- 4. NEW RESULTS, FILTERING, & SUBMISSION LOGIC ---

    /**
     * This is the new master function that builds the *entire* results UI,
     * including filters, the table container, and the submission panel.
     * It's called ONCE per ranking.
     */
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

            <div class="results-table-container" id="results-table-container">
                </div>

            <div class="submission-panel" id="submission-panel">
                <div id="selection-feedback">
                    </div>
                <div class="metric-display" id="selection-metric">0 / ${internship.offers}</div>
                <button class="button-primary" id="submit-selection-btn">Submit Selections</button>
            </div>
            
            <div id="final-submission-message"></div>
        `;

        // --- Add event listeners to the new controls ---
        document.getElementById('filter-category').addEventListener('change', applyFiltersAndRedrawTable);
        document.getElementById('filter-gender').addEventListener('change', applyFiltersAndRedrawTable);
        document.getElementById('sort-by').addEventListener('change', applyFiltersAndRedrawTable);
        document.getElementById('submit-selection-btn').addEventListener('click', handleSubmitSelection);
        
        // Use event delegation for checkboxes (since they will be redrawn)
        document.getElementById('results-table-container').addEventListener('change', (e) => {
            if (e.target.classList.contains('candidate-select-checkbox')) {
                updateSelectionCount();
            }
        });
    }

    /**
     * This function reads the filter dropdowns, filters the master list, 
     * sorts it, and then calls renderTable() to draw it.
     * This is called ANY time a filter or sort option is changed.
     */
    function applyFiltersAndRedrawTable() {
        const category = document.getElementById('filter-category').value;
        const gender = document.getElementById('filter-gender').value;
        const sortBy = document.getElementById('sort-by').value;

        // 1. Filter
        let filteredList = [...CURRENT_RANKED_LIST]; // Start from the master list
        if (category && category !== 'ALL') {
            filteredList = filteredList.filter(c => c.Category === category);
        }
        if (gender && gender !== 'ALL') {
            filteredList = filteredList.filter(c => c.Gender === gender);
        }

        // 2. Sort
        filteredList.sort((a, b) => {
            // Sort by the chosen column, descending. 
            // All values are numbers (percentages)
            return b[sortBy] - a[sortBy];
        });

        // 3. Re-Rank
        // The visible rank must be updated based on the filtered/sorted view
        filteredList.forEach((item, index) => {
            item.Rank = index + 1; // Update rank dynamically
        });
        
        FILTERED_CANDIDATE_LIST = filteredList; // Store the currently visible list

        // 4. Redraw the table
        renderTable(FILTERED_CANDIDATE_LIST);
        // 5. Update counts (in case any previously-checked items are now hidden)
        updateSelectionCount();
    }

    /**
     * This function ONLY builds the HTML for the table and injects it.
     */
    function renderTable(candidates) {
        const tableContainer = document.getElementById('results-table-container');
        const offers = CURRENT_INTERNSHIP.offers;
        
        // Get headers from the first candidate, excluding hidden fields
        const headers = Object.keys(candidates[0] || {}).filter(h => h !== 'Gender' && h !== 'Category');
        
        let headerHtml = "<tr>" + headers.map(h => `<th>${h}</th>`).join("") + "</tr>";

        let rowsHtml = candidates.map((candidate) => {
            const isTopPick = candidate['Rank'] <= offers;
            const rowClass = isTopPick ? 'class="top-pick"' : '';
            
            const cellsHtml = headers.map(header => {
                let value = candidate[header];
                if (header === 'Select') {
                    // This data-name links the checkbox to the unique candidate name
                    return `<td><input type="checkbox" class="candidate-select-checkbox" data-name="${candidate.Name}" ${candidate.Select ? 'checked' : ''}></td>`;
                }
                if (header.includes('%')) {
                    value = `${value}%`; // Add % sign back
                }
                return `<td>${value}</td>`;
            }).join("");

            return `<tr ${rowClass}>${cellsHtml}</tr>`;
        }).join("");

        tableContainer.innerHTML = `
            <table class="results-table">
                <thead>${headerHtml}</thead>
                <tbody>${rowsHtml || '<tr><td colspan="${headers.length}">No candidates match the current filters.</td></tr>'}</tbody>
            </table>
        `;
    }

    /**
     * Checks how many boxes are selected and updates the feedback panel.
     * Called every time a checkbox is clicked.
     */
    function updateSelectionCount() {
        const checkedBoxes = document.querySelectorAll('#results-table-container .candidate-select-checkbox:checked');
        const numSelected = checkedBoxes.length;
        const offersLimit = CURRENT_INTERNSHIP.offers;

        // Update the metric
        document.getElementById('selection-metric').innerHTML = `${numSelected} / ${offersLimit}`;

        // Update the feedback message
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

    /**
     * Final submission logic, runs when the "Submit" button is clicked.
     */
    function handleSubmitSelection() {
        const checkedBoxes = document.querySelectorAll('#results-table-container .candidate-select-checkbox:checked');
        const numSelected = checkedBoxes.length;
        const offersLimit = CURRENT_INTERNSHIP.offers;

        const finalMessageEl = document.getElementById('final-submission-message');

        // Validation logic from Streamlit
        if (numSelected > offersLimit) {
            finalMessageEl.innerHTML = `<p class="feedback-message error">Error: You can only select up to ${offersLimit} candidates. Please uncheck some.</p>`;
            return;
        }
        if (numSelected === 0) {
            finalMessageEl.innerHTML = `<p class="feedback-message info">Please select at least one candidate.</p>`; // Changed from warning to info
            return;
        }

        // Success! Get the list of names.
        let selectedCandidateHtml = "";
        checkedBoxes.forEach(box => {
            const name = box.dataset.name;
            // Find the full candidate object from the (visible) filtered list to get their match score
            const candidate = FILTERED_CANDIDATE_LIST.find(c => c.Name === name);
            if (candidate) {
                selectedCandidateHtml += `<li><b>${candidate.Name}</b> (Match: ${candidate['Overall Match %']}%)</li>`;
            }
        });

        // Mimic st.success + st.balloons + st.write
        alert("Selections Submitted! 🎈🎈🎈"); // Mimics st.balloons()
        finalMessageEl.innerHTML = `
            <div class="submit-success-popup">
                <h3>✅ Selections Submitted!</h3>
                <p><b>Selected Candidates for ${CURRENT_INTERNSHIP.post}:</b></p>
                <ul>
                    ${selectedCandidateHtml}
                </ul>
            </div>
        `;
        finalMessageEl.scrollIntoView({ behavior: 'smooth' });
    }

    // --- Finally, start the app! ---
    initializeApp();
});