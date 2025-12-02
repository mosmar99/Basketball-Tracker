def convert_possession_to_team_series(ball_acquisition_list, team_assignments):
    """
    Converts raw possession (player_id or -1 per frame)
    into two binary lists: Team A possession, Team B possession.
    """
    teamA_series = []
    teamB_series = []

    for pid in ball_acquisition_list:
        if pid == -1:
            # No one has the ball
            teamA_series.append(0)
            teamB_series.append(0)
        else:
            # Which team does the player belong to?
            team = team_assignments.get(pid, None)
            if team == 0:
                teamA_series.append(1)
                teamB_series.append(0)
            elif team == 1:
                teamA_series.append(0)
                teamB_series.append(1)
            else:
                teamA_series.append(0)
                teamB_series.append(0)

    return teamA_series, teamB_series
