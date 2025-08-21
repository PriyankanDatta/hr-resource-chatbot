# UI Spec (v1)

## 13.1 Chat flow
- Input box + Send.
- Show streaming/typed response in a message bubble (non-blocking feel).
- Under the response, show “Candidate cards”.

## 13.2 Candidate cards (per candidate)
- Name
- Skills (top 5)
- Experience (years)
- Projects (top 2)
- Availability
- “Why matched” (from API)

## 13.3 Filters (optional panel)
- Mirrors API params: skill, min_experience, domain, availability.
- If set, prepend to the query (or call `/employees/search` for a list).

## 13.4 Empty/error states
- Empty: “Ask for skills + domain (e.g., ‘python aws ecommerce 3+ years’).”
- Error: Show a toast/banner; expose “Retry” button.

## 13.5 Accessibility
- Large readable fonts (>= 14px), clear focus states, keyboard submit (Enter), no tiny click targets.
