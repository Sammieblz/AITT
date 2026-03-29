interface DailyTip {
  headline: string
  body: string
  category: string
}

const TIPS: DailyTip[] = [
  { category: 'STAR method', headline: 'Open with the outcome.', body: 'Start your answer by stating the result, then work backwards through the situation, task, and action. Interviewers remember the last thing they hear — but they stay engaged when they know where you\'re going.' },
  { category: 'Storytelling', headline: 'Name the conflict clearly.', body: 'Vague tension doesn\'t land. Be specific: "My manager wanted to ship in two weeks. The codebase had no tests and a known race condition." Clarity creates credibility.' },
  { category: 'Leadership', headline: 'Show influence without authority.', body: 'The best leadership stories often involve no direct reports. Focus on how you aligned people around a goal, resolved disagreement, or moved work forward when it wasn\'t your job to.' },
  { category: 'Problem solving', headline: 'Quantify the scale of the problem.', body: '"A slow query" is less compelling than "a query that added 800ms to every page load, affecting 40k daily users." Numbers give interviewers something to hold onto.' },
  { category: 'STAR method', headline: 'Your action, not the team\'s.', body: 'Interviewers want to know what YOU did. It\'s fine to mention the team, but anchor every sentence in your specific contribution: "I proposed… I wrote… I convinced…"' },
  { category: 'Conflict & collaboration', headline: 'Show you listened first.', body: 'In conflict stories, demonstrate that you understood the other person\'s position before pushing back. "I wanted to understand their concern, so I asked…" signals maturity.' },
  { category: 'Achievement & impact', headline: 'Impact > effort.', body: 'Don\'t just describe how hard you worked. Describe what changed because you did the work. Promotions, revenue, latency, retention — tie your effort to a measurable outcome.' },
  { category: 'Preparation', headline: 'Have five core stories ready.', body: 'Most behavioral questions can be answered with 5 well-prepared stories covering: leadership, failure, conflict, achievement, and growth. Adapt them to fit the specific question.' },
  { category: 'STAR method', headline: 'The Result should close the loop.', body: 'Don\'t end with "and it worked out." What specifically happened? Ship date met, team aligned, bug resolved, user complaint rate dropped. The Result is your proof point.' },
  { category: 'Storytelling', headline: 'Cut the backstory.', body: 'Situational context should take 15-20% of your answer — not 60%. Get to the conflict and your action faster. Interviewers lose the thread when the setup runs long.' },
  { category: 'Failure', headline: 'Own the failure fully.', body: 'Hedging ("it wasn\'t entirely my fault") undermines the story. Interviewers know projects are messy — they want to see that you can take ownership and learn without making excuses.' },
  { category: 'Growth', headline: 'Show a before and after.', body: 'Growth stories are most convincing when you articulate a specific gap — "I used to avoid giving critical feedback" — and then demonstrate what changed and what you did differently.' },
  { category: 'Problem solving', headline: 'Explain your decision-making process.', body: 'What information did you gather? What trade-offs did you consider? How did you decide? Interviewers at senior levels care as much about your reasoning as your answer.' },
  { category: 'Leadership', headline: 'Disagreement done well impresses.', body: 'Saying you disagreed with a manager and were proved right isn\'t a red flag — it\'s a green one, if you handled it professionally. Show the conversation, not just the outcome.' },
]

export function getTodaysTip(): DailyTip {
  const start = new Date('2026-01-01')
  const today = new Date()
  const dayOfYear = Math.floor((today.getTime() - start.getTime()) / 86_400_000)
  return TIPS[Math.abs(dayOfYear) % TIPS.length]
}
