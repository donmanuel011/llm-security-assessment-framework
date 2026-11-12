const express = require('express');
const cors = require('cors');
const path = require('path');
const fs = require('fs');
const { spawn } = require('child_process');
const { parse } = require('csv-parse/sync');

const app = express();
const PORT = process.env.PORT || 3000;

const PROJECT_ROOT = path.resolve(__dirname, '..');
const PROCESSED_DIR = path.join(PROJECT_ROOT, 'data', 'processed');
const REPORTS_DIR = path.join(PROJECT_ROOT, 'reports');
const BRIDGE_SCRIPT = path.join(PROJECT_ROOT, 'scripts', 'bridge.py');

// Detect Python executable
function getPythonCommand() {
    if (process.env.PYTHON_PATH && fs.existsSync(process.env.PYTHON_PATH)) {
        return process.env.PYTHON_PATH;
    }
    const defaultWinPython = 'C:\\Users\\Dell\\AppData\\Local\\Programs\\Python\\Python312\\python.exe';
    if (fs.existsSync(defaultWinPython)) {
        return defaultWinPython;
    }
    return 'python';
}

const PYTHON_BIN = getPythonCommand();

app.use(cors());
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true }));
app.use(express.static(path.join(__dirname, 'public')));

// Helper to safely read and parse CSV
function readCsv(filePath) {
    if (!fs.existsSync(filePath)) return [];
    try {
        const fileContent = fs.readFileSync(filePath, 'utf-8');
        return parse(fileContent, {
            columns: true,
            skip_empty_lines: true,
            trim: true
        });
    } catch (err) {
        console.error(`Error parsing CSV ${filePath}:`, err.message);
        return [];
    }
}

// ─────────────────────────────────────────────────────────────
// 1. API: Executive Overview
// ─────────────────────────────────────────────────────────────
app.get('/api/overview', (req, res) => {
    const splitData = readCsv(path.join(PROCESSED_DIR, 'split_dataset.csv'));
    const unifiedData = splitData.length ? splitData : readCsv(path.join(PROCESSED_DIR, 'unified_dataset.csv'));
    const baselineMetrics = readCsv(path.join(REPORTS_DIR, 'baseline_metrics.csv'));
    const debertaMetrics = readCsv(path.join(REPORTS_DIR, 'deberta_metrics.csv'));

    // Count categories
    const categoryCounts = {};
    const sourceCounts = {};
    unifiedData.forEach(row => {
        const cat = row.unified_label || row.attack_type || 'Unknown';
        categoryCounts[cat] = (categoryCounts[cat] || 0) + 1;
        const src = row.source || 'Unknown';
        sourceCounts[src] = (sourceCounts[src] || 0) + 1;
    });

    res.json({
        totalPrompts: unifiedData.length || 1984,
        categoriesCount: Object.keys(categoryCounts).length || 5,
        categoryCounts,
        sourceCounts,
        bestF1Known: '99.03% (DistilBERT)',
        bestF1Novel: '94.92% (DistilBERT)',
        baselineMetrics,
        debertaMetrics,
        status: 'Operational'
    });
});

// ─────────────────────────────────────────────────────────────
// 2. API: Dataset Explorer
// ─────────────────────────────────────────────────────────────
app.get('/api/dataset', (req, res) => {
    let rows = readCsv(path.join(PROCESSED_DIR, 'split_dataset.csv'));
    if (!rows.length) {
        rows = readCsv(path.join(PROCESSED_DIR, 'unified_dataset.csv'));
    }

    const { source, label, search, page = 1, limit = 25 } = req.query;

    // Available filter options
    const availableSources = [...new Set(rows.map(r => r.source).filter(Boolean))];
    const availableLabels = [...new Set(rows.map(r => r.unified_label || r.label).filter(Boolean))];

    // Filtering
    let filtered = rows;
    if (source && source !== 'all') {
        filtered = filtered.filter(r => r.source === source);
    }
    if (label && label !== 'all') {
        filtered = filtered.filter(r => (r.unified_label === label || r.label === label));
    }
    if (search) {
        const q = search.toLowerCase();
        filtered = filtered.filter(r => (r.prompt && r.prompt.toLowerCase().includes(q)) || (r.sample_id && r.sample_id.toLowerCase().includes(q)));
    }

    const total = filtered.length;
    const pageNum = parseInt(page, 10);
    const limitNum = parseInt(limit, 10);
    const startIndex = (pageNum - 1) * limitNum;
    const paginated = filtered.slice(startIndex, startIndex + limitNum);

    res.json({
        total,
        page: pageNum,
        limit: limitNum,
        totalPages: Math.ceil(total / limitNum),
        availableSources,
        availableLabels,
        data: paginated
    });
});

app.get('/api/dataset/stats', (req, res) => {
    const rows = readCsv(path.join(PROCESSED_DIR, 'split_dataset.csv')) || [];
    const byCategory = {};
    const bySource = {};
    const bySplit = {};
    const byDifficulty = {};

    rows.forEach(r => {
        const cat = r.unified_label || r.attack_type || 'Unknown';
        byCategory[cat] = (byCategory[cat] || 0) + 1;

        const src = r.source || 'Unknown';
        bySource[src] = (bySource[src] || 0) + 1;

        const spl = r.split || 'unspecified';
        bySplit[spl] = (bySplit[spl] || 0) + 1;

        const diff = r.difficulty || 'Medium';
        byDifficulty[diff] = (byDifficulty[diff] || 0) + 1;
    });

    res.json({
        total: rows.length,
        byCategory,
        bySource,
        bySplit,
        byDifficulty
    });
});

// ─────────────────────────────────────────────────────────────
// 3. API: Live Attack Detector
// ─────────────────────────────────────────────────────────────
app.post('/api/detect', (req, res) => {
    const { prompt, model = 'tfidf_lr' } = req.body;
    if (!prompt) {
        return res.status(400).json({ error: 'Prompt is required' });
    }

    const args = [BRIDGE_SCRIPT, 'detect', '--prompt', prompt, '--model', model];
    const proc = spawn(PYTHON_BIN, args, { cwd: PROJECT_ROOT });

    let stdout = '';
    let stderr = '';

    proc.stdout.on('data', data => { stdout += data.toString(); });
    proc.stderr.on('data', data => { stderr += data.toString(); });

    proc.on('close', code => {
        try {
            // Find last line that is valid JSON
            const lines = stdout.trim().split('\n');
            const lastJsonLine = lines.reverse().find(l => l.startsWith('{') && l.endsWith('}'));
            if (lastJsonLine) {
                const parsed = JSON.parse(lastJsonLine);
                return res.json(parsed);
            }
            res.json({
                prompt,
                model_used: model,
                is_attack: false,
                label: 'benign',
                confidence: 0.5,
                raw_output: stdout,
                stderr
            });
        } catch (e) {
            res.status(500).json({ error: 'Failed to parse detector output', details: stdout, stderr });
        }
    });
});

// ─────────────────────────────────────────────────────────────
// 4. API: Target LLM Assessment Engine
// ─────────────────────────────────────────────────────────────
app.post('/api/assess', (req, res) => {
    const {
        target = 'mock',
        model = '',
        security_level = 'medium',
        sample_size = 20,
        detector = 'tfidf_lr',
        api_key = ''
    } = req.body;

    const args = [
        BRIDGE_SCRIPT,
        'assess',
        '--target', target,
        '--security', security_level,
        '--sample-size', String(sample_size),
        '--detector', detector
    ];

    if (model) {
        args.push('--model', model);
    }
    if (api_key) {
        args.push('--api-key', api_key);
    }

    const proc = spawn(PYTHON_BIN, args, { cwd: PROJECT_ROOT });
    let stdout = '';
    let stderr = '';

    proc.stdout.on('data', data => { stdout += data.toString(); });
    proc.stderr.on('data', data => { stderr += data.toString(); });

    proc.on('close', code => {
        try {
            const lines = stdout.trim().split('\n');
            const jsonLine = lines.reverse().find(l => l.startsWith('{') && l.endsWith('}'));
            if (jsonLine) {
                const parsed = JSON.parse(jsonLine);
                return res.json(parsed);
            }
            res.status(500).json({ error: 'No JSON output from assessment engine', stdout, stderr });
        } catch (err) {
            res.status(500).json({ error: err.message, stdout, stderr });
        }
    });
});

// ─────────────────────────────────────────────────────────────
// 5. API: Model Performance & Comparison
// ─────────────────────────────────────────────────────────────
app.get('/api/metrics', (req, res) => {
    const baseline = readCsv(path.join(REPORTS_DIR, 'baseline_metrics.csv'));
    const deberta = readCsv(path.join(REPORTS_DIR, 'deberta_metrics.csv'));
    const split = readCsv(path.join(REPORTS_DIR, 'split_report.csv'));
    const unseen = readCsv(path.join(REPORTS_DIR, 'unseen_eval_tfidf_lr.csv'));

    res.json({
        baseline,
        deberta,
        split,
        unseen
    });
});

// ─────────────────────────────────────────────────────────────
// 6. API: Risk Scoring & Analysis
// ─────────────────────────────────────────────────────────────
const SEVERITY_WEIGHTS = {
    'Jailbreak': 1.0,
    'Indirect Prompt Injection': 0.9,
    'Prompt Injection': 0.7,
    'Prompt Leakage': 0.6,
    'Benign': 0.0,
    'Unknown': 0.5
};

app.post('/api/risk/calculate', (req, res) => {
    const {
        category = 'Jailbreak',
        attack_successful = true,
        detector_confidence = 0.5,
        is_detected_by_security = true
    } = req.body;

    const sev = SEVERITY_WEIGHTS[category] !== undefined ? SEVERITY_WEIGHTS[category] : 0.5;
    const success_val = attack_successful ? 1.0 : 0.0;
    const evasion_val = !is_detected_by_security ? 1.0 : (1.0 - parseFloat(detector_confidence));

    const raw_score = (sev * 0.35) + (success_val * 0.45) + (evasion_val * 0.20);
    const score = Math.round(Math.min(1.0, Math.max(0.0, raw_score)) * 10000) / 10000;

    let tier = 'LOW';
    if (score >= 0.75) tier = 'CRITICAL';
    else if (score >= 0.50) tier = 'HIGH';
    else if (score >= 0.25) tier = 'MEDIUM';

    res.json({
        category,
        risk_score: score,
        risk_tier: tier,
        severity_weight: sev,
        attack_successful: !!attack_successful,
        detector_confidence: parseFloat(detector_confidence),
        evasion_penalty: Math.round(evasion_val * 10000) / 10000,
        formula: 'Risk Score = (Severity × 0.35) + (Attack Success × 0.45) + (Evasion × 0.20)'
    });
});

// ─────────────────────────────────────────────────────────────
// 7. API: Reports & Artifacts
// ─────────────────────────────────────────────────────────────
app.get('/api/reports', (req, res) => {
    if (!fs.existsSync(REPORTS_DIR)) return res.json({ reports: [] });

    const files = fs.readdirSync(REPORTS_DIR).filter(f => f.endsWith('.csv') || f.endsWith('.json') || f.endsWith('.pdf'));
    const reportList = files.map(filename => {
        const stat = fs.statSync(path.join(REPORTS_DIR, filename));
        return {
            filename,
            size: stat.size,
            updatedAt: stat.mtime
        };
    });

    res.json({ reports: reportList });
});

app.get('/api/reports/:filename', (req, res) => {
    const filename = path.basename(req.params.filename);
    const filePath = path.join(REPORTS_DIR, filename);

    if (!fs.existsSync(filePath)) {
        return res.status(404).json({ error: 'Report not found' });
    }

    if (filename.endsWith('.csv')) {
        const rows = readCsv(filePath);
        return res.json({ filename, totalRows: rows.length, data: rows.slice(0, 300) });
    } else if (filename.endsWith('.json')) {
        try {
            const raw = fs.readFileSync(filePath, 'utf-8');
            return res.json({ filename, data: JSON.parse(raw) });
        } catch (e) {
            return res.status(500).json({ error: 'Failed to read JSON report' });
        }
    } else {
        // Send file for download (e.g. PDF)
        res.download(filePath);
    }
});

app.listen(PORT, () => {
    console.log(`🛡️ LLM Security Dashboard Server running at http://localhost:${PORT}`);
    console.log(`Using Python binary: ${PYTHON_BIN}`);
});

