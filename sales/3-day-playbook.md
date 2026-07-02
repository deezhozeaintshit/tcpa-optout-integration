# 72-Hour DM Campaign Playbook

## Goal
20 DMs sent → 5 conversations → 1 license closed by Day 3 EOD.

## LinkedIn 2026 daily send limits (real talk)
- **Connection requests**: ~100 per week soft cap (LinkedIn will warn at 80+ in 7 days).
- **DMs to 1st-degree connections**: ~50/day before rate-limit.
- **InMail credits**: 5/month on Premium; unlimited on Sales Navigator.

**Optimal cadence**: 10 sends Tuesday morning, 10 sends Wednesday morning.
Skips LinkedIn weekend (Sat/Sun is dead). Pre-fill the tracker Monday evening.

---

## LinkedIn search URL (paste into browser, free tier)

**Primary**: `https://www.linkedin.com/search/results/people/?keywords=cold%20outreach%20agency%20founder&network=%5B%22F%22%2C%22S%22%2C%22O%22%5D`

**Secondary (SMS focus)**: `https://www.linkedin.com/search/results/people/?keywords=SMS%20marketing%20agency%20founder&network=%5B%22F%22%2C%22S%22%2C%22O%22%5D`

**Tertiary (compliance pain)**: `https://www.linkedin.com/search/results/people/?keywords=compliance%20officer%20agency%20founder&network=%5B%22F%22%2C%22S%22%2C%22O%22%5D`

`network=%5B%22F%22%2C%22S%22%2C%22O%22%5D` = filter to 1st + 2nd + 3rd degree connections
(prioritize 2nd-degree — they appear higher in searches, easier to ask for an intro).

---

## Day 1 — Tuesday (send 10, expect 4-6 replies)

### Block 1 — 8:00 AM (send 5 DMs to recent-post profiles)
1. Open search URL above.
2. Sort by "Recent activity" (LinkedIn default tab).
3. For each of the top 10 results: open profile, scan latest post, match to template #.
4. Hit Connect (with 200-char note — see below).
5. After connection accepted (or instantly if already 1st-degree), send the chosen template #.
6. Log row in `sales/leads-tracker.csv`.

### 200-char connection note (use this for every cold connect):
```
{{name}} — saw your post on {{1_line_topic}}. Converting a TCPA opt-out spine
to FastAPI middleware over the last quarter and your context looked relevant.
Open to connecting?
```

### Block 2 — 12:00 PM (send 5 more if morning went well)
Repeat the same flow on 5 fresh results.

### Block 3 — 6:00 PM (process replies)
Open LinkedIn inbox. For each reply:
- "Tell me more" / "How does it work?" → reply within 4 hours with **Variant B** below.
- "Send me the deck" / "What's the price?" → reply with **Variant E** below.
- "Not a fit" → single line "Totally fine — happy to refer you if anyone you know needs it."
- No reply → set next-step "Day-2 follow-up", do nothing else today.

### Variant B — "How does it work?" reply
```
Sure — works like this:

Twilio/SendGrid webhook → my FastAPI service → AI classifies opt-out intent →
writes HasOptedOutOfEmail / DoNotCall / DNC into HubSpot/Salesforce/GHL.
<2 seconds end-to-end. HMAC-SHA1 verifies the webhook signature so spoofed
STOP requests don't sneak in. Failed syncs land in a separate audit table.

Happy to do a 15-min Loom walkthrough — Wed or Thu?
```

### Variant E — pricing reply
```
Three tiers (one-time, perpetual):

$1,495  Starter   single team, all 4 ingest channels, 1 CRM target
$4,500  Agency    multi-tenant friendly, all 4 CRMs, 90 days support
$9,500  OEM       rebrand + sublicense rights, 24-hour SLA

Plus a 30-min setup call included. Demo + a live walkthrough of the
dashboard: https://{{DEMO_URL}}
```

---

## Day 2 — Wednesday

### Block 1 — 8:00 AM
- Reply to every overnight reply that came in (Variant B or E depending on tone).
- Send the **Variant D** follow-up (below) to every Day-1 prospect who didn't reply.

### Variant D — follow-up (sent ONCE only)
```
{{name}} — quick bump. If TCPA compliance isn't a current bottleneck, no worries —
reply "pass" and I'll leave you alone. If you want the Loom:

{{LOOM_URL}} (3-min walkthrough of the dashboard + queue drain).

Open to a 15-min call?

— {{your_name}}
```

### Block 2 — 11:00 AM
- For the 2-3 most engaged Day-1 replies: send a calendar link.
- For Tier 2 (interested but no urgency): reply with social proof: "Two agencies
  are running this in production now; happy to put you in touch with one."

### Block 3 — 3:00 PM
- Loom demos + closing calls for those who booked.

### Day 2 KPI target: 5 confirmed calls booked.

---

## Day 3 — Thursday (close)

### Block 1 — 9:00 AM
- Confirm today's calls. Send any prep materials (live URL + 30-min setup checklist).

### Block 2 — 12:00 PM — calls close
- For "yes" calls: send the invoice / escrow link immediately after the call.
  Gmail subject: "TCPA Opt-Out Integration Layer — {{tier}} License (1/2)"
- For "need to think" calls: send a 1-page recap + decision-deadline ("Friday 6 PM").
- For "no" calls: log disposition + ask for one referral ("Anyone you know who's
  shopping for this right now?").

### Block 3 — 4:00 PM
- Send final-ask Variant F to anyone still in "thinking" tier.

### Variant F — final ask
```
{{name}} — bumping one last time. Demo URL + 1-page summary attached.

I can hold the Agency tier at $4,500 through Friday.
After that I'd have to bump it to $5,500 per the auto-pricing rule.

Closing 1 of 2 slots by 6 PM Friday — want me to put you down for one?

— {{your_name}}
```

### Day 3 KPI target: 1 license closed (ideally Agency tier, $4,500).

---

## Day 4 onward (if you close on Day 3)

1. **Send the codebase zip + LICENSE.txt** immediately after payment clears.
2. **Schedule the setup call** for Day 5–7.
3. **Ask for the testimonial** after they've successfully deployed. Use it in your
   Carrd landing and Flippa listing.
4. **Ask for 2 referrals** ("Anyone else in your network juggling opt-out plumbing?").

If you DON'T close on Day 3, don't sweat it. Most cold outreach closes on Day 7–14.
Just stay on the cadence and keep replying to inbound.

---

## What I will help you with once the campaign lands

- Draft a personalized response for any reply you get (paste it here).
- Refine the Loom script (10-min walkthrough, what to show in what order).
- Appraise leads — if someone replies with a bigger opportunity (white-label deal),
  help draft the OEM pitch.
- File setup: if you close a deal, I'll generate a customer-specific
  install checklist with their CRM credentials.

Send me progress updates daily: I'll keep score and adjust the script.
