# Worked example: a community tool-library proposal

This is an original illustrative scenario, not an executed test receipt.

## Facts

A two-page proposal asks a neighbourhood council to approve a shared tool library. The author confirms:

- Primary readers: R1 council member who approves the budget; R2 volunteer coordinator who will run the library.
- Secondary reader: R3 resident who only wants to know how to borrow.
- Reading situation: council members pre-read the evening before the meeting.
- Intent: C1 tools are lent for at most seven days; C2 a deposit is required only for power tools; C3 volunteers check tools on return, not on loan.
- Constraint: W1 the attached sign-up form is fixed and must not be edited.
- Out of scope: opening hours and insurance wording, which belong to the operating handbook.

Task questions, with the key kept private:

| Reader | Question | Expected answer |
|---|---|---|
| R1 | What does the council pay for, and what risk remains? | Shelving and tags; damage on return |
| R2 | When exactly do volunteers inspect a tool? | On return (C3) |
| R3 | Do I pay a deposit for a ladder? | No; only power tools (C2) |

## Round 1

Fresh readers receive the Markdown copy and their briefs. R2 answers "on loan and on return". The text says "volunteers check every tool" in the overview and "inspection happens when the tool comes back" in the procedure. That is a contradiction (class 1). R3 skims only "How to borrow" and answers "not found" for the ladder deposit, because the deposit rule appears only in the budget section. That is a navigation issue (class 1). R1 asks who pays for a lost tool; the proposal is silent, and the answer is a policy choice (class 3, pending decision D1).

Before editing, the main agent runs `sweep.py` for "check", "inspect" and "deposit" and finds a third statement in the FAQ. All three inspection statements are rewritten together to say "on return". The deposit rule is stated once in "How to borrow", and the budget section now points to it. The export comparison shows only those four lines changed.

Round 1 retrospective: the skimming reader exposed a rule that existed only outside their path. Next round, every secondary-reader task question names the section that reader actually reads.

## Round 2

New readers include a question for each changed sentence. R2's consistency check lists all inspection statements and finds them consistent. R3 now finds the deposit rule. R1 reports that "power tools" is undefined: is a cordless drill a power tool? Defining the term is a class 1 fix. The main agent writes both branches: "Power tools are tools with a motor or battery; all other tools need no deposit."

## Round 3

Only R1 and R2 join, because R3's sections did not change materially. Both answer every task question. R2 suggests reordering two sentences, which is class 6 polish. No new issue or process change appears, so the loop stops.

## Report

- Changed: the inspection timing in three places, the deposit rule moved into the borrowing section, and a definition of "power tools".
- Pending: D1, who pays for a lost tool.
- Declined: opening hours, which are out of scope.
- Unreviewed: the round 3 polish edit was not read by a later reader.
