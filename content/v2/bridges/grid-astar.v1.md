# Grid search, heuristics and exact shortcut checks

This optional bridge takes about 20 minutes. You can skip it and open any activity. Reading it creates no evidence. It covers a small, declared 2D world; it is not a general planning course.

## The world

An occupancy grid is a table of cells, each free (`.`) or blocked (`#`). A cell is written (row, col), row 0 at the top. In a 4-connected grid the robot moves up, down, left or right, each move costing 1. In an 8-connected grid it may also move diagonally for sqrt(2) = 1.414214. A common safety rule, used here, forbids corner cutting: a diagonal move is legal only if both orthogonal neighbours it passes are free. State the rule you use; a different rule gives different costs.

A path is a list of cells with one legal move between neighbours. Its cost is the sum of the move costs. The cheapest cost is a number you can check by hand on small grids; the path itself may not be unique, so check cost and validity, not one particular route.

## A* in one paragraph

A* keeps cells to try (the open set), each with g, the best cost found so far from the start, and a heuristic h, an estimate of the remaining cost. It always expands the open cell with the smallest f = g + h. It stops when the goal is removed from the open set, not when the goal is first seen. If h never exceeds the true remaining cost (admissible) and obeys h(a) <= cost(a, b) + h(b) on every move (consistent), the first time the goal is removed its g is the optimal cost.

Good heuristics on an empty grid: for 4-connectivity the Manhattan distance |dr| + |dc|; for 8-connectivity the octile distance max(|dr|, |dc|) + (sqrt(2) - 1) * min(|dr|, |dc|). Obstacles can only make the true cost larger, so both stay admissible on any grid. Manhattan distance with 8-connectivity is NOT admissible: from (0, 0) to (5, 5) it is 10 but the true cost on an empty grid is 5 sqrt(2) = 7.07. An inadmissible heuristic can steer A* to a worse path. A weight w > 1 in f = g + w * h trades optimality for speed: the returned cost is at least the optimum and at most w times it.

## Worked example

Grid (rows top to bottom): `..` and `#.`. Start (0, 0), goal (1, 1), 8-connected, no corner cutting. The diagonal (0, 0) to (1, 1) needs (0, 1) and (1, 0) free, but (1, 0) is blocked, so it is illegal. The cheapest legal path is (0, 0), (0, 1), (1, 1): cost 2. If corner cutting were allowed the cost would be 1.414214. The octile heuristic at the start is 1.414214, below the true cost 2, so it is admissible but not exact.

## Running out of budget is not "no path"

If you limit a search to B expansions and stop with the goal not yet expanded and cells still in the open set, you know only that the budget ran out. Report "budget exhausted". Report "unreachable" only when the open set became empty, meaning every reachable cell was tried. A larger budget may still find a path.

## Checking a straight shortcut exactly

A grid path wiggles; a straight segment between two waypoints is shorter if it is collision free. Test it exactly, not by sampling. Treat a shelf as a closed axis-aligned rectangle [xmin, xmax] x [ymin, ymax]. Write the segment as p + t (q - p) with t from 0 to 1 and clip it against each pair of sides: for the x sides, t runs between (xmin - px)/dx and (xmax - px)/dx; do the same for y; the segment hits when the intersection of these t ranges with [0, 1] is not empty. Handle dx = 0 (the x range is all t or none). Touching an edge or a corner counts as a hit.

Why not sample? A wall 0.03 m wide between two samples 1 m apart is never inside any sample, so a sampled check reports "clear" for a crossing segment (tunneling). Checking only the endpoints has the same flaw. A robot with a square body of half-width h sweeps exactly the segment grown by h, so test the segment against each shelf grown by h on all four sides.

## Scope

You can check a grid A* cost against an exhaustive search on a small grid, and an exact segment test against hand cases. This does not show that a real planner works: a randomised sampling planner such as RRT proves nothing about completeness from one run, arm planning needs configuration space, and real robots need footprints, heading, dynamics, moving obstacles and localisation error. Practice and AI solutions never automatically establish verified mastery.

Original educational content © 2026 Le Trong Nghia, CC BY 4.0. Author draft; independent review pending.
