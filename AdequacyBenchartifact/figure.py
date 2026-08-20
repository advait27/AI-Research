import json, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

r = json.load(open("results/results.json"))
deg = r["degradation"]
ps = sorted(deg.keys(), key=float)
x = [float(p) for p in ps]
CONDS = ["BARE", "OTEL", "GUARD", "TYPED"]
# validated categorical slots, in fixed order; secondary encoding for grayscale/CVD
STYLE = {"BARE":  ("#2a78d6", ":",  "o"),
         "OTEL":  ("#eb6834", "--", "s"),
         "GUARD": ("#1baf7a", "-.", "^"),
         "TYPED": ("#4a3aa7", "-",  "D")}

plt.rcParams.update({"font.family": "serif", "font.serif": ["Times New Roman", "DejaVu Serif"],
                     "font.size": 7.5, "axes.linewidth": 0.6,
                     "figure.facecolor": "#fcfcfb", "axes.facecolor": "#fcfcfb"})
fig, axes = plt.subplots(2, 1, figsize=(3.25, 3.7), sharex=True, dpi=300)

for ax, key, ttl in ((axes[0], "coverage", "(a) Coverage"),
                     (axes[1], "soundness", "(b) Soundness")):
    for c in CONDS:
        col, ls, mk = STYLE[c]
        y = [deg[p][c][key] for p in ps]
        ax.plot(x, y, color=col, linestyle=ls, marker=mk, linewidth=1.5,
                markersize=3.6, markeredgewidth=0, label=c, clip_on=False, zorder=3)
    ax.set_ylim(0, 1.05)
    ax.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
    ax.grid(axis="y", color="#c3c2b7", linewidth=0.4, alpha=0.7, zorder=0)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color("#c3c2b7")
    ax.tick_params(length=2, width=0.5, colors="#52514e")
    ax.set_title(ttl, fontsize=8, loc="left", color="#0b0b0b", pad=4)
    ax.set_ylabel("proportion", fontsize=7.5, color="#52514e")

# selective direct labels at the right end, not a number on every point
NUDGE = {("coverage", "BARE"): -1, ("coverage", "GUARD"): 1,
         ("soundness", "BARE"): -4.5, ("soundness", "OTEL"): 3.5,
         ("soundness", "GUARD"): 0, ("soundness", "TYPED"): 0,
         ("coverage", "TYPED"): 0}
for ax, key in ((axes[0], "coverage"), (axes[1], "soundness")):
    for c in CONDS:
        if c == "OTEL" and key == "coverage":
            continue                      # coincides with BARE; noted in the caption
        if key == "soundness" and c in ("BARE", "OTEL"):
            continue                      # labelled jointly below
        col, _, _ = STYLE[c]
        yv = deg[ps[-1]][c][key]
        ax.annotate(c, (x[-1], yv), xytext=(3, NUDGE.get((key, c), 0)),
                    textcoords="offset points", fontsize=6.2, color="#52514e",
                    va="center", annotation_clip=False)

_b = deg[ps[-1]]["BARE"]["soundness"]; _o = deg[ps[-1]]["OTEL"]["soundness"]
axes[1].annotate("BARE, OTEL", (x[-1], (_b + _o) / 2), xytext=(3, 0),
                 textcoords="offset points", fontsize=6.2, color="#52514e",
                 va="center", annotation_clip=False)
axes[1].set_xlabel("fraction of spans lost", fontsize=7.5, color="#52514e")
axes[1].set_xticks(x)
axes[1].set_xticklabels(["0", ".05", ".10", ".20", ".40"], fontsize=6.5)
axes[0].legend(frameon=False, fontsize=6.5, ncol=4, loc="lower left",
               bbox_to_anchor=(0, 1.12), handlelength=2.4, columnspacing=1.1,
               labelcolor="#52514e")
fig.subplots_adjust(left=0.16, right=0.735, top=0.885, bottom=0.115, hspace=0.30)
fig.savefig("fig1.png", dpi=300, facecolor="#fcfcfb")
print("saved", [deg[ps[-1]][c]["coverage"] for c in CONDS])
