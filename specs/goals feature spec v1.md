# Goals Enhancement Specification

## Context
We already have a partially working goals feature. Now we want to:
1. **Allow users to create systematic investment plans (SIPs)** that automatically contribute to a goal each month.
2. **Permit users to allocate a portion of their existing portfolio** to a new goal immediately (i.e., initial lumpsum from pre-existing holdings).
3. **Prompt the user to associate newly added investments** with a goal (if desired).

---

## Implementation Instructions

1. **Database Changes**
```aider
	•	Add a new column recurring (BOOLEAN or INT) to goal_investments table:
	•	recurring = 1 means it’s a monthly SIP.
	•	recurring = 0 means it’s a one-time lumpsum.
	•	Optional: If needed, store the SIP start date, end date (or indefinite if no end).
	•	You can also consider a frequency field (monthly, quarterly) if you want more than monthly in the future.
```
2.	Implement SIP Creation
```aider
	•	Under “Associate an Investment with a Goal”:
	•	Prompt the user: “Is this a one-time lumpsum or a recurring SIP?”
	•	If lumpsum: Insert a single record into goal_investments with investment_type = "Lumpsum" and recurring = 0.
	•	If SIP:
	•	Insert one record with recurring = 1, investment_type = "SIP", and the monthly amount.
	•	Optionally store start_date (defaults to today) and end_date (optional).
	•	The system needs a job or function to automatically add a new entry every month (or the user can manually trigger it for now).
```
3.	Auto-Allocation of Existing Portfolio at Goal Creation
	•	When user adds a new goal:
	•	Ask “Do you want to allocate any existing portfolio to this goal?”
	•	If yes, let them specify an amount (or default to an existing lumpsum).
	•	Create a lumpsum record in goal_investments with that amount.

4.	Prompt to Associate Investments When Adding Stocks/Funds
	•	In “Add Stock” (or mutual fund) flow:
	•	After the user enters purchase details, ask “Would you like to associate this purchase with any existing goal?”
	•	If yes:
	•	Provide a list of existing goals to pick from.
	•	Insert a lumpsum entry in goal_investments referencing that goal, investment_date = today, amount = purchase_price × units.
	•	If no:
	•	Just add the investment to the portfolio without linking to a goal.

5.	Auto-Add SIPs Each Month  
	•	If we want real monthly records, we can implement:
	•	A function apply_sips_for_the_month() that runs to insert lumpsum entries for each active SIP into goal_investments.
	•	If end_date is reached, it stops.

6.	Update Calculations in “View Goals / Progress”
Where do we incorporate lumpsum + SIP amounts?
- Ensure we sum up all records in `goal_investments` for that goal
- Possibly skip or partially count future SIPs if we only track them monthly
•	Summation step:
SELECT SUM(amount)
FROM goal_investments
WHERE goal_id = ?

7.	Ensure Dormant Priority Halts Future SIPs
	•	If priority_level == 'Dormant', do not insert SIP records when apply_sips_for_the_month() runs.
	•	Possibly reallocate that SIP’s monthly amount to other goals if needed.