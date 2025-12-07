import matplotlib.pyplot as plt
import numpy as np

def possession_plot(ball_tp):
    x, y = possession_to_percentages(ball_tp)
    y_percent = np.array(y) * 100

    fig, ax_left = plt.subplots(figsize=(14, 4))
    ax_right = ax_left.twinx()

    for i, val in enumerate(y_percent):
        ax_left.bar(i, val, color="#9eaec6", width=1.0)
        ax_left.bar(i, 100 - val, bottom=val, color="#9cb2a0", width=1.0)

    ax_left.plot(x, y_percent, color="black", linewidth=2)

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

def control_plot(control_stats):
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
        ax_left.bar(i, val, color="#9cb2a0", width=1.0)
        ax_left.bar(i, 100 - val, color="#9eaec6", bottom=val, width=1.0)

    ax_left.plot(x, y_percent, color="black", linewidth=2)

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