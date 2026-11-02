# A task state machine with a watchdog

This optional bridge takes about 20 minutes. You can skip it and open any activity. Reading it creates no evidence. It covers a small, made-up, simulated pick-and-deliver task. It is not a safety course and nothing here is a safety function.

## Why a state machine

A robot task is a sequence of phases: approach an object, grasp it, carry it, release it. An executive is the part of the software that decides which phase is current and what to command next. The simplest honest model is a plain state machine: a finite list of states, a finite list of events, and a table that says, for each (state, event) pair, the next state and the commands to emit. You can check a table by hand and enumerate it by machine, which is exactly why this is a good first model before any behaviour-tree library.

States used here: IDLE, APPROACH, GRASP, TRANSPORT, RELEASE, DONE, FAULT, and a hold state for each active phase (HOLD_GRASP and so on) that remembers which phase it interrupted. Events: start, reached, grasped, released, grasp_failed, obs (a new observation arrived), tick (time passes), cancel, fault, resume, reset. An event is a pair (time in milliseconds, name).

## Preconditions and guards

A transition may carry a guard: a condition that must hold or the transition does not happen. Here start from IDLE requires a fresh observation, because moving on a world model of unknown age is a hazard. When a guard fails, say what happens: here the machine stays where it is and emits nothing. An unlisted (state, event) pair is also a decision: ignore it. Write that decision down; a hidden default is a bug waiting for an unusual event order.

## The watchdog and explicit time

An observation has an age: the time of the current event minus the time of the latest obs event. It is stale if there was none, or if the age is greater than a declared max_age. Pick the boundary on purpose: here an age exactly equal to max_age is still fresh, and max_age + 1 ms is stale. Tests at the boundary catch an off-by-one that no ordinary test finds.

When the machine is in an active phase and the observation is stale, the executive must stop the motion and enter the matching hold state. Two design points matter. First, priority: the watchdog is checked before the normal table, so a reached event on a stale observation does not start the next phase; the event is discarded. Second, time only advances when an event arrives. A machine with no events never checks its watchdog, so a real system needs its own timer (the tick event stands for it here). Also notice that a stop command is only a request; this toy cannot show that the hardware obeyed it.

## Cancel and fault

Cancel and fault outrank the watchdog. Cancel in an active phase emits stop and returns to IDLE with the retry counter cleared; cancel in a hold state returns to IDLE and emits nothing, because the machine is already stopped. Fault goes to a latched FAULT state, again emitting stop only if the machine was moving. FAULT leaves only on an explicit reset. A second stop in a state that is already stopped is not a harmless extra: it hides which transition did the stopping when you read a log.

## Bounded retry and no blind re-entry

The retry counter is set to 0 by an accepted start, by reset and by cancel; fault and reaching DONE keep it, and only a grasp retry or a resume adds 1. A failed grasp may be retried, but not forever: each retry adds 1 to a counter, and when the counter reaches max_retries the next failure goes to FAULT. A hold may be recovered, but never by itself. A fresh obs arriving in HOLD_GRASP does not restart anything; only an explicit resume does, and only if the observation is fresh and the same retry budget is not used up. Recovery re-issues the phase command, because the stop discarded the old goal. Blind re-entry means jumping back into a phase because a timer ran out or an event happened to arrive, without checking that the world model is current and that the budget allows it.

## A worked example

max_age = 5, max_retries = 1. Events: (0, obs), (1, start), (2, reached), (9, tick), (10, obs), (10, resume), (11, reached).

- (0, obs): age 0, nothing else changes; state IDLE.
- (1, start): age 1, fresh, so IDLE goes to APPROACH and emits move_pick.
- (2, reached): age 2, APPROACH goes to GRASP, emits close_gripper.
- (9, tick): age 9 > 5 in the active phase GRASP, so the watchdog gives HOLD_GRASP and stop.
- (10, obs): age 0; in a hold state obs only refreshes the observation. No automatic restart.
- (10, resume): age 0, fresh, retries 0 < 1, so the machine returns to GRASP, emits close_gripper, counter 1.
- (11, reached): GRASP has no rule for reached, so nothing happens.

States after each event: IDLE, APPROACH, GRASP, HOLD_GRASP, HOLD_GRASP, GRASP, GRASP. Now repeat the stale tick: another resume would find retries 1, which is not below 1, so the machine would stay in HOLD_GRASP until a cancel or fault.

## A trace invariant

You can also check a log without knowing the machine. The invariant "no motion command while stale, cancelled or faulted" looks only at events and emitted commands: flag any event that emitted a motion command when the observation was stale, when the event itself was a cancel or fault, when a fault has occurred and no reset since, or when a cancel has occurred and no start since. Staleness alone is not enough: after a cancel with a fresh observation, motion is still wrong. Running every short event sequence through a machine and through this monitor is a cheap exhaustive test of the table.

## Scope

You can compare a state machine with a hand-written table, check every short event sequence, and test the stale boundary exactly. This does not make a robot safe. Hazard analysis needs a human review of what can go wrong; a stop command may be lost or ignored; clocks and sensors fail in ways that look fresh; real timing, hardware safety functions and standards are outside this toy. Practice and AI solutions never automatically establish verified mastery.

Original educational content © 2026 Le Trong Nghia, CC BY 4.0. Author draft; independent review pending.
