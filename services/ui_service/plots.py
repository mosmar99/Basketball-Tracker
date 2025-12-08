import numpy as np
import matplotlib.pyplot as plt

def possession_plot(ball_tp, t1_color="#9cb2a0", t2_color="#9eaec6"):
    x, y = possession_to_percentages(ball_tp)
    y_percent = np.array(y) * 100

    fig, ax_left = plt.subplots(figsize=(14, 4))
    ax_right = ax_left.twinx()

    for i, val in enumerate(y_percent):
        ax_left.bar(i, val, color=t1_color, width=1.0)
        ax_left.bar(i, 100 - val, bottom=val, color=t2_color, width=1.0)

    ax_left.plot(x, y_percent, color="black", linewidth=3)

    ax_left.set_ylim(0, 100)
    ax_left.set_yticks(np.arange(0, 101, 5))
    ax_left.set_ylabel("Team A Possession (%)")

    ax_right.set_ylim(100, 0)
    ax_right.set_yticks(np.arange(0, 101, 5))
    ax_right.set_ylabel("Team B Possession (%)")

    ax_left.set_xlim(0, len(x))
    ax_left.set_xlabel("Frames")

    plt.tight_layout()

    return fig

def pi_plots(pi_stats, t1_color="#9cb2a0", t2_color="#9eaec6"):
    p1, p2, i1, i2 = extract_timeseries(pi_stats)
    frames = list(range(len(pi_stats)))
    plot_pass = passes_plot(frames, p1, p2, t1_color, t2_color)
    plot_intr = interceptions_plot(frames, i1, i2, t1_color, t2_color)
    return plot_pass, plot_intr
    
def to_percent(v1, v2):
    v1 = np.array(v1, dtype=float)
    v2 = np.array(v2, dtype=float)

    pct = np.zeros_like(v1, dtype=float)

    for i in range(len(v1)):
        a, b = v1[i], v2[i]
        if a == 0 and b == 0:
            pct[i] = 0.5
        elif a > 0 and b == 0:
            pct[i] = 1.0
        elif a == 0 and b > 0:
            pct[i] = 0.0
        else:  # both >0
            pct[i] = a / (a + b)

    return pct

def extract_timeseries(stats):
    passes_t1 = []
    passes_t2 = []
    inter_t1 = []
    inter_t2 = []

    for frame in stats:
        t1 = frame.get(1) or frame.get("1")
        t2 = frame.get(2) or frame.get("2")

        if t1 is None or t2 is None:
            raise ValueError(f"Bad stats format: {frame}")

        passes_t1.append(t1["Passes"])
        passes_t2.append(t2["Passes"])
        inter_t1.append(t1["Interceptions"])
        inter_t2.append(t2["Interceptions"])

    return passes_t1, passes_t2, inter_t1, inter_t2

def passes_plot(frames, passes_t1, passes_t2, t1_color="#9cb2a0", t2_color="#9eaec6"):
    pct = to_percent(passes_t1, passes_t2)
    return percent_style_plot(
        frames, pct, label="Passes", t1_color=t1_color, t2_color=t2_color
    )

def interceptions_plot(frames, inter_t1, inter_t2, t1_color="#9cb2a0", t2_color="#9eaec6"):
    pct = to_percent(inter_t1, inter_t2)
    return percent_style_plot(
        frames, pct, "Interceptions", t1_color=t1_color, t2_color=t2_color
    )

def percent_style_plot(x, pct_team1, label, t1_color="#9cb2a0", t2_color="#9eaec6"):
    y_percent = pct_team1 * 100

    fig, ax_left = plt.subplots(figsize=(14, 4))
    ax_right = ax_left.twinx()

    for i, val in enumerate(y_percent):
        ax_left.bar(i, val, color=t2_color, width=1.0)            
        ax_left.bar(i, 100 - val, bottom=val, color=t1_color, width=1.0)

    ax_left.plot(x, y_percent, color="black", linewidth=3)

    ax_left.set_ylim(0, 100)
    ax_left.set_yticks(np.arange(0, 101, 5))
    ax_left.set_ylabel(f"Team A {label} (%)")

    ax_right.set_ylim(100, 0)
    ax_right.set_yticks(np.arange(0, 101, 5))
    ax_right.set_ylabel(f"Team B {label} (%)")

    ax_left.set_xlim(0, len(x))
    ax_left.set_xlabel("Frames")

    plt.tight_layout()

    return fig

def control_plot(control_stats, t1_color="#9cb2a0", t2_color="#9eaec6"):
    y_percent = []
    for frame in control_stats:
        a = float(frame.get("1", 0))
        b = float(frame.get("2", 0))

        total = a + b
        if total == 0:
            y_percent.append(50)
        else:
            y_percent.append((a / total) * 100)

    y_percent = np.array(y_percent)
    x = np.arange(len(y_percent))

    fig, ax_left = plt.subplots(figsize=(14, 4))
    ax_right = ax_left.twinx()

    for i, val in enumerate(y_percent):
        ax_left.bar(i, val, color=t1_color, width=1.0)
        ax_left.bar(i, 100 - val, color=t2_color, bottom=val, width=1.0)

    ax_left.plot(x, y_percent, color="black", linewidth=3)

    ax_left.set_ylim(0, 100)
    ax_left.set_yticks(np.arange(0, 101, 10))
    ax_left.set_ylabel("Team A Control (%)")

    ax_right.set_ylim(100, 0)
    ax_right.set_yticks(np.arange(0, 101, 10))
    ax_right.set_ylabel("Team B Control (%)")

    ax_left.set_xlim(0, len(x))
    ax_left.set_xlabel("Frames")

    plt.tight_layout()

    return fig

def possession_to_percentages(ball_tp):
    x = []
    y = []

    team1_count = 0
    team2_count = 0
    total_possession_frames = 0

    for i, team in enumerate(ball_tp):

        # If no possession, percentage stays the same
        if team == -1:
            # Use last known value or 50%
            if not y:
                y.append(0.5)
            else:
                y.append(y[-1])
        else:
            # Update counters
            if team == 1:
                team1_count += 1
            elif team == 2:
                team2_count += 1

            total_possession_frames = team1_count + team2_count
            team1_percentage = team1_count / total_possession_frames

            y.append(team1_percentage)

        x.append(i)

    return x, y