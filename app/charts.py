import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator

SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
OTHER = "#9a9993"
INK, INK2, GRID, SURFACE = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"

plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "axes.edgecolor": GRID, "axes.labelcolor": INK2, "axes.titlecolor": INK,
    "axes.titlesize": 13, "axes.titleweight": "bold", "axes.titlelocation": "left",
    "axes.labelsize": 10, "xtick.color": INK2, "ytick.color": INK2,
    "xtick.labelsize": 9, "ytick.labelsize": 9, "axes.grid": True, "grid.color": GRID,
    "grid.linewidth": 0.8, "axes.spines.top": False, "axes.spines.right": False,
    "legend.frameon": False, "legend.fontsize": 9, "font.family": "DejaVu Sans",
    "lines.linewidth": 2, "lines.markersize": 5,
})


def _finish(fig, path):
    fig.tight_layout()
    if path:
        fig.savefig(path, dpi=150)
    return fig


def _color(i):
    return SERIES[i] if i < len(SERIES) else OTHER


def _hbar(rows, label_col, value_col, title, xlabel, path, fmt="{:g}", color=SERIES[0]):
    labels = [str(r[label_col]) for r in rows]
    values = [float(r[value_col]) for r in rows]
    fig, ax = plt.subplots(figsize=(8, max(2.5, 0.38 * len(rows) + 1)))
    ax.barh(range(len(labels)), values, color=color, height=0.65)
    ax.set_yticks(range(len(labels)), labels)
    ax.invert_yaxis()                      # keep the SQL order: first row on top
    ax.grid(axis="y", visible=False)
    for y, v in enumerate(values):
        ax.text(v, y, " " + fmt.format(v), va="center", fontsize=8, color=INK2)
    ax.set_xlabel(xlabel)
    ax.set_title(title)
    ax.margins(x=0.12)
    return _finish(fig, path)


def _empty(title, path):
    fig, ax = plt.subplots(figsize=(8, 2))
    ax.axis("off")
    ax.text(0.5, 0.5, "No data for the selected filters", ha="center", va="center", color=INK2)
    ax.set_title(title)
    return _finish(fig, path)


def c01(rows, path=None):
    if not rows:
        return _empty("Driver against his teammates", path)
    labels = [f"{r['teammate']} ({r['from_season']}-{r['to_season']})" for r in rows]
    values = [float(r["pct_ahead"]) for r in rows]
    fig, ax = plt.subplots(figsize=(9, max(2.5, 0.38 * len(rows) + 1)))
    ax.barh(range(len(labels)), values, color=SERIES[0], height=0.65)
    ax.set_yticks(range(len(labels)), labels)
    ax.axvline(50, color=INK2, linewidth=1, linestyle=":")
    ax.invert_yaxis()
    ax.grid(axis="y", visible=False)
    for y, (v, r) in enumerate(zip(values, rows)):
        ax.text(v, y, f" {r['times_ahead']}/{r['sessions']}", va="center", fontsize=8, color=INK2)
    ax.set_xlim(0, 110)
    ax.set_xlabel("% of qualifying sessions ahead of the teammate (dotted line = 50 %)")
    ax.set_title("Qualifying head-to-head against each teammate")
    return _finish(fig, path)


def c02(rows, path=None):
    if not rows:
        return _empty("Career points", path)
    fig, ax = plt.subplots(figsize=(9, 4.8))
    for i, r in enumerate(rows):
        ax.plot(r["seasons"], [float(p) for p in r["points_so_far"]], color=_color(i),
                marker="o", markersize=3, label=r["driver"])
    ax.set_xlabel("Season")
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    ax.set_ylabel("Career points so far")
    ax.set_title("Career points, season after season")
    ax.legend(loc="upper left", fontsize=8)
    return _finish(fig, path)


def c03(rows, path=None):
    if not rows:
        return _empty("Grands Prix in the country", path)
    labels = [r["circuit"] for r in rows]
    values = [r["races"] for r in rows]
    fig, ax = plt.subplots(figsize=(11, max(2.5, 0.45 * len(rows) + 1)))
    ax.barh(range(len(labels)), values, color=SERIES[0], height=0.6)
    ax.set_yticks(range(len(labels)), labels)
    ax.invert_yaxis()
    ax.grid(axis="y", visible=False)
    for y, r in enumerate(rows):
        ax.text(r["races"], y, f" {r['races']} races ({r['first_race']}-{r['last_race']}) - most wins: {r['top_winner']}",
                va="center", fontsize=8, color=INK2)
    ax.set_xlim(0, max(values) * 3.6)
    ax.set_xlabel("Grands Prix held")
    ax.set_title("Grands Prix held at each circuit of the country")
    return _finish(fig, path)


def c04(rows, path=None):
    if not rows:
        return _empty("Points without a win", path)
    return _hbar(rows, "driver", "points", "Most career points without a race win", "Career points", path, "{:g}")


def c05(rows, path=None):
    if not rows:
        return _empty("First-time winners", path)
    labels = [f"{r['driver']} ({r['year']})" for r in rows]
    values = [float(r["age_at_first_win"]) for r in rows]
    fig, ax = plt.subplots(figsize=(8, max(2.5, 0.38 * len(rows) + 1)))
    ax.barh(range(len(labels)), values, color=SERIES[0], height=0.65)
    ax.set_yticks(range(len(labels)), labels)
    ax.invert_yaxis()
    ax.grid(axis="y", visible=False)
    for y, v in enumerate(values):
        ax.text(v, y, f" {v:.1f}", va="center", fontsize=8, color=INK2)
    ax.set_xlabel("Age at first Grand Prix win (years)")
    ax.set_title("Age of drivers at their first win")
    ax.margins(x=0.12)
    return _finish(fig, path)


def c06(rows, path=None):
    if not rows:
        return _empty("Comebacks", path)
    labels = [f"{r['driver']} - {r['race']} {r['year']}" for r in rows]
    values = [r["started"] for r in rows]
    fig, ax = plt.subplots(figsize=(9, max(2.5, 0.38 * len(rows) + 1)))
    ax.barh(range(len(labels)), values, color=SERIES[0], height=0.65)
    ax.set_yticks(range(len(labels)), labels)
    ax.invert_yaxis()
    ax.grid(axis="y", visible=False)
    for y, v in enumerate(values):
        ax.text(v, y, f" P{v}", va="center", fontsize=8, color=INK2)
    ax.set_xlabel("Starting position of the winner")
    ax.set_title("Race wins from furthest back on the grid")
    ax.margins(x=0.1)
    return _finish(fig, path)


def c07(rows, path=None):
    if not rows:
        return _empty("Winning streaks", path)
    labels = [f"{r['driver']} ({r['from_season']}" + (f"-{r['to_season']})" if r['to_season'] != r['from_season'] else ")")
              for r in rows]
    values = [r["consecutive_wins"] for r in rows]
    fig, ax = plt.subplots(figsize=(8, max(2.5, 0.38 * len(rows) + 1)))
    ax.barh(range(len(labels)), values, color=SERIES[0], height=0.65)
    ax.set_yticks(range(len(labels)), labels)
    ax.invert_yaxis()
    ax.grid(axis="y", visible=False)
    for y, v in enumerate(values):
        ax.text(v, y, f" {v}", va="center", fontsize=8, color=INK2)
    ax.set_xlabel("Consecutive race wins")
    ax.set_title("Longest winning streaks")
    ax.margins(x=0.1)
    return _finish(fig, path)


def c08(rows, path=None):
    if not rows:
        return _empty("Pit stops and result", path)
    stops = [str(r["n_stops"]) for r in rows]
    avg = [float(r["avg_finish"]) for r in rows]
    fig, ax = plt.subplots(figsize=(8, 4.2))
    ax.bar(stops, avg, color=SERIES[0], width=0.6)
    ax.grid(axis="x", visible=False)
    for x, r in enumerate(rows):
        ax.text(x, float(r["avg_finish"]), f"{r['pct_podium']} % podium\n{r['finishers']} finishers",
                ha="center", va="bottom", fontsize=8, color=INK2)
    ax.set_xlabel("Pit stops made in the race")
    ax.set_ylabel("Average finishing position (lower is better)")
    ax.set_title("Finishing position by number of pit stops")
    ax.margins(y=0.2)
    return _finish(fig, path)


def c09(rows, path=None):
    if not rows:
        return _empty("Championship margins", path)
    years = [r["year"] for r in rows]
    margins = [float(r["margin"]) for r in rows]
    fig, ax = plt.subplots(figsize=(10, 4.2))
    ax.bar(years, margins, color=SERIES[0], width=0.75)
    ax.grid(axis="x", visible=False)
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    ax.set_xlabel("Season")
    ax.set_ylabel("Points between champion and runner-up")
    ax.set_title("Championship winning margin")
    return _finish(fig, path)


def c10(rows, path=None):
    if not rows:
        return _empty("Team reliability", path)
    labels = [r["team"] for r in rows]
    mech = [float(r["pct_mechanical"]) for r in rows]
    acc = [float(r["pct_accident"]) for r in rows]
    ys = list(range(len(rows)))
    fig, ax = plt.subplots(figsize=(9, max(2.5, 0.42 * len(rows) + 1)))
    ax.barh([y - 0.2 for y in ys], mech, height=0.38, color=SERIES[0], label="Mechanical failure")
    ax.barh([y + 0.2 for y in ys], acc, height=0.38, color=SERIES[1], label="Accident")
    ax.set_yticks(ys)
    ax.set_yticklabels(labels)
    ax.invert_yaxis()
    ax.grid(axis="y", visible=False)
    ax.set_xlabel("% of starts ending in a retirement")
    ax.set_title("Retirements: mechanical failures versus accidents")
    ax.legend(loc="lower right")
    return _finish(fig, path)


def c11(rows, path=None):
    if not rows:
        return _empty("Age of the grid", path)
    years = [r["year"] for r in rows]
    fig, ax = plt.subplots(figsize=(9, 4.2))
    ax.plot(years, [float(r["oldest"]) for r in rows], color=SERIES[1], linewidth=1.2, linestyle="--", label="Oldest")
    ax.plot(years, [float(r["avg_age"]) for r in rows], color=SERIES[0], label="Average")
    ax.plot(years, [float(r["youngest"]) for r in rows], color=SERIES[2], linewidth=1.2, linestyle="--", label="Youngest")
    ax.set_xlabel("Season")
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    ax.set_ylabel("Age of the drivers (years)")
    ax.set_title("Age of the drivers on the grid")
    ax.legend(loc="upper right")
    return _finish(fig, path)


def c12(before, after, path=None):
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.6), sharex=True)
    for ax, rows, title, color in ((axes[0], before, "Stored results", OTHER),
                                   (axes[1], after, "What-if (rolled back)", SERIES[0])):
        labels = [f"{r['position']}. {r['driver']}" for r in rows]
        vals = [float(r["points"]) for r in rows]
        ax.barh(range(len(labels)), vals, color=color, height=0.6)
        ax.set_yticks(range(len(labels)), labels)
        ax.invert_yaxis()
        ax.grid(axis="y", visible=False)
        for y, v in enumerate(vals):
            ax.text(v, y, f" {v:g}", va="center", fontsize=8, color=INK2)
        ax.set_title(title, fontsize=11)
        ax.set_xlabel("Season points (races + sprints)")
        ax.margins(x=0.18)
    return _finish(fig, path)


CHARTS = {"Q01": c01, "Q02": c02, "Q03": c03, "Q04": c04, "Q05": c05, "Q06": c06,
          "Q07": c07, "Q08": c08, "Q09": c09, "Q10": c10, "Q11": c11, "Q12": c12}