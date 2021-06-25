import pandas as pd
import random
import copy
import urllib.request
import json
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib
import numpy as np

matplotlib.use('TKAgg')

league_id = "597593297883566080"

#get owners, flatten metadata, and extract user_id, roster_id, and team_name
with urllib.request.urlopen("https://api.sleeper.app/v1/league/" + league_id + "/users") as url:
    owners = json.loads(url.read().decode())
for owner in range(len(owners)):
	for datapoint in owners[owner]["metadata"]:
		owners[owner][datapoint] = owners[owner]["metadata"][datapoint]
	del owners[owner]["metadata"]

owners_df = pd.DataFrame(owners)[["user_id", "display_name", "team_name"]]
print(owners_df)

#get rosters, flatten settings, and extract owner_id, roster_id, and wins
with urllib.request.urlopen("https://api.sleeper.app/v1/league/" + league_id + "/rosters") as url:
    rosters = json.loads(url.read().decode())
for roster in range(len(rosters)):
	for datapoint in rosters[roster]["settings"]:
		if datapoint == 'wins':
			rosters[roster][datapoint] = rosters[roster]["settings"][datapoint]
	del rosters[roster]["settings"]
rosters_df = pd.DataFrame(rosters)[["owner_id", "roster_id", "wins"]]


#merge owners and rosters
owners_df = pd.merge(owners_df, rosters_df, left_on="user_id", right_on="owner_id")[['user_id', 'display_name', 'roster_id', 'team_name']]

#get matchups and extract roster_id, matchup_id, points, and week, and also find upcoming gameweek
upcoming_gameweek = 1
matchups_df = pd.DataFrame()
for week in range(1, 14):
	with urllib.request.urlopen(("https://api.sleeper.app/v1/league/" + league_id + "/matchups/" + str(week))) as url:
		matchups = json.loads(url.read().decode())
	temporary_df = pd.DataFrame(matchups)[['roster_id', 'matchup_id', 'points']]
	temporary_df['week'] = week
	matchups_df = matchups_df.append(temporary_df)
	if temporary_df['points'].sum() != 0:
		upcoming_gameweek = week + 1


#get team averages and std deviations, then merge with owners to get user_id
team_stats_df = matchups_df[matchups_df['points'] != 0][['roster_id', 'points']].groupby('roster_id').agg(['mean', 'std']).reset_index()
team_stats_df.columns = ['roster_id', 'mean_points', 'std_points']
team_stats_df = pd.merge(team_stats_df, owners_df, on='roster_id')[['user_id', 'mean_points', 'std_points']]


#merge owners with matchups to get user_ids instead of roster_ids for both teams
matchups_df = pd.merge(matchups_df, owners_df, on='roster_id')[['user_id', 'display_name', 'matchup_id', 'points', 'week']]
matchups_df = pd.merge(matchups_df, matchups_df, on=('week', 'matchup_id'))
matchups_df = matchups_df[matchups_df['user_id_x'] != matchups_df['user_id_y']].drop_duplicates(['week', 'matchup_id'])

#select remaining matchups
remaining_matchups_df = matchups_df[matchups_df['week'] >= upcoming_gameweek]


"""
simulate an individual matchup
return each team's points in dict
"""
def matchup_simulator(team_stats_df, matchup):
	team_x = matchup['user_id_x']
	team_y = matchup['user_id_y']

	#get team_x points
	team_x_mean = team_stats_df[team_stats_df['user_id'] == team_x]['mean_points'].values
	team_x_std = team_stats_df[team_stats_df['user_id'] == team_x]['std_points'].values
	team_x_points = random.normalvariate(team_x_mean, team_x_std)

	#get team_y points
	team_y_mean = team_stats_df[team_stats_df['user_id'] == team_y]['mean_points'].values
	team_y_std = team_stats_df[team_stats_df['user_id'] == team_y]['std_points'].values
	team_y_points = random.normalvariate(team_y_mean, team_y_std)

	return {team_x: team_x_points, team_y: team_y_points}	


#construct team_dict
team_dict = {}
for index, team in owners_df.iterrows():
	team_dict[team['user_id']] = 0

"""
run n trials of rest-of-season simulation
return seed_pivot and team_dict  
"""
def trial_runner(n, team_dict):

	#get current team wins
	original_team_wins_dict = {}
	for index, team in rosters_df.iterrows():
		original_team_wins_dict[team['owner_id']] = team['wins']

	#create df for overall seeding - each team mapped to each possible seed
	total_seed_df = pd.DataFrame(team_dict.items(), columns=['user_id', 'occurences'])
	total_seed_df['key'] = 0
	possible_seeds_df = pd.DataFrame({'seed': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]})
	possible_seeds_df['key'] = 0
	total_seed_df = pd.merge(total_seed_df, possible_seeds_df, on='key')[['user_id', 'seed', 'occurences']]


	#run n trials
	for i in range(n):
		seeding_dict = {}
		team_wins_dict = original_team_wins_dict.copy()

		#run through each week remaining in season
		for week in list(remaining_matchups_df['week'].unique()):
			points_dict = {}

			#run matchup_simulator on all remaining matchups in a week
			for index, matchup in remaining_matchups_df[remaining_matchups_df['week'] == week].iterrows():
				matchup_points_dict = matchup_simulator(team_stats_df, matchup)
				points_dict.update(matchup_points_dict)

				#award head-to-head win to winning team
				if points_dict[matchup['user_id_x']] >= points_dict[matchup['user_id_y']]:
					team_wins_dict[matchup['user_id_x']] += 1
				else:
					team_wins_dict[matchup['user_id_y']] += 1

			#create matchup_points_df to determine top 6 scoring teams each week and award additional win vs league median
			points_df = pd.DataFrame.from_dict(points_dict, orient="index", columns=['points'])
			top_6_teams_df = points_df.sort_values('points', ascending=False)[:6]
			for team in team_wins_dict:
				if team in list(top_6_teams_df.index.values):
					team_wins_dict[team] += 1

		#determine playoffs
		team_wins_df = pd.DataFrame.from_dict(team_wins_dict, orient="index", columns=['wins'])
		playoff_teams_df = team_wins_df.sort_values('wins', ascending=False)[:6]
		for index, team in playoff_teams_df.iterrows():
			team_dict[index] += 1

		#determine seeding probabilities
		trial_team_wins_df = pd.DataFrame.from_dict(team_wins_dict, orient="index", columns=['wins'])
		trial_team_wins_df['seed'] = team_wins_df['wins'].rank(method='first', ascending=False)
		for trial_user_id, trial_row in trial_team_wins_df.iterrows():
			for index, total_row in total_seed_df.iterrows():
				if trial_user_id == total_row['user_id']:
					if int(trial_row['seed']) == int(total_row['seed']):
						total_seed_df.loc[index, 'occurences'] += 1

	#get team name from owners_df, pivot, and add Playoff Probability column (sum of top 6 seeds)
	total_seed_df = pd.merge(total_seed_df, owners_df, on='user_id')[['team_name', 'seed', 'occurences']]
	print("total_seed_df:\n")
	print(total_seed_df)


	seed_pivot = pd.pivot_table(total_seed_df, values='occurences', index='team_name', columns='seed', aggfunc=lambda x:12*x.sum()/total_seed_df['occurences'].sum())
	seed_pivot['Playoff Probability'] = seed_pivot[[1,2,3,4,5,6]].sum(axis=1)
	seed_pivot = seed_pivot.sort_values(['Playoff Probability', 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12], ascending=False)
	return (seed_pivot, team_dict)

n = 1000
seed_pivot, team_dict = trial_runner(n, team_dict)

#create df to exclude last column from heatmap coloring
heatmap_colors = seed_pivot.iloc[:,:12]
heatmap_colors['Playoffs'] = 0

#create and show heatmap
ax = sns.heatmap(heatmap_colors, annot=seed_pivot, alpha=1, cmap='Greens', linewidths=1, cbar=False)
ax.set_xticklabels(ax.get_xticklabels(), rotation=45, horizontalalignment='right')
ax.set_xlabel('Seed')
ax.set_ylabel('Team')
plt.title(('Seed Probability, n = ' + str(n) + ' Trials'))
plt.tight_layout()
plt.show()

#add results to log
team_df = pd.DataFrame(team_dict.items(), columns=['user_id', 'successes'])
team_df = pd.merge(team_df, owners_df)[['display_name', 'successes']].sort_values('successes', ascending=False)
team_df['week'] = upcoming_gameweek
team_df['success %'] = team_df['successes'] / n 
team_df.to_csv("WeeklySeedProbabilityLog.csv", mode='a', header=False)

	







