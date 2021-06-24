# sleeper-fantasy-simulation
Simulation tools for the Sleeper fantasy football platform

One of the great honors of my life is to commission a somewhat serious fantasy football league of 12 members. For the uninitiated, fantasy football is a game wherein managers (the participants in the league) "draft" real-life football players onto their respective rosters and craft starting lineups on a weekly basis in hopes of scoring more points (based on real-life events like touchdowns scored or passes caught) than their opponents. There is a considerable amount of analysis that goes into these decisions, but in week 7, entering the home stretch of the regular season, another important question on everyone's mind is, "given the state of the league right now and the remaining matchups, what's the likelihood that I will make the playoffs?" The goal of this project is to answer that question and present the results elegantly.

"Making the playoffs" can be defined as ranking in the top half of the 12 teams after the conclusion of week 13. Furthermore, teams are ranked based on the number of head-to-head wins they accumulate, and ties are broken by the total points scored in all games.

So, the problem reduces to: 
  1. Find the current state of each team (wins, points scored, game history)
  2. Find the list of remaining matchups
  3. Forecast the results of the reamining matchups
  4. Tabulate the results and determine the probability that each team ranks in the top 6

Steps 1 and 2 are accomplished easily by connecting to the Sleeper (our fantasy football platform) API. 

For the more difficult problem of step 3, I settled on the following approach:

  1. For each team in the league, take the points scored in their last n=5 games as events
  2. Construct a normal distribution using these games
  3. For k=10000 runs 
    1. For each week remaining in the season, take a random sample from every team's distribution and award a win to the higher score in each matchup, and an additional win to the top 6 scoring teams**
    2. At the conclusion of the simulated season, tabulate the rankings and record each team's finishing rank
  4. After all runs are complete, take the percentage of runs for which each team finished in each rank as their probability of finishing in that rank
  5. Sum each team's probability of making ranks 1 thru 6 - this is their probability of making the playoffs



**Note: My league uses an "Extra Game vs. League Median" format - every week, in addition to the wins and losses awarded as a result of the head-to-head matchups, an additional win is awarded to each team that scored above the league's median score for that week (and an additional loss to the teams who did not). Because this is a realatively uncommon format, my script takes in a parameter to enable/disable this.
