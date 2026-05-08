"""Generate the four-panel analysis figure for the Queue Paradox."""
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, ".")
from model import analyze, save_results

# Editorial palette (light)
NAVY = "#001F3F"
MUTED = "#6B7A8D"
LABEL = "#8FA3B1"
RULE = "#D6DBE0"
BG = "#FFFFFF"

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "axes.unicode_minus": False,
    "axes.edgecolor": RULE,
    "axes.labelcolor": MUTED,
    "axes.titlecolor": NAVY,
    "xtick.color": MUTED,
    "ytick.color": MUTED,
    "text.color": NAVY,
})


def style(ax):
    """Apply the editorial light style to an axis."""
    ax.set_facecolor(BG)
    ax.tick_params(colors=MUTED, labelsize=9)
    for spine in ax.spines.values():
        spine.set_color(RULE)
        spine.set_linewidth(0.6)
    ax.grid(False)


def main():
    os.makedirs("docs/viz", exist_ok=True)
    save_results()
    results = analyze()
    by_name = {r.strategy: r for r in results}

    fig, axes = plt.subplots(2, 2, figsize=(13, 8),
                             constrained_layout=True)
    fig.patch.set_facecolor(BG)

    strat_color = {
        "shortest": NAVY,
        "random": MUTED,
        "serpentine": LABEL,
    }
    strat_label = {
        "shortest": "pick shortest",
        "random": "pick random",
        "serpentine": "serpentine (single queue)",
    }

    # ---- Panel 1: distribution of queue waits ------------------------------
    ax = axes[0, 0]
    style(ax)
    bins = np.linspace(0, 6, 41)
    for name in ("shortest", "random", "serpentine"):
        w = np.array(by_name[name].waits)
        ax.hist(w, bins=bins, histtype="step", linewidth=1.8,
                color=strat_color[name], label=strat_label[name],
                density=True)
    ax.set_xlabel("queue wait (min)", fontsize=10, color=MUTED)
    ax.set_ylabel("density", fontsize=10, color=MUTED)
    ax.set_title("Distribution of queue waits",
                 fontsize=12, color=NAVY, fontweight="bold", pad=10)
    ax.set_yscale("log")
    ax.set_ylim(bottom=1e-4)
    ax.legend(frameon=False, fontsize=9, loc="upper right")

    # ---- Panel 2: mean vs SD bar chart -------------------------------------
    ax = axes[0, 1]
    style(ax)
    names = ["shortest", "random", "serpentine"]
    means = [by_name[n].mean_wait for n in names]
    stds = [by_name[n].std_wait for n in names]
    x = np.arange(len(names))
    ax.bar(x - 0.18, means, width=0.36, color=NAVY,
           label="E[Wq]")
    ax.bar(x + 0.18, stds, width=0.36, color=MUTED,
           label="SD[Wq]")
    ax.set_xticks(x)
    ax.set_xticklabels(["shortest", "random", "serpentine"], fontsize=9)
    ax.set_ylabel("minutes", fontsize=10, color=MUTED)
    ax.set_title("Mean vs. standard deviation",
                 fontsize=12, color=NAVY, fontweight="bold", pad=10)
    ax.legend(frameon=False, fontsize=9, loc="upper left")

    # ---- Panel 3: CDF of queue waits --------------------------------------
    ax = axes[1, 0]
    style(ax)
    for name in ("shortest", "random", "serpentine"):
        w = np.sort(np.array(by_name[name].waits))
        cdf = np.arange(1, len(w) + 1) / len(w)
        ax.plot(w, cdf, linewidth=1.8,
                color=strat_color[name], label=strat_label[name])
    ax.set_xlabel("queue wait (min)", fontsize=10, color=MUTED)
    ax.set_ylabel("cumulative fraction", fontsize=10, color=MUTED)
    ax.set_title("CDF of queue waits",
                 fontsize=12, color=NAVY, fontweight="bold", pad=10)
    ax.legend(frameon=False, fontsize=9, loc="lower right")

    # ---- Panel 4: tail percentiles ----------------------------------------
    ax = axes[1, 1]
    style(ax)
    pcts = ["p50", "p95", "p99"]
    xp = np.arange(len(pcts))
    width = 0.25
    for i, name in enumerate(("shortest", "random", "serpentine")):
        vals = [by_name[name].p50_wait, by_name[name].p95_wait,
                by_name[name].p99_wait]
        ax.bar(xp + (i - 1) * width, vals, width=width,
               color=[NAVY, MUTED, LABEL][i], label=strat_label[name])
    ax.set_xticks(xp)
    ax.set_xticklabels(pcts, fontsize=10)
    ax.set_ylabel("minutes", fontsize=10, color=MUTED)
    ax.set_title("Tail percentiles",
                 fontsize=12, color=NAVY, fontweight="bold", pad=10)
    ax.legend(frameon=False, fontsize=8, loc="upper left")

    plt.savefig("docs/viz/analysis-light.png", dpi=150,
                bbox_inches="tight", facecolor=BG)
    plt.close()
    print("Saved: docs/viz/analysis-light.png")


if __name__ == "__main__":
    main()
