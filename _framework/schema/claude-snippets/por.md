## POR discipline

When `por` is enabled, every area (and commons) has a `POR.md` capturing the current plan and execution state. POR sits alongside `brief.md` and `pulse.md`:

- **brief.md** — why this area exists. Changes rarely.
- **POR.md** — current plan, active workstreams, upcoming phases, dependencies, status/risks. Changes when phases shift, workstreams are added, or replans happen.
- **pulse.md** — what's hot this week. Changes constantly.

POR is loaded in every role's preload list. Update the relevant POR(s) when something materially changes — new spec, phase shift, completed workstream, replan with structural impact. `/wrap-up` prompts you to confirm POR updates when relevant events happened during the session.

Commons POR is updated by the `coordinator` role. Area PORs are updated by area roles. Sub-area POR may be a stub if the parent POR adequately covers it; mark this explicitly in the sub-area POR.

When the coordinator wants to influence an area's POR, the coordinator files an INBOX entry suggesting the change — area roles own area POR writes.
