# Tabular updates and an honest seed report

This optional bridge takes about 25 minutes. You can skip it and open any activity. Reading it creates no evidence. It uses tiny tables and short lists of numbers, not a simulator, and it makes no claim that any method works on a robot.

## One update, step by step

A tabular agent keeps a number Q(s, a) for every state and action: its current estimate of the discounted return after taking a in s. After one transition (s, a, r, s') it nudges that entry toward a target:

Q_new = Q + alpha (target - Q)

alpha in [0, 1] is the step size. With alpha = 1 the entry becomes the target; with alpha = 0 nothing changes. The target is the reward plus a discounted guess about the future:

- Q-learning (off-policy): target = r + gamma max_a' Q(s', a'). It assumes the best next action, whatever the robot will really do.
- SARSA (on-policy): target = r + gamma Q(s', a'), where a' is the action the behaviour policy actually chose in s'. If that was an exploratory pick, the target is lower than the Q-learning one.

When the behaviour happens to pick a greedy action, the two targets agree.

## Terminated is not truncated

Many logs carry one `done` flag, but two different things end an episode:

- Terminated: the task itself ended (goal reached, crash). There is no future, so the target is just r. Whatever the table holds for s' is never read.
- Truncated: a time limit or recording cut stopped the episode while the task would go on. The state s' still has a future, so the target bootstraps as usual.

Treating a truncation as a terminal teaches the agent that the last moves before a time limit lead to nothing, which biases the values near the limit. If a transition is both, it terminated.

## Exploration probabilities

An epsilon-greedy behaviour picks uniformly among all n actions with probability epsilon and a greedy action otherwise. Exactly tied maxima share the greedy probability equally. For k tied maxima: each of them has probability epsilon/n + (1 - epsilon)/k, every other action epsilon/n. The total is 1.

## Returns

For rewards r_0, ..., r_{T-1} the return from step t is G_t = r_t + gamma G_{t+1}, starting from G_T = 0 for a terminated episode. For a truncated one, start from an estimate of the value of the cut-off state instead; it is discounted by gamma^T in G_0.

## Many seeds, one honest table

A learning run depends on its random seed. One run is one draw. A protocol written before the experiment declares the seeds (for example 11 to 15) and reports every one of them, the same budget for each method. Never choose seeds, or drop runs, after seeing results.

For n final returns x_1, ..., x_n:

- mean = (sum of x) / n
- sample standard deviation s = sqrt( sum (x - mean)^2 / (n - 1) ). The n - 1 appears because the mean was estimated from the same numbers.
- standard error of the mean = s / sqrt(n)

Reporting only the best seed is the maximum of n draws; it overstates a typical outcome, more so when the spread is large. With n = 1 there is no s at all.

## Reward loopholes

A reward loophole is a way to collect reward without doing the task. On a tiny deterministic environment you can check it exactly: compute the best total reward among paths that reach the goal within the time limit, and the best total among paths of the full length that never reach it. If the second is strictly larger, an agent that maximises reward will not finish. It may depend on the time limit: a bonus of 2 per step beats a goal worth 9 only once the limit is long enough.

## Worked example

Table row of the next state: Q(s', .) = (1, 4, 2). Take r = 0.5, gamma = 0.5, alpha = 0.5, Q(s, a) = 2.

Q-learning: target = 0.5 + 0.5 * 4 = 2.5, Q_new = 2 + 0.5 * 0.5 = 2.25.
SARSA with a' = 0 (value 1): target = 0.5 + 0.5 = 1, Q_new = 2 + 0.5 * (-1) = 1.5.
Terminated transition: target = 0.5, Q_new = 2 + 0.5 * (-1.5) = 1.25.
Truncated only: same as the Q-learning case, 2.25.

Five seeds with returns 4, 6, 8, 10, 2: mean 6, squared deviations 4, 0, 4, 16, 16 sum to 40, s = sqrt(10) = 3.1623, standard error = sqrt(2) = 1.4142. The best seed (10) is 4 above the mean.

## What this does not show

None of this trains anything. Tabular numbers on toy tables say nothing about a physics simulator, about deep or continuous-control methods such as PPO or SAC, about whether five seeds are enough, or about statistical significance: the standard error is a description of these five numbers, not a test. Whether a real experiment protocol is sound needs a human to read it.
