
# sleeper-fantasy-simulation
Simulation tools for the Sleeper fantasy football platform

![Screen Shot 2020-10-27 at 9 17 47 AM](https://user-images.githubusercontent.com/19737289/123337359-14819c00-d515-11eb-859c-72d85cf5feb6.jpg)

## Background
One of the great honors of my life is to commission a somewhat serious fantasy football league of 12 members. For the uninitiated, fantasy football is a game wherein managers (the participants in the league) "draft" real-life football players onto their respective rosters and craft starting lineups on a weekly basis in hopes of scoring more points (based on real-life events like touchdowns scored or passes caught) than their opponents. There is a considerable amount of analysis that goes into these decisions, but in week 7, entering the home stretch of the regular season, another important question on everyone's mind is, "given the state of the league right now and the remaining matchups, what's the likelihood that I will make the playoffs?" The goal of this project is to answer that question and present the results elegantly.

## Approach

"Making the playoffs" can be defined as ranking in the top half of the 12 teams after the conclusion of week 13. Furthermore, teams are ranked based on the number of head-to-head wins they accumulate, and ties are broken by the total points scored in all games.

So, the problem reduces to: 
  1. Find the current state of each team (wins, points scored, game history)
  2. Find the list of remaining matchups
  3. Forecast the results of the reamining matchups
  4. Tabulate the results and determine the probability that each team ranks in the top 6
  5. Visualize the results

Steps 1 and 2 are accomplished easily by connecting to the Sleeper (our fantasy football platform) API. 

For the more difficult problem of steps 3 and 4, I settled on the following approach:

  1. For each team in the league, take the points scored in their last k=5 games as events
  2. Construct a normal distribution using these games
  3. For n=1000 runs 
    1. For each week remaining in the season, take a random sample from every team's distribution and award a win to the higher score in each matchup, and an additional win to the top 6 scoring teams**
    2. At the conclusion of the simulated season, tabulate the rankings and record each team's finishing rank
  4. After all runs are complete, take the percentage of runs for which each team finished in each rank as their probability of finishing in that rank
  5. Sum each team's probability of making ranks 1 thru 6 - this is their probability of making the playoffs

**Note: My league uses an "Extra Game vs. League Median" format - every week, in addition to the wins and losses awarded as a result of the head-to-head matchups, an additional win is awarded to each team that scored above the league's median score for that week (and an additional loss to the teams who did not). Because this is a realatively uncommon format, my script takes in a parameter to enable/disable this.

## Reasoning

The approach equates to a Monte Carlo style distribution sampling algorithm where the distributions are constructed using time-series data. 3 key decisions went into choosing the model and its parameters:

#### Why simulation?

I settled on this approach after considering a few others - namely, some sort of time series model like ARIMA or some optimization model like network flow. The problem with the former is that projecting future results based on a team's past results sounds good, but ignores one of the main factors in a team's performance: the matchup structure of the league. Additionally, you may end up with probabilites that are practically infeasible. The problem with the latter is the factorial complexity in constructing a flow network across 12 teams in 8 or so gameweeks. Such a network would be impractical to solve and would require approximation heuristics.

Simulation provides an opportunity to follow the structure of the league in an intuitive way - it is easy to imagine an algorithm going through each game week and simulating each team's score. It is also easy to interpret the results and diagnose potential issues.

#### Why sample from a normal distribution?

Analysis from previous seasons' gamescore data showed that a team's gamescores follow an approximately normal distribution. It is also intuitive and straightforward to implement using the random library.

#### Why 5 games?

The choice of 5 games is based on an understanding of the way a fantasy football team is likely to change throughout the season. It balances the desire to include more data - in order to construct a more representative distribution with less impactful random effects - with the desire to include less data - in order to capture changes a team may have made (e.g., adding a valuable player or losing one to injury). Lower values were tested, but these made the model too succeptible to single high scoring or low scoring games.

## Usage





https://user-images.githubusercontent.com/19737289/123337528-57dc0a80-d515-11eb-9e86-5ed8181ab2e4.mp4


