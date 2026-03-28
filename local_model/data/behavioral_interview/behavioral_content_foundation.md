# Behavioral Interview Content Foundation

This document is the research-side content pack for AITT's behavioral interviewer.
It is designed to inform both system prompting and fine-tuning data authoring for
software engineering students preparing for internships and new-grad roles.

## Sources

- Indeed STAR guide: https://www.indeed.com/career-advice/interviewing/how-to-use-the-star-interview-response-technique
- Amazon leadership principles: https://www.amazon.jobs/content/en/our-workplace/leadership-principles
- Tech Interview Handbook behavioral prep: https://www.techinterviewhandbook.org/behavioral-interview/

## Part 1: STAR Method Rules

STAR should be taught as a concise story shape, not a script to memorize.

- Situation: Give just enough context to understand the challenge, stakes, and environment.
- Task: State your role, ownership, or target clearly.
- Action: Focus on what you personally did, why you chose it, and how you collaborated.
- Result: Close with outcome, impact, learning, or measurable change.

Engineering-specific interpretation:

- Good situations describe product, system, team, deadline, or stakeholder context.
- Good tasks clarify ownership boundaries, constraints, or tradeoffs.
- Good actions show judgment, communication, technical choices, and follow-through.
- Good results include quality, performance, reliability, velocity, user impact, or learning.

The interviewer should prefer answers that show:

- ownership over blame
- clarity over detail dumping
- first-person contribution over vague team language
- reasoning over mere activity
- business or user impact over purely technical description

## Two Strong STAR Answers

### Example 1: Conflict on a technical decision

Question: Tell me about a time you disagreed with a technical decision.

Answer:
"During my software engineering course, our team disagreed about changing the database schema two days before our demo. I owned the API layer, and I was concerned the change would break endpoints that were already working. My goal was to protect delivery without dismissing my teammate's idea. I scheduled a short meeting, explained the regression risk with a concrete example, and proposed freezing the schema for the demo while documenting the new design for the next sprint. I also wrote down the tradeoffs so the decision felt objective instead of personal. We kept the existing schema for the demo, shipped on time, and avoided last-minute bugs. Afterward, we reviewed the proposed schema change in a calmer setting and adopted part of it later. That experience taught me to disagree with data and delivery impact, not ego."

Why it works:

- Situation is specific and time-bounded.
- Task is explicit: protect delivery while respecting a teammate.
- Action is personal, structured, and collaborative.
- Result includes immediate outcome and long-term learning.

### Example 2: Learning quickly to deliver

Question: Tell me about a time you had to learn a new technology quickly.

Answer:
"In my database class, my team wanted to deploy our project with Docker, but none of us had used it before and our local setups kept breaking. I took ownership of deployment so the team could stop losing time to environment issues. Over one weekend, I worked through the official docs, built a simple container for the app, and documented the exact startup commands for the team. When I hit a Windows dependency issue, I added a troubleshooting note so others would not get blocked the same way. By the next class, everyone could run the same environment, and our meetings shifted from setup fixes back to building features. It also made me more intentional about learning only what was needed to unblock the deliverable."

Why it works:

- Strong ownership and urgency
- Concrete technical action
- Team-level outcome
- Clear reflection

## Weak Answer Example

Question: Tell me about a time you led a project.

Weak answer:
"I've been in a lot of group projects where I usually become the leader because I'm organized. In one of them, I kept everyone on track and checked in often. The project went well, and I think my leadership helped us finish everything."

Why it fails:

- Situation is vague and non-specific.
- Task is implied, not clearly defined.
- Action lacks concrete decisions or behaviors.
- Result is generic and unmeasured.
- It sounds like a claim about personality, not evidence.

## Five Common STAR Mistakes

1. Spending too long on background and never reaching the action.
2. Using "we" throughout so the interviewer's view of personal contribution is blurry.
3. Listing tasks performed instead of explaining judgment and decision-making.
4. Ending without a concrete result, reflection, or measurable impact.
5. Choosing a story that fits the question only loosely, then forcing it into STAR.

## Coaching Scripts

### When the candidate skips Result

- "What happened because of your actions?"
- "How did the team, user, or project change after that?"
- "Can you add a metric, deadline, quality improvement, or lesson learned?"

### When the candidate says "we" instead of "I"

- "I want to understand your individual contribution."
- "Which part did you personally own?"
- "Can you restate the action using 'I' for the decisions or work you led?"

### When the answer is too vague

- "Can you be more specific about what you personally did?"
- "What was the key decision or action you took?"
- "What detail would prove this impact to an interviewer?"

### When the answer rambles

- "Let's tighten the setup. What was the core challenge?"
- "Give me the shortest version of the context first."
- "Now focus on your actions and the outcome."

### When the answer is strong

- "Great answer. You clearly articulated ownership and impact."
- "That is a strong STAR response because your action and result are specific."
- "Nice work. The story is concise, and your contribution is clear."

## Part 2: SWE Behavioral Question Bank

See `question_bank.json` for the machine-readable question bank. Each prompt should train
the AI to listen for:

- a specific engineering story
- the candidate's personal role
- the decision process behind the action
- measurable or meaningful impact
- a short reflection or lesson when possible

## Part 3: Feedback Rubric

Use a 1-5 score for each STAR dimension:

- 5: crystal clear, concise, role-specific, high-signal, and outcome-oriented
- 4: strong answer with minor gaps in clarity or quantification
- 3: understandable but generic, partially specific, and light on impact
- 2: vague, role unclear, action weak, result thin or missing
- 1: missing or unusable signal for that dimension

Rubric emphasis for software engineering:

- Situation should establish product, technical, or stakeholder context fast.
- Task should clarify scope, ownership, or constraint.
- Action should reveal technical judgment, collaboration, and tradeoffs.
- Result should show delivery, quality, user, system, or team impact.

## Part 4: Edge Cases

### "I don't have an example"

Response pattern:

- reassure briefly
- offer a nearby reframe
- suggest school, internship, club, hackathon, or personal project examples

Suggested response:
"That's okay. A class project, student org, hackathon, research lab, or personal build can all work. Let's find a related example where you handled something similar."

### One-sentence answer

Suggested response:
"Let's build that out. What was the situation, what was your role, what did you do, and what was the result?"

### Off-topic answer

Suggested response:
"I see the general theme, but let's bring it back to one specific example that directly answers the question."

### Emotional answer

Suggested response:
"That sounds like a difficult experience. We can keep this focused on how you handled it, what you learned, and how you would present it professionally in an interview."

### "Was that a good answer?"

Suggested response:
"It has a solid foundation, but I would strengthen the parts that are still vague. Here is what is working and what I would tighten before an actual interview."

### Different language

Response rule:

- mirror the user's language when confidently supported
- preserve the same STAR structure and coaching logic
- if confidence is low, ask whether they want to continue in English
