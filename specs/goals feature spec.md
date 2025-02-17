# Implement the goals feature in the portfolio manager cli application

## High-Level Objective

- **Implement Goals Feature**: Provide a robust, intuitive, and accurate goals system for the portfolio manager that allows users to:
  1. Create, edit, and delete financial goals
  2. Associate actual investments (SIPs/lumpsums) with each goal
  3. Track progress over time, including a realistic CAGR calculation
  4. Suggest additional SIP amounts if a goal is falling behind
  5. Manage goal priority (High, Standard, Low, Dormant) and reallocate SIPs accordingly

## Mid-Level Objectives

1. **Database Schema for Goals & Investments**  
   - Create (or refine) `goals` table with fields:
     - `id`, `name`, `target_amount`, `time_horizon`, `priority_level`, `expected_cagr`, `goal_creation_date`
   - Create (or refine) `goal_investments` table with fields:
     - `id`, `goal_id`, `investment_type` (SIP/lumpsum), `investment_date`, `amount`
   - Ensure we do not rely on “% of portfolio” logic; actual amounts are tied to each goal.

2. **Core Goal Logic**  
   - For each goal:
     - Summarize all **investments** from `goal_investments`.
     - Calculate `current_progress`, `years_passed`, `cagr_achieved`.
     - Compute future value: `projected_future_value = current_progress * ((1 + expected_cagr / 100) ^ years_remaining)`
     - If user sets a `dormant` priority, stop future SIPs and reallocate capital proportionally among active goals.

3. **User Flow and Menu Integration**  
   - **Manage Goals** menu:
     1. **Add a Goal** → Provide name, target, horizon, expected CAGR, priority.
     2. **Associate an Investment with a Goal** → A lumpsum or new SIP.
     3. **View Goals / Progress** → Summaries for each goal, shortfall, or success.
     4. **Edit Priority / Dormant** → Let user mark a goal as dormant or adjust priority.
     5. **Delete Goal** → Remove a goal if no longer needed.
   - This replaces the old notion of “goal = x% of portfolio.”

4. **SIP Reallocation & Dormant Mode**  
   - If a goal is set to **Dormant**:
     - Stop future SIP allocations to that goal.
     - Optionally reallocate the monthly SIP portion to other goals based on priority weights.
   - If we **reactivate** a dormant goal, recalculate allocations.

5. **Comprehensive Debugging and Logging**  
   - Print debug info for:
     - `current_progress`, `years_passed`, `cagr_achieved`
     - `projected_future_value`, `shortfall`, `suggested_SIP`
   - This helps the user (and developer) confirm correct calculations.

6. **(Optional) Historical Goal Tracking**  
   - If time allows, track each goal’s progress monthly or daily.  
   - Provide a small chart or table showing how much each goal has grown over time.

## Implementation Notes

- **Technical Details**:
  - Each goal is identified by `goal_id`.
  - `goal_investments.goal_id` references which goal the investment belongs to.
  - `current_progress` should come from the sum of lumpsum + total SIP contributions recorded for that goal.
  - `cagr_achieved` is calculated only if `years_passed > 0`.
- **Dependencies & Requirements**:
  - Follow the existing CLI patterns: add to `main.py` menu, or add new files as needed.
  - Keep consistent with existing Python code style (snake_case, docstrings, etc.).
  - If older columns like `allocation_percent` exist, **remove** or ignore them.
- **Coding Standards**:
  - Use Pythonic code and docstrings for clarity.
  - For DB queries, maintain the pattern used in `database.py`.
- **Other Guidance**:
  - Test thoroughly with debug logs.
  - Handle edge cases, like newly created goals with zero days passed or reactivating a dormant goal.

## Context

### Beginning Context

- **Files That Exist**:
  - `main.py` (main CLI loop, user menu)
  - `database.py` (managing DB, price updates)
  - Possibly old references to goals logic that we are removing or rewriting

### Ending Context

- **Files That Will Exist**:
  - `main.py` updated with a new “Manage Goals” menu flow
  - A new or updated file that handles the “goals” logic (could be in `database.py` or separate)
  - Possibly `goals.py` or `goal_investments.py` if we separate logic thoroughly

## Low-Level Tasks
> Ordered from start to finish

1. **Create / Update DB Schema**
```aider
	•	Write view_goal_progress(goal_id) to compute real progress from goal_investments.
	•	Implement calculate_required_investment() for realistic SIP suggestions.
	•	add record_goal_investment(goal_id, amount, type) if lumpsum or new SIP is assigned.
```
2.	Implement Core Goal Logic
```aider
	•	Write view_goal_progress(goal_id) to compute real progress from goal_investments.
	•	Implement calculate_required_investment() for realistic SIP suggestions.
	•	add record_goal_investment(goal_id, amount, type) if lumpsum or new SIP is assigned.
```
3.	Integrate with Menu / User Flow
```aider
	•	Provide new CLI commands: “Add a Goal”, “Associate an Investment”, “View Goals/Progress”, “Edit Priority / Dormant”. "Delete Goal(s)".
	•	Make sure each sub-command references the new or updated code from step 2.
```
4.	Test & Debug
```aider
	•	Insert sample goals & investments.
	•	Print debug logs for initial_investment, current_progress, cagr_achieved, suggested_SIP.
	•	the shell command to run the app is uv run main.py
```