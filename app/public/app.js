/**
 * LLM Security Assessment Framework — Node.js Frontend Client (app.js)
 */

document.addEventListener('DOMContentLoaded', () => {
    initNavigation();
    loadOverview();
    initDatasetExplorer();
    initLiveDetector();
    initAssessmentEngine();
    initModelPerformance();
    initRiskCalculator();
    initReportsBrowser();
});

// ─────────────────────────────────────────────────────────────
// 1. Navigation & Page Routing
// ─────────────────────────────────────────────────────────────
function initNavigation() {
    const navItems = document.querySelectorAll('.nav-item');
    const sections = document.querySelectorAll('.page-section');
    const pageTitle = document.getElementById('page-title');
    const pageSubtitle = document.getElementById('page-subtitle');

    const pageMeta = {
        overview: {
            title: '📊 Executive Overview',
            subtitle: 'Security Assessment Platform for Prompt Injections, Jailbreaks & Model Auditing'
        },
        dataset: {
            title: '🔍 Dataset Explorer',
            subtitle: 'Explore 1,984 deduplicated adversarial prompts across 5 attack classes'
        },
        detector: {
            title: '🎯 Live Attack Detector',
            subtitle: 'Real-time prompt safety classifier using Preflight Heuristics & Transformer Models'
        },
        assessment: {
            title: '🤖 Target LLM Assessment',
            subtitle: 'Automated Red-Teaming Engine: Test LLMs against adversarial prompts and measure ASR'
        },
        performance: {
            title: '📈 Model Performance',
            subtitle: 'Evaluation benchmarks: TF-IDF vs. DistilBERT vs. DeBERTa-v3 across test splits'
        },
        risk: {
            title: '⚠️ Risk Scoring & Analysis',
            subtitle: 'Dynamic multi-factor risk quantification based on attack severity and target breach'
        },
        reports: {
            title: '📑 Security Reports & Artifacts',
            subtitle: 'Inspect generated CSV assessment logs, JSON metrics, and summary data'
        }
    };

    function switchPage(pageId) {
        navItems.forEach(item => {
            if (item.getAttribute('data-page') === pageId) {
                item.classList.add('active');
            } else {
                item.classList.remove('active');
            }
        });

        sections.forEach(sec => {
            if (sec.id === `page-${pageId}`) {
                sec.classList.add('active');
            } else {
                sec.classList.remove('active');
            }
        });

        if (pageMeta[pageId]) {
            pageTitle.textContent = pageMeta[pageId].title;
            pageSubtitle.textContent = pageMeta[pageId].subtitle;
        }

        window.location.hash = pageId;
    }

    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const pageId = item.getAttribute('data-page');
            switchPage(pageId);
        });
    });

    // Check URL hash on load
    const currentHash = window.location.hash.replace('#', '');
    if (currentHash && pageMeta[currentHash]) {
        switchPage(currentHash);
    }
}

// ─────────────────────────────────────────────────────────────
// 2. Executive Overview
// ─────────────────────────────────────────────────────────────
let taxonomyChartInstance = null;
let sourceChartInstance = null;

async function loadOverview() {
    try {
        const res = await fetch('/api/overview');
        const data = await res.json();

        // Populate summary stats
        document.getElementById('stat-total-prompts').textContent = data.totalPrompts.toLocaleString();
        document.getElementById('stat-categories').textContent = `${data.categoriesCount} Classes`;
        document.getElementById('stat-best-known').textContent = data.bestF1Known;
        document.getElementById('stat-best-novel').textContent = data.bestF1Novel;

        // Populate benchmark table
        const tbody = document.querySelector('#overview-benchmark-table tbody');
        if (data.baselineMetrics && data.baselineMetrics.length > 0) {
            tbody.innerHTML = '';
            data.baselineMetrics.forEach(row => {
                const tr = document.createElement('tr');
                const f1 = parseFloat(row.f1_score);
                const f1Pct = !isNaN(f1) ? (f1 * 100).toFixed(2) + '%' : row.f1_score;
                const acc = parseFloat(row.accuracy);
                const accPct = !isNaN(acc) ? (acc * 100).toFixed(2) + '%' : row.accuracy;
                const prec = parseFloat(row.precision);
                const precPct = !isNaN(prec) ? (prec * 100).toFixed(2) + '%' : row.precision;
                const rec = parseFloat(row.recall);
                const recPct = !isNaN(rec) ? (rec * 100).toFixed(2) + '%' : row.recall;

                tr.innerHTML = `
                    <td><strong>${row.model}</strong></td>
                    <td><span class="badge ${row.split === 'test_known' ? 'badge-info' : 'badge-warning'}">${row.split}</span></td>
                    <td>${accPct}</td>
                    <td>${precPct}</td>
                    <td>${recPct}</td>
                    <td><strong class="text-accent">${f1Pct}</strong></td>
                `;
                tbody.appendChild(tr);
            });
        }

        // Render Charts
        renderOverviewCharts(data.categoryCounts, data.sourceCounts);
    } catch (err) {
        console.error('Error loading overview:', err);
    }
}

function renderOverviewCharts(categoryCounts, sourceCounts) {
    // Taxonomy Chart (Doughnut)
    const taxCtx = document.getElementById('overviewTaxonomyChart');
    if (taxCtx && categoryCounts) {
        if (taxonomyChartInstance) taxonomyChartInstance.destroy();

        const labels = Object.keys(categoryCounts);
        const values = Object.values(categoryCounts);

        taxonomyChartInstance = new Chart(taxCtx, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: values,
                    backgroundColor: [
                        '#ef4444', // Jailbreak
                        '#f59e0b', // Prompt Injection
                        '#8b5cf6', // Prompt Leakage
                        '#10b981', // Benign
                        '#06b6d4'  // Indirect
                    ]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'bottom' }
                }
            }
        });
    }

    // Source Chart (Bar)
    const srcCtx = document.getElementById('overviewSourceChart');
    if (srcCtx && sourceCounts) {
        if (sourceChartInstance) sourceChartInstance.destroy();

        const labels = Object.keys(sourceCounts);
        const values = Object.values(sourceCounts);

        sourceChartInstance = new Chart(srcCtx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Prompts Count',
                    data: values,
                    backgroundColor: '#2563eb'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    y: { beginAtZero: true }
                }
            }
        });
    }
}

// ─────────────────────────────────────────────────────────────
// 3. Dataset Explorer
// ─────────────────────────────────────────────────────────────
let datasetCurrentPage = 1;
const datasetPageLimit = 20;

function initDatasetExplorer() {
    const filterBtn = document.getElementById('dataset-filter-btn');
    const searchInput = document.getElementById('dataset-search');
    const sourceSelect = document.getElementById('dataset-source-filter');
    const labelSelect = document.getElementById('dataset-label-filter');
    const prevBtn = document.getElementById('btn-prev-page');
    const nextBtn = document.getElementById('btn-next-page');

    filterBtn.addEventListener('click', () => {
        datasetCurrentPage = 1;
        fetchDatasetPage();
    });

    searchInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            datasetCurrentPage = 1;
            fetchDatasetPage();
        }
    });

    prevBtn.addEventListener('click', () => {
        if (datasetCurrentPage > 1) {
            datasetCurrentPage--;
            fetchDatasetPage();
        }
    });

    nextBtn.addEventListener('click', () => {
        datasetCurrentPage++;
        fetchDatasetPage();
    });

    // Initial load
    fetchDatasetPage(true);
}

async function fetchDatasetPage(populateFilters = false) {
    const source = document.getElementById('dataset-source-filter').value;
    const label = document.getElementById('dataset-label-filter').value;
    const search = document.getElementById('dataset-search').value.trim();

    const queryParams = new URLSearchParams({
        page: datasetCurrentPage,
        limit: datasetPageLimit,
        source: source || 'all',
        label: label || 'all',
        search: search || ''
    });

    try {
        const res = await fetch(`/api/dataset?${queryParams.toString()}`);
        const data = await res.json();

        // Populate dropdowns once
        if (populateFilters) {
            const srcSel = document.getElementById('dataset-source-filter');
            data.availableSources.forEach(s => {
                const opt = document.createElement('option');
                opt.value = s;
                opt.textContent = s;
                srcSel.appendChild(opt);
            });

            const lblSel = document.getElementById('dataset-label-filter');
            data.availableLabels.forEach(l => {
                const opt = document.createElement('option');
                opt.value = l;
                opt.textContent = l;
                lblSel.appendChild(opt);
            });
        }

        // Render table
        const tbody = document.querySelector('#dataset-table tbody');
        tbody.innerHTML = '';

        if (!data.data || data.data.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="text-center">No prompts found matching current filters.</td></tr>';
        } else {
            data.data.forEach(r => {
                const tr = document.createElement('tr');
                const isMal = (r.label === 'malicious');
                const badgeClass = isMal ? 'badge-danger' : 'badge-success';

                tr.innerHTML = `
                    <td><code>${r.sample_id || 'N/A'}</code></td>
                    <td title="${r.prompt || ''}">${(r.prompt || '').substring(0, 110)}${(r.prompt && r.prompt.length > 110) ? '...' : ''}</td>
                    <td><span class="badge ${badgeClass}">${r.label || 'malicious'}</span></td>
                    <td><strong>${r.unified_label || r.attack_type || 'Unknown'}</strong></td>
                    <td><span class="badge badge-info">${r.source || 'Curated'}</span></td>
                    <td>${r.split || 'train'}</td>
                `;
                tbody.appendChild(tr);
            });
        }

        // Update pagination
        document.getElementById('dataset-page-info').textContent =
            `Showing ${data.data.length} of ${data.total.toLocaleString()} prompts (Page ${data.page} of ${data.totalPages || 1})`;
        document.getElementById('current-page-display').textContent = `Page ${data.page}`;
        document.getElementById('btn-prev-page').disabled = (data.page <= 1);
        document.getElementById('btn-next-page').disabled = (data.page >= data.totalPages);

    } catch (err) {
        console.error('Error fetching dataset:', err);
    }
}

// ─────────────────────────────────────────────────────────────
// 4. Live Attack Detector
// ─────────────────────────────────────────────────────────────
function initLiveDetector() {
    const form = document.getElementById('detector-form');
    const promptInput = document.getElementById('detector-prompt');
    const modelSelect = document.getElementById('detector-model');
    const scanBtn = document.getElementById('btn-scan-prompt');

    // Quick chip buttons
    document.querySelectorAll('.btn-chip').forEach(chip => {
        chip.addEventListener('click', () => {
            promptInput.value = chip.getAttribute('data-sample');
            form.dispatchEvent(new Event('submit'));
        });
    });

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const prompt = promptInput.value.trim();
        if (!prompt) return;

        const model = modelSelect.value;
        scanBtn.disabled = true;
        scanBtn.textContent = '⏳ Scanning...';

        document.getElementById('detector-placeholder').style.display = 'none';
        document.getElementById('detector-result').style.display = 'block';

        try {
            const res = await fetch('/api/detect', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ prompt, model })
            });
            const data = await res.json();

            // Populate result
            const banner = document.getElementById('verdict-banner');
            const icon = document.getElementById('verdict-icon');
            const title = document.getElementById('verdict-title');
            const subtitle = document.getElementById('verdict-subtitle');

            if (data.is_attack) {
                banner.className = 'verdict-banner verdict-attack';
                icon.textContent = '⚠️';
                title.textContent = 'ATTACK DETECTED';
                subtitle.textContent = 'Flagged as Malicious Prompt Injection / Jailbreak';
            } else {
                banner.className = 'verdict-banner verdict-benign';
                icon.textContent = '✅';
                title.textContent = 'PROMPT BENIGN';
                subtitle.textContent = 'Passed Security Verification (Safe)';
            }

            document.getElementById('res-label').textContent = (data.label || 'Unknown').toUpperCase();
            const confPct = Math.round((data.confidence || 0.5) * 100);
            document.getElementById('res-confidence').textContent = `${confPct}%`;
            document.getElementById('confidence-bar').style.width = `${confPct}%`;
            document.getElementById('confidence-bar').style.backgroundColor = data.is_attack ? '#ef4444' : '#10b981';

            // Preflight
            if (data.preflight) {
                const pfFlag = document.getElementById('res-preflight-flag');
                pfFlag.textContent = data.preflight.flagged ? 'FLAGGED' : 'PASSED';
                pfFlag.className = `badge ${data.preflight.flagged ? 'badge-danger' : 'badge-success'}`;
                document.getElementById('res-preflight-entropy').textContent = data.preflight.entropy || 'N/A';
                document.getElementById('res-preflight-reason').textContent = data.preflight.reason || 'Clean';
            }

            document.getElementById('res-raw-json').textContent = JSON.stringify(data, null, 2);

        } catch (err) {
            console.error('Detector error:', err);
        } finally {
            scanBtn.disabled = false;
            scanBtn.textContent = '🛡️ Run Security Scan';
        }
    });
}

// ─────────────────────────────────────────────────────────────
// 5. Target LLM Assessment Engine
// ─────────────────────────────────────────────────────────────
function initAssessmentEngine() {
    const form = document.getElementById('assessment-form');
    const targetType = document.getElementById('target-type');
    const apiKeyGroup = document.getElementById('api-key-group');
    const loadingBox = document.getElementById('assessment-loading');
    const resultsCard = document.getElementById('assessment-results-card');
    const runBtn = document.getElementById('btn-run-assessment');

    targetType.addEventListener('change', () => {
        const val = targetType.value;
        if (['gemini', 'groq', 'api'].includes(val)) {
            apiKeyGroup.style.display = 'block';
        } else {
            apiKeyGroup.style.display = 'none';
        }
    });

    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const payload = {
            target: targetType.value,
            security_level: document.getElementById('target-security').value,
            sample_size: parseInt(document.getElementById('sample-size').value, 10),
            detector: document.getElementById('assess-detector').value,
            api_key: document.getElementById('target-api-key').value.trim()
        };

        runBtn.disabled = true;
        loadingBox.style.display = 'block';
        resultsCard.style.display = 'none';

        try {
            const res = await fetch('/api/assess', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const data = await res.json();

            loadingBox.style.display = 'none';

            if (data.status === 'success') {
                resultsCard.style.display = 'block';
                document.getElementById('res-asr').textContent = `${data.asr}%`;
                document.getElementById('res-refusal').textContent = `${data.refusal_rate}%`;
                document.getElementById('assessment-run-meta').textContent =
                    `Target: ${data.target.toUpperCase()} (${data.security_level}) • Detector: ${data.detector} • Samples: ${data.sample_size}`;

                const tbody = document.querySelector('#assessment-results-table tbody');
                tbody.innerHTML = '';

                data.records.forEach((r, idx) => {
                    const tr = document.createElement('tr');
                    const outcomeBadge = r.attack_successful
                        ? '<span class="badge badge-danger">BREACHED</span>'
                        : '<span class="badge badge-success">BLOCKED (REFUSED)</span>';
                    const detBadge = r.detector_flag
                        ? '<span class="badge badge-warning">FLAGGED</span>'
                        : '<span class="badge badge-info">CLEAN</span>';

                    tr.innerHTML = `
                        <td>${idx + 1}</td>
                        <td title="${r.prompt}">${r.prompt}</td>
                        <td><strong>${r.attack_type}</strong></td>
                        <td>${detBadge}</td>
                        <td title="${r.model_response}">${(r.model_response || '').substring(0, 90)}...</td>
                        <td>${outcomeBadge}</td>
                        <td><span class="badge tier-${r.risk_tier.toLowerCase()}">${r.risk_tier}</span></td>
                    `;
                    tbody.appendChild(tr);
                });
            } else {
                alert(`Assessment execution failed: ${data.error || 'Check logs'}`);
            }
        } catch (err) {
            console.error('Assessment run error:', err);
            alert(`Assessment error: ${err.message}`);
        } finally {
            runBtn.disabled = false;
            loadingBox.style.display = 'none';
        }
    });
}

// ─────────────────────────────────────────────────────────────
// 6. Model Performance & Comparison
// ─────────────────────────────────────────────────────────────
async function initModelPerformance() {
    try {
        const res = await fetch('/api/metrics');
        const data = await res.json();

        // Populate baseline table
        const baseTbody = document.querySelector('#perf-baseline-table tbody');
        baseTbody.innerHTML = '';
        (data.baseline || []).forEach(row => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td><strong>${row.model}</strong></td>
                <td><span class="badge ${row.split === 'test_known' ? 'badge-info' : 'badge-warning'}">${row.split}</span></td>
                <td>${(parseFloat(row.accuracy) * 100).toFixed(2)}%</td>
                <td>${(parseFloat(row.precision) * 100).toFixed(2)}%</td>
                <td>${(parseFloat(row.recall) * 100).toFixed(2)}%</td>
                <td><strong class="text-accent">${(parseFloat(row.f1_score) * 100).toFixed(2)}%</strong></td>
            `;
            baseTbody.appendChild(tr);
        });

        // Populate DeBERTa table
        const debTbody = document.querySelector('#perf-deberta-table tbody');
        debTbody.innerHTML = '';
        (data.deberta || []).forEach(row => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td><strong>${row.model}</strong></td>
                <td><span class="badge ${row.split === 'test_known' ? 'badge-info' : 'badge-warning'}">${row.split}</span></td>
                <td>${(parseFloat(row.accuracy) * 100).toFixed(2)}%</td>
                <td>${(parseFloat(row.precision) * 100).toFixed(2)}%</td>
                <td>${(parseFloat(row.recall) * 100).toFixed(2)}%</td>
                <td><strong class="text-accent">${(parseFloat(row.f1_score) * 100).toFixed(2)}%</strong></td>
            `;
            debTbody.appendChild(tr);
        });

    } catch (err) {
        console.error('Error fetching metrics:', err);
    }
}

// ─────────────────────────────────────────────────────────────
// 7. Dynamic Risk Scoring Calculator
// ─────────────────────────────────────────────────────────────
function initRiskCalculator() {
    const catSelect = document.getElementById('risk-category');
    const successCheckbox = document.getElementById('risk-attack-success');
    const detectedCheckbox = document.getElementById('risk-detected');
    const confSlider = document.getElementById('risk-confidence');
    const confVal = document.getElementById('risk-conf-val');

    confSlider.addEventListener('input', () => {
        confVal.textContent = parseFloat(confSlider.value).toFixed(2);
        calculateRisk();
    });

    catSelect.addEventListener('change', calculateRisk);
    successCheckbox.addEventListener('change', calculateRisk);
    detectedCheckbox.addEventListener('change', calculateRisk);

    async function calculateRisk() {
        const payload = {
            category: catSelect.value,
            attack_successful: successCheckbox.checked,
            detector_confidence: parseFloat(confSlider.value),
            is_detected_by_security: detectedCheckbox.checked
        };

        try {
            const res = await fetch('/api/risk/calculate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const data = await res.json();

            // Update UI
            document.getElementById('risk-number').textContent = data.risk_score.toFixed(2);
            const circle = document.getElementById('risk-score-circle');
            const badge = document.getElementById('risk-tier-badge');

            circle.className = `risk-circle risk-${data.risk_tier.toLowerCase()}`;
            badge.className = `badge-tier tier-${data.risk_tier.toLowerCase()}`;
            badge.textContent = `${data.risk_tier} RISK`;

            // Weights breakdown
            document.getElementById('w-sev').textContent = (data.severity_weight * 0.35).toFixed(3);
            document.getElementById('w-success').textContent = (data.attack_successful ? 0.45 : 0.0).toFixed(3);
            document.getElementById('w-evasion').textContent = (data.evasion_penalty * 0.20).toFixed(3);

        } catch (err) {
            console.error('Error calculating risk:', err);
        }
    }

    // Initial calculation
    calculateRisk();
}

// ─────────────────────────────────────────────────────────────
// 8. Security Reports Browser
// ─────────────────────────────────────────────────────────────
async function initReportsBrowser() {
    const select = document.getElementById('reports-select');
    const loadBtn = document.getElementById('btn-load-report');
    const viewContainer = document.getElementById('report-view-container');
    const title = document.getElementById('viewing-report-title');
    const count = document.getElementById('viewing-report-count');

    try {
        const res = await fetch('/api/reports');
        const data = await res.json();

        select.innerHTML = '<option value="">-- Choose a report artifact --</option>';
        (data.reports || []).forEach(r => {
            const opt = document.createElement('option');
            opt.value = r.filename;
            opt.textContent = `${r.filename} (${(r.size / 1024).toFixed(1)} KB)`;
            select.appendChild(opt);
        });
    } catch (err) {
        console.error('Error loading reports list:', err);
    }

    loadBtn.addEventListener('click', async () => {
        const filename = select.value;
        if (!filename) return;

        if (filename.endsWith('.pdf')) {
            window.open(`/api/reports/${filename}`, '_blank');
            return;
        }

        try {
            const res = await fetch(`/api/reports/${filename}`);
            const report = await res.json();

            viewContainer.style.display = 'block';
            title.textContent = `File: ${report.filename}`;
            count.textContent = `${report.totalRows || (report.data ? report.data.length : 0)} rows`;

            const table = document.getElementById('report-data-table');
            const thead = table.querySelector('thead');
            const tbody = table.querySelector('tbody');

            thead.innerHTML = '';
            tbody.innerHTML = '';

            const rows = report.data || [];
            if (rows.length > 0 && typeof rows[0] === 'object') {
                const headers = Object.keys(rows[0]);
                const headerRow = document.createElement('tr');
                headers.forEach(h => {
                    const th = document.createElement('th');
                    th.textContent = h;
                    headerRow.appendChild(th);
                });
                thead.appendChild(headerRow);

                rows.slice(0, 50).forEach(r => {
                    const tr = document.createElement('tr');
                    headers.forEach(h => {
                        const td = document.createElement('td');
                        td.textContent = r[h];
                        tr.appendChild(td);
                    });
                    tbody.appendChild(tr);
                });
            }
        } catch (err) {
            console.error('Error reading report content:', err);
        }
    });
}

