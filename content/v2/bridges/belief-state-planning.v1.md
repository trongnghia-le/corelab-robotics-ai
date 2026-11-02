# Belief states, sensing and plans that must work in every world

This optional bridge takes about 25 minutes. You can skip it and open any activity. Reading it creates no evidence. It covers a small, made-up, symbolic task that you can enumerate completely by hand or by machine. It is not perception, language understanding or a robot course.

## Possible worlds and a belief

A robot rarely knows the whole state of its world. Suppose it must fetch a key that lies in exactly one of a few closed boxes, and it does not know which. Write down every state the world could be in: one possible world per box ("the key is in the drawer", "the key is on the shelf", ...). The list of worlds the robot cannot yet rule out is its belief state. When the worlds are not equally plausible, give each a weight; a world's probability is its weight divided by the sum of the weights of the worlds still possible.

A world is a set of facts such as at(home) and in(key,drawer). Closed-world reading: a fact that is not listed is false. Objects are the names inside the brackets (home, key, drawer).

## Actions with preconditions and effects

A STRIPS-style action has a name, preconditions (facts that must be true to start it), a delete list and an add list. Applying it to a state: if some precondition is false the action is not applicable; otherwise remove the deleted facts first, then add the added facts (so a fact in both ends up true), and sort or treat the result as a set. For example open_drawer needs at(drawer) and closed(drawer), deletes closed(drawer) and adds open(drawer).

## Sensing actions and belief update

A sensing action does not change the world. It needs preconditions too (you cannot look in a box you have not opened), and it reports whether one fact is true. The robot then keeps exactly the worlds that agree with the report and discards the rest, in whatever order they were listed. That is the belief update. Three habits matter:

- Apply observations one after another to what is left; the second look filters the survivors of the first.
- Renormalise weights over the survivors: the new probability is a survivor's weight over the survivors' total weight.
- If no world survives, the observation contradicts the model. Report that; it is not a probability of zero for everything, it means the model of the world was wrong.

## Conditional plans and counterexamples

A fixed list of actions assumes one particular world. A conditional plan is a tree: after a sensing action it branches on what was reported, and each branch ends in a stop. To check a plan against a belief, run it in every possible world, which is a finite, exact computation here. In one world the plan fails if an action's precondition is false there (reason: precondition) or if the goal is not true when the plan stops (reason: goal). A world where it fails is a counterexample: a hidden state the planner did not account for. The plan is correct for the belief only if there is no counterexample. The probability of success is the total weight of the successful worlds over the total weight; a high number is still not a guarantee, only 1 is.

## Grounding is a separate question

A plan can talk about things that are not in the belief at all: open_cabinet when no cabinet appears in any world, or wipe_with_cloth when no fact mentions a cloth. Such a plan is ungrounded. Feasibility asks whether the preconditions hold; grounding asks whether the objects exist. Check both, and note that fixing one does not fix the other.

## Worked example

Places: a locker and a crate. The locker may be locked. Three worlds, with weights: P (key in the locker, lid unlocked) 3, Q (key in the locker, lid locked) 1, R (key in the crate, lid unlocked) 2. The robot starts at home and everything is closed.

Plan S: go to the locker, open it, grab the key, go home, deliver, stop. Open needs the lid unlocked and grab needs the key to be in the locker.

- World P: every precondition holds and the key is delivered. Success.
- World Q: open_locker needs unlocked(locker), which is false. Fail, reason precondition. This is a counterexample caused by a hidden lock.
- World R: the lid opens, but grab needs in(key,locker), which is false. Fail, reason precondition. A second counterexample.

Probability of success = 3/(3 + 1 + 2) = 0.5. Suppose the robot then tests the lid and it is locked. Update: only Q survives, so S cannot succeed in the only remaining world, and the belief tells you the key is in the locker behind a lid you cannot open. If the test says unlocked, P and R remain with weights 3 and 2: the key is in the locker with probability 3/5 = 0.6.

A repaired plan S2 senses first: test the lid. If unlocked: open the locker and look; if the key is there, grab it, go home, deliver; otherwise go to the crate, open it, grab, go home, deliver. If locked: go to the crate, open it, look; if the key is there, grab, go home, deliver; otherwise stop. S2 now handles P and R, and in Q it stops with the goal false, so Q stays a counterexample until the plan can get the lid open, or an honest "cannot do this" branch is accepted. Looking alone would not have fixed anything: a branch has to reach the place, open it, look and fetch.

## What this does not show

This is an exact toy on a handful of symbolic worlds. Real perception is noisy and can name things wrongly, the number of hidden states is usually far too large to list, actions fail unpredictably, geometry and timing matter, and a plan written in free text by a person or a language model needs a human to interpret it before anything moves. Passing a finite plan check demonstrates nothing about whether a robot reasons well, and nothing here certifies cognition or safety. Practice and AI solutions never automatically establish verified mastery.

Original educational content © 2026 Le Trong Nghia, CC BY 4.0. Author draft; independent review pending.
