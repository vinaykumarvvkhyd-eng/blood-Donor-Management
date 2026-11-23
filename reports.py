"""Markdown, plain-text audit and CSV reporting."""
from datetime import datetime
from pathlib import Path
from .services import summary, all_donors
from .storage import write_csv
from .config import REPORT_DIR, AUDIT_LOG

def export_all():
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    records = all_donors()
    stats = summary()
    csv_path = REPORT_DIR / f"bloodcare_report_{stamp}.csv"
    write_csv(records, csv_path)
    md_path = REPORT_DIR / f"bloodcare_summary_{stamp}.md"
    lines = ["# BloodCare — Executive Summary", "", f"Generated: {datetime.now().astimezone().isoformat(timespec='seconds')}", "",
             "## Key metrics", "", f"- Total registrations: {stats['total']}",
             f"- Average age: {stats['average_age']}", f"- Donated: {stats['donated']}",
             f"- Donation rate: {stats['donation_rate']}%", f"- Cities represented: {stats['cities']}",
             f"- Overdue registrations: {stats['overdue']}", "", "## Blood group distribution", "",
             "| Blood group | Registrations |", "|---|---:|"]
    lines += [f"| {g} | {n} |" for g, n in stats["blood_groups"].items()]
    lines += ["", "## Status distribution", "", "| Status | Count |", "|---|---:|"]
    lines += [f"| {g} | {n} |" for g, n in stats["statuses"].items()]
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    audit_path = REPORT_DIR / f"bloodcare_audit_{stamp}.txt"
    audit_path.write_text(AUDIT_LOG.read_text(encoding="utf-8") if AUDIT_LOG.exists() else "No audit events recorded.\n", encoding="utf-8")
    return [str(p) for p in (csv_path, md_path, audit_path)]

def create_matplotlib_chart():
    """Optional Matplotlib output. Returns None when Matplotlib is not installed."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        return None
    stats = summary()
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    path = REPORT_DIR / "blood_group_distribution.png"
    groups, counts = list(stats["blood_groups"].keys()), list(stats["blood_groups"].values())
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.bar(groups, counts)
    ax.set_title("Blood Group Registration Distribution")
    ax.set_xlabel("Blood group")
    ax.set_ylabel("Number of registrations")
    ax.grid(axis="y", alpha=.2)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)
    return str(path)
