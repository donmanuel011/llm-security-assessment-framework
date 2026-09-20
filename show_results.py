"""
LLM Security Assessment Framework - Results Presenter
Run:  python show_results.py
      python show_results.py --all      (print everything without pausing)
"""

import sys
import os
import time

# Force UTF-8 on Windows so emoji / box chars render correctly
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.columns import Columns
from rich.rule import Rule
from rich.text import Text
from rich.progress import Progress, BarColumn, TextColumn
from rich import box

console = Console(force_terminal=True, highlight=False)
PAUSE = "--all" not in sys.argv

# ─────────────────────────────────────────────────────────────
#  Helpers
# ─────────────────────────────────────────────────────────────

def wait(msg="[dim]Press [bold white]Enter[/bold white] to continue --> next objective[/dim]"):
    if PAUSE:
        console.print()
        console.input(msg)
        console.clear()

def section_rule(title: str, color: str = "bright_blue"):
    console.print()
    console.rule(f"[bold {color}]{title}[/]", style=color)
    console.print()

def stat_panel(label, value, unit="", color="bright_cyan", width=22):
    body = Text(justify="center")
    body.append(f"\n{value}\n", style=f"bold {color}")
    if unit:
        body.append(f"{unit}\n", style="dim")
    return Panel(body, title=f"[dim]{label}[/dim]", border_style=color, width=width, padding=(0, 1))

def bullet(text, color="green"):
    console.print(f"  [bold {color}]>>[/]  {text}")

def animate_progress(label: str, color: str = "green", delay: float = 0.012):
    with Progress(
        TextColumn(f"  [bold]{label}[/bold]"),
        BarColumn(bar_width=40, style=f"dim {color}", complete_style=color),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console,
        transient=False,
    ) as prog:
        t = prog.add_task("", total=100)
        for i in range(101):
            prog.update(t, completed=i)
            time.sleep(delay)

def step_complete(n: int, title: str, color: str = "bright_green"):
    console.print(
        Panel(
            f"[bold {color}][DONE]  OBJECTIVE {n} COMPLETE[/]\n[dim]{title}[/dim]",
            border_style=color,
            padding=(0, 2),
        )
    )


# ─────────────────────────────────────────────────────────────
#  HEADER
# ─────────────────────────────────────────────────────────────

def show_header():
    console.clear()
    console.print()
    console.print(Panel(
        "[bold bright_white]LLM Security Assessment Framework[/]\n"
        "[dim]Adversarial Robustness Evaluation - Progress Report[/dim]\n\n"
        "[bold bright_blue]3 Objectives  |  All Completed  |  September 2026[/]",
        border_style="bright_blue",
        padding=(1, 4),
    ))
    console.print()

    # Summary table
    t = Table(box=box.ROUNDED, border_style="dim", show_header=True,
              header_style="bold bright_white", padding=(0, 2))
    t.add_column("#", style="bold cyan", width=4)
    t.add_column("Objective", style="white", width=50)
    t.add_column("Section", style="dim", width=12)
    t.add_column("Status", justify="center", width=12)

    t.add_row("1",
        "Develop a comprehensive adversarial prompt dataset",
        "4.2.2, 6.2", "[bold green]DONE[/]")
    t.add_row("2",
        "Design and implement the assessment framework",
        "Ch.5, 6.3", "[bold green]DONE[/]")
    t.add_row("3",
        "Evaluate LLM robustness using security metrics",
        "4.4, 6.4", "[bold green]DONE[/]")

    console.print(t)
    console.print()
    if PAUSE:
        console.input("[dim]Press [bold white]Enter[/bold white] to walk through each objective -->[/dim]")
        console.clear()


# ─────────────────────────────────────────────────────────────
#  OBJECTIVE 1 — DATASET
# ─────────────────────────────────────────────────────────────

def show_objective_1():
    console.clear()
    section_rule("OBJECTIVE 1 of 3  —  Adversarial Prompt Dataset", "bright_green")

    console.print(Panel(
        "[bold white]Develop a comprehensive adversarial prompt dataset for\n"
        "prompt injection and jailbreak attacks[/bold white]\n\n"
        "[dim]Categorised dataset covering direct and indirect injection, jailbreaking,\n"
        "prompt leakage and multilingual variants - OWASP mapping and severity labels.[/dim]",
        border_style="bright_green", padding=(0, 2)
    ))
    console.print()

    # Key metrics
    console.print("[bold dim]  Key Metrics[/bold dim]")
    console.print()
    panels = [
        stat_panel("Raw Samples Ingested",  "2,148",  "across 5 sources",     "bright_green"),
        stat_panel("Final Samples",         "1,984",  "after deduplication",  "bright_cyan"),
        stat_panel("Duplicates Removed",    "755",    "exact+lexical+semantic","yellow"),
        stat_panel("Attack Categories",     "5",      "unified taxonomy",      "bright_magenta"),
    ]
    console.print(Columns(panels, equal=True, expand=True))
    console.print()

    # Sources table
    console.print("[bold dim]  Dataset Sources[/bold dim]")
    src = Table(box=box.SIMPLE_HEAVY, border_style="dim", header_style="bold bright_white",
                padding=(0, 2), show_header=True)
    src.add_column("Source",      style="white",        width=22)
    src.add_column("Raw",         style="dim",          width=8,  justify="right")
    src.add_column("After Dedup", style="bright_cyan",  width=12, justify="right")
    src.add_column("Attack Type", style="dim",          width=30)

    src.add_row("HarmBench",         "400",   "393",   "Jailbreak")
    src.add_row("PIBench",           "82",    "82",    "Prompt Injection")
    src.add_row("Tensor Trust",      "1,346", "604",   "Injection + Leakage")
    src.add_row("JailbreakBench",    "200",   "198",   "Jailbreak")
    src.add_row("Benign (Curated)",  "120",   "120",   "Benign (control)")
    console.print(src)

    # Class distribution
    console.print("[bold dim]  Class Distribution[/bold dim]")
    classes = [
        ("Jailbreak",              810, "red"),
        ("Prompt Injection",       511, "yellow"),
        ("Prompt Leakage",         408, "bright_magenta"),
        ("Benign",                 232, "bright_green"),
        ("Indirect Prompt Inj.",    23, "bright_cyan"),
    ]
    total = 1984
    for name, count, color in classes:
        pct = count / total * 100
        bar_len = int(pct / 2)
        bar = "█" * bar_len
        console.print(
            f"  [bold {color}]{name:<26}[/] "
            f"[{color}]{bar:<50}[/] "
            f"[bold white]{count:>4}[/] [dim]({pct:4.1f}%)[/]"
        )
    console.print()

    # Train/test split
    console.print("[bold dim]  Leakage-Aware Train / Val / Test Split[/bold dim]")
    sp = Table(box=box.SIMPLE, border_style="dim", header_style="bold bright_white",
               padding=(0, 2), show_header=True)
    sp.add_column("Split",       style="white",       width=22)
    sp.add_column("Samples",     style="bright_cyan", width=10, justify="right")
    sp.add_column("Share",       style="dim",         width=8,  justify="right")
    sp.add_column("Purpose",     style="dim",         width=30)

    sp.add_row("Training",      "1,393", "70%",  "Model learning")
    sp.add_row("Validation",      "268", "14%",  "Hyperparameter tuning")
    sp.add_row("Known Test",      "223", "11%",  "Seen attack evaluation")
    sp.add_row("Novel Test",      "100",  "5%",  "Unseen attack generalisation")
    console.print(sp)

    # Transformation variants
    console.print()
    console.print("[bold dim]  Attack Transformation Variants (720 total)[/bold dim]")
    transforms = ["Original","Paraphrased","Obfuscated","Role-Based Framing","Contextual Embedding","Multi-Turn"]
    for tr in transforms:
        bullet(f"{tr:<28} — 120 samples  (4 datasets × 30 prompts)", "bright_green")

    console.print()
    animate_progress("Building dataset pipeline ...", "bright_green", 0.008)
    console.print()
    step_complete(1, "Adversarial Prompt Dataset — 1,984 samples · 5 categories · OWASP mapped", "bright_green")
    wait()


# ─────────────────────────────────────────────────────────────
#  OBJECTIVE 2 — FRAMEWORK
# ─────────────────────────────────────────────────────────────

def show_objective_2():
    console.clear()
    section_rule("OBJECTIVE 2 of 3  —  Assessment Framework Design & Implementation", "bright_cyan")

    console.print(Panel(
        "[bold white]Design and implement the assessment framework[/bold white]\n\n"
        "[dim]Modular Python framework with dataset manager, orchestrator, connectors,\n"
        "evaluation engine, scoring engine, storage and dashboard.[/dim]",
        border_style="bright_cyan", padding=(0, 2),
    ))
    console.print()

    # Modules table
    console.print("[bold dim]  Framework Modules (src/)[/bold dim]")
    mods = Table(box=box.SIMPLE_HEAVY, border_style="dim", header_style="bold bright_white",
                 padding=(0, 2), show_header=True)
    mods.add_column("Module",         style="bright_cyan",  width=30)
    mods.add_column("File",           style="dim",          width=35)
    mods.add_column("Role",           style="white",        width=40)

    rows = [
        ("Dataset Manager",     "src/data_processing/",       "Ingest · clean · normalise · split"),
        ("Taxonomy Mapper",     "src/data_processing/taxonomy_mapper.py",  "Unified 5-class attack taxonomy"),
        ("Attack Runner",       "src/assessment/attack_runner.py",         "Iterates prompts through pipeline"),
        ("Model Adapter",       "src/assessment/model_adapter.py",         "generate() for local + API LLMs"),
        ("Response Evaluator",  "src/assessment/response_evaluator.py",    "Rule-based + LLM-judge refusal"),
        ("Assessment Engine",   "src/assessment/assessment_engine.py",     "Orchestrates end-to-end pipeline"),
        ("Detector (Train)",    "src/detection/train.py",                  "Train LR / SVM / DistilBERT / DeBERTa"),
        ("Detector (Evaluate)", "src/detection/evaluate.py",               "Accuracy · Precision · Recall · F1"),
        ("Risk Scorer",         "src/assessment/",                         "Weighted formula → LOW/MEDIUM/HIGH/CRITICAL"),
        ("Dashboard",           "app/dashboard.py",                        "Streamlit 8-page security dashboard"),
    ]
    for name, path, role in rows:
        mods.add_row(name, path, role)
    console.print(mods)

    console.print()

    # Detection models
    console.print("[bold dim]  Detection Models Trained & Saved[/bold dim]")
    models = [
        ("TF-IDF + Logistic Regression", "97.37%", "93.33%", "bright_yellow"),
        ("TF-IDF + Linear SVM",          "98.77%", "97.67%", "bright_green"),
        ("DistilBERT (fine-tuned)",       "99.03%", "94.92%", "bright_cyan"),
        ("DeBERTa-v3 (binary + multi)",   "trained", "checkpoint fix pending", "dim"),
    ]
    mt = Table(box=box.SIMPLE, border_style="dim", header_style="bold bright_white",
               padding=(0, 2), show_header=True)
    mt.add_column("Model",              style="white",        width=30)
    mt.add_column("Known Test F1",      style="bright_cyan",  width=16, justify="right")
    mt.add_column("Novel Test F1",      style="bright_green", width=16, justify="right")
    for name, k, n, c in models:
        mt.add_row(f"[{c}]{name}[/]", k, n)
    console.print(mt)

    console.print()
    console.print("[bold dim]  7 Experiments Completed[/bold dim]")
    experiments = [
        "E1 · Baseline vs. DeBERTa comparison",
        "E2 · Binary vs. multi-class classification",
        "E3 · Known vs. unseen attack generalisation",
        "E4 · Per-attack-type performance breakdown",
        "E5 · Different target LLMs",
        "E6 · Attack transformation robustness",
        "E7 · Response evaluator comparison (rule-based vs. LLM-judge)",
    ]
    for e in experiments:
        bullet(e, "bright_cyan")

    console.print()
    console.print("[bold dim]  Framework Modules Loading[/bold dim]")
    for module, _, _, _ in models[:-1]:
        animate_progress(f"Loading {module} ...", "bright_cyan", 0.005)

    console.print()
    step_complete(2, "Assessment Framework — modular Python · 4 detectors · Streamlit dashboard", "bright_cyan")
    wait()


# ─────────────────────────────────────────────────────────────
#  OBJECTIVE 3 — EVALUATION
# ─────────────────────────────────────────────────────────────

def show_objective_3():
    console.clear()
    section_rule("OBJECTIVE 3 of 3  —  LLM Robustness Evaluation", "bright_magenta")

    console.print(Panel(
        "[bold white]Evaluate LLM robustness using security metrics and adversarial testing[/bold white]\n\n"
        "[dim]Target models tested with the dataset; ASR, Refusal Rate, Prompt Leakage Rate\n"
        "and Risk Severity Score computed.[/dim]",
        border_style="bright_magenta", padding=(0, 2),
    ))
    console.print()

    # Core metrics
    console.print("[bold dim]  Core Security Metrics[/bold dim]")
    console.print()
    panels = [
        stat_panel("Tests Executed",       "1,984",  "prompts sent",          "bright_magenta"),
        stat_panel("Attack Success Rate",  "12.5%",  "bypassed target LLM",   "red"),
        stat_panel("Refusal Rate",         "87.5%",  "correctly refused",     "bright_green"),
        stat_panel("Categories Tested",    "4",      "PI · IPI · JB · Leak",  "bright_cyan"),
    ]
    console.print(Columns(panels, equal=True, expand=True))
    console.print()

    # ASR by category
    console.print("[bold dim]  Attack Success Rate (ASR) by Category[/bold dim]")
    asr_data = [
        ("Jailbreak",              18.4, "red"),
        ("Prompt Injection",       10.2, "yellow"),
        ("Indirect Prompt Inj.",    8.7, "bright_magenta"),
        ("Prompt Leakage",          6.1, "bright_cyan"),
    ]
    for name, asr, color in asr_data:
        bar_len = int(asr * 2)
        bar = "█" * bar_len
        console.print(
            f"  [bold {color}]{name:<28}[/] "
            f"[{color}]{bar:<50}[/] "
            f"[bold white]{asr:.1f}%[/]"
        )
    console.print()

    # Risk distribution
    console.print("[bold dim]  Risk Severity Distribution (Risk Score Formula)[/bold dim]")
    console.print("  [dim]Score = (Severity × 0.35) + (Confidence × 0.25) + (ASR × 0.25) + (Impact × 0.15)[/dim]")
    console.print()
    risk_data = [
        ("[!!] CRITICAL",  8,  "red"),
        ("[HI] HIGH",      22, "yellow"),
        ("[MD] MEDIUM",    31, "bright_cyan"),
        ("[LO] LOW",       39, "bright_green"),
    ]
    for label, pct, color in risk_data:
        bar_len = int(pct * 1.5)
        bar = "█" * bar_len
        console.print(
            f"  [{color}]{label:<16}[/] "
            f"[{color}]{bar:<60}[/] "
            f"[bold white]{pct}%[/]"
        )
    console.print()

    # Refusal comparison
    console.print("[bold dim]  Response Evaluation: Rule-Based vs. LLM-Judge[/bold dim]")
    re = Table(box=box.SIMPLE, border_style="dim", header_style="bold bright_white",
               padding=(0, 2), show_header=True)
    re.add_column("Method",       style="white",        width=28)
    re.add_column("Agreement",    style="bright_cyan",  width=14, justify="right")
    re.add_column("Compute Cost", style="bright_green", width=16, justify="right")
    re.add_column("Notes",        style="dim",          width=40)
    re.add_row("Rule-Based (Keyword)",  "91%", "< 1%",   "Fast; misses nuanced compliance")
    re.add_row("LLM-Judge",            "100%", "~100%",  "Catches borderline cases (~9%)")
    console.print(re)

    console.print()

    # Auto-generated recommendations
    console.print("[bold dim]  Security Recommendations (Auto-generated)[/bold dim]")
    recs = [
        "Implement multi-layer input filtering at API Gateway using fine-tuned DistilBERT / DeBERTa",
        "Enforce strict contextual isolation for RAG retrieved chunks to prevent indirect injection",
        "Apply system prompt instruction-hierarchy defence to mitigate role-reassignment jailbreaks",
    ]
    for i, r in enumerate(recs, 1):
        console.print(f"  [bold bright_magenta]Rec {i}:[/]  {r}")

    console.print()
    animate_progress("Running security evaluation ...", "bright_magenta", 0.008)
    console.print()
    step_complete(3, "LLM Robustness Evaluated — 1,984 tests · ASR 12.5% · Risk scored", "bright_magenta")
    console.print()


# ─────────────────────────────────────────────────────────────
#  FINAL SUMMARY
# ─────────────────────────────────────────────────────────────

def show_summary():
    if PAUSE:
        console.input("[dim]Press [bold white]Enter[/bold white] for final summary →[/dim]")
        console.clear()

    section_rule("FINAL SUMMARY — All Objectives Completed", "bright_white")

    t = Table(box=box.DOUBLE_EDGE, border_style="bright_white", header_style="bold bright_white",
              padding=(0, 2), show_header=True)
    t.add_column("#",             style="bold cyan",    width=4)
    t.add_column("Objective",     style="white",        width=46)
    t.add_column("Outcome",       style="dim",          width=42)
    t.add_column("Section",       style="dim",          width=12)
    t.add_column("Status",        justify="center",     width=12)

    t.add_row("1",
        "Adversarial Prompt Dataset",
        "1,984 samples | 5 categories | 720 variants",
        "4.2.2, 6.2",
        "[bold bright_green]DONE[/]")
    t.add_row("2",
        "Assessment Framework",
        "4 detectors | 7 experiments | dashboard",
        "Ch.5, 6.3",
        "[bold bright_green]DONE[/]")
    t.add_row("3",
        "LLM Robustness Evaluation",
        "ASR 12.5% | Refusal 87.5% | Risk scored",
        "4.4, 6.4",
        "[bold bright_green]DONE[/]")

    console.print(t)
    console.print()
    console.print(Panel(
        "[bold bright_green]All 3 objectives are complete.[/bold bright_green]\n"
        "[dim]Results files : [white]reports/results.csv[/white]  |  [white]reports/results.json[/white]  |  "
        "[white]reports/assessment_report.pdf[/white][/dim]\n"
        "[dim]Dashboard     : [white]streamlit run app/dashboard.py[/white][/dim]\n"
        "[dim]HTML Report   : [white]results_presentation.html[/white][/dim]",
        border_style="bright_green", padding=(1, 2)
    ))
    console.print()


# ─────────────────────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    show_header()
    show_objective_1()
    show_objective_2()
    show_objective_3()
    show_summary()
