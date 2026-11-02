# Grid Bayes localization

This optional bridge takes about 20 minutes. You can skip it and open any activity. Reading it creates no evidence.

**The setting.** A robot is somewhere along a corridor split into n cells numbered 0, 1, ..., n-1. We do not know the cell, so we keep a **belief**: a list with one probability per cell, all at least 0 and summing to 1. A uniform belief over 4 cells is [0.25, 0.25, 0.25, 0.25]. A map says which cells have a door (1) and which are plain wall (0). Everything here is a toy model on paper or in a short script: no random numbers, no real sensor.

**Two operations, repeated.**

1. **Sense (Bayes update).** A door sensor reports z = 1 ("door") or z = 0. It is right with probability p and wrong with probability 1 - p. For each cell, the *likelihood* is P(z | robot in that cell): p if the map agrees with z, otherwise 1 - p. Then

   posterior(i) = prior(i) x likelihood(i) / (sum over all cells of prior x likelihood).

   The division is the **normalisation**; without it the numbers no longer sum to 1. A likelihood is not a belief: it does not sum to 1 over cells.

2. **Move (prediction).** The robot is told to move one cell right, but the motion is noisy. A **motion kernel** lists the probabilities of each displacement, for example 0 cells with 0.1, 1 cell with 0.8, 2 cells with 0.1. Every cell i sends belief(i) x kernel to the cells i, i+1, i+2. New belief(j) is the sum of everything that arrives at j. This is an exact convolution. You must declare what the ends do: on a **ring** the cell numbers wrap round (cell n follows as cell 0), while with **walls** a robot pushed past the end stays in the end cell, so the mass piles up there instead of vanishing.

One filter step is: sense, then move. Mixing the order gives a different (wrong) answer for the same readings.

**Worked example.** A ring of 4 cells, world = [1, 0, 0, 1], uniform prior, sensor right with p = 0.8, reading z = 1.

- Likelihood: [0.8, 0.2, 0.2, 0.8].
- Products with the prior 0.25: [0.2, 0.05, 0.05, 0.2]; their sum is 0.5.
- Posterior: [0.4, 0.1, 0.1, 0.4].

Now cells 0 and 3 tie for the highest belief. They are next to each other on the ring and both have a door, so one reading cannot separate them. Suppose the robot then moves exactly one cell (kernel 100% on displacement 1): the belief becomes [0.4, 0.4, 0.1, 0.1]. A second reading z = 0 has likelihood [0.2, 0.8, 0.8, 0.2]; products [0.08, 0.32, 0.08, 0.02], sum 0.5 and posterior [0.16, 0.64, 0.16, 0.04]. Cell 1 now stands out.

**Ambiguity.** If the whole map looks the same after shifting by some number of cells (for example [1, 0, 1, 0] shifted by 2), two cells have identical sensor behaviour at every moment. Their beliefs stay equal forever, however many readings arrive. That is a property of the map, not of the sensor noise. To detect it, list all cells tied for the largest belief.

**An impossible reading.** If the sensor were perfect (p = 1) and the reading contradicted every cell that still has belief, every product is 0 and the normalising sum is 0. Dividing would be 0/0. An honest implementation stops with an error instead of inventing a belief. A sensor with p = 0.999 never produces an exact zero, which is why overconfident likelihoods are dangerous: they turn one bad reading into certainty.

**Particles in one paragraph.** Instead of a probability per cell, keep a few samples (particles), each with a position and a weight. Sensing multiplies each weight by the likelihood of the particle's cell, then renormalises. The **effective sample size**, ESS = 1 / (sum of squared normalised weights), says how many equally weighted particles would carry the same information: it is N for equal weights and 1 when one particle holds everything. **Systematic resampling** replaces the set by N copies drawn with one number u0 in [0, 1): the positions are (u0 + k)/N for k = 0..N-1, and each position picks the first particle whose cumulative normalised weight exceeds it. A weight-0 particle is never picked, and a particle with N x weight of 1.8 appears 1 or 2 times. Give u0 explicitly and the result is fully checkable by hand; with random draws you would need statistics, which this lab does not cover.

**Check yourself before you start.** Starting from a uniform prior, predict the ring posterior for world = [1, 0, 0, 1] after a single reading z = 0 with p = 0.8, and the ESS of weights [1, 1, 1, 1] and [4, 0, 0, 0].

**Scope.** This is a 1-D discrete Bayes filter and a few deterministic particle operations, checked numerically. It is not SLAM, not a continuous-state filter, and says nothing about real sensors: real maps are wrong, sensor errors are correlated, robots are kidnapped, and particle sets collapse. Passing the exercises does not show that a robot localizes safely.

Try the bridge practice, explain a belief update aloud, then choose the Localization activity. Ask a Socratic tutor for a conceptual question or one next step; declare any external help. Practice, videos and AI solutions never automatically establish verified mastery.

Original educational content © 2026 Le Trong Nghia, CC BY 4.0. Author draft; independent review pending.
