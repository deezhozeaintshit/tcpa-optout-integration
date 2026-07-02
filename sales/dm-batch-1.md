# LinkedIn DM Batch — Variant A (20 Templates)
# Every template is < 290 characters. LinkedIn truncates >300. Each carries a distinct
# pain_hook so they don't read as a copy-paste. Pick the template # that best matches
# a recent post / comment from the prospect — then fill {{name}}.

────────────────────────────────────────────────────────────────────────────────
TEMPLATE 1 — "manual opt-out reconciliation"
Subject: Quick question about your TCPA setup

{{name}} — saw your post about reconciling opt-outs across HubSpot + Twilio by hand.

I built a Python/FastAPI middleware that closes that loop in <2 seconds, with a
state-tracked retry queue + audit log compliance teams can read.

Same applies to SendGrid/Salesforce/GoHighLevel — HMAC-sha1 signature verified
on inbound webhooks (no spoofed STOP requests).

Haven't listed publicly — opened a 15-min demo window this week. Open to sharing
a Loom + pricing?

— {{your_name}}
────────────────────────────────────────────────────────────────────────────────
TEMPLATE 2 — "Twilio STOP not landing"
{{name}} — re: your question about Twilio STOP texts not making it into HubSpot.

Built a FastAPI middleware with HMAC-SHA1 webhook verification (so spoofed STOP
requests don't slip through), AI intent classification, and writes
hs_do_not_email / DoNotCall back to the CRM in under 2 seconds.

Failed syncs are logged to a separate audit table for your compliance team.

Selling the codebase (not SaaS). Single-team license $1,495, agency $4,500.

Live demo: {{DEMO_URL}}
Loom walkthrough: {{LOOM_URL}}

Want a screenshot of the dashboard + pricing PDF?

— {{your_name}}
────────────────────────────────────────────────────────────────────────────────
TEMPLATE 3 — "compliance gap on cold outreach lists"
{{name}} — saw your post on cold-outreach compliance gaps.

I had the same concern last quarter. Built a FastAPI middleware that:
• pulls STOP/UNSUBSCRIBE from Twilio SMS + verifies the signature
• AI-classifies intent (so "I'll subscribe later" doesn't get treated as a STOP)
• writes HasOptedOutOfEmail / DoNotCall / DNC back to the CRM in <2 sec
• keeps an audit log + retries indefinitely on API flakes

Commercial source license — single $1,495, agency $4,500.

Live demo: {{DEMO_URL}}
Loom walkthrough: {{LOOM_URL}}

— {{your_name}}
────────────────────────────────────────────────────────────────────────────────
TEMPLATE 4 — "one-to-one consent rules"
{{name}} — saw your comment on the new FCC one-to-one consent rules.

I built a Python service that auto-syncs contact-level opt-out status across
Twilio SMS, SendGrid Email, and your CRM (HubSpot / Salesforce / GHL) so the
consent revocation lands in <2 seconds — not "next quarter when someone
notices".

Encrypted at rest, audit trail per contact, HMAC-SHA1 verified on inbound webhooks.

Demo + pricing in 15 min. Open to a Loom walkthrough?

— {{your_name}}
────────────────────────────────────────────────────────────────────────────────
TEMPLATE 5 — "auditing opt-out handling for clients"
{{name}} — re: your post about auditing opt-out handling for your agency clients.

Built a FastAPI middleware that ingests "STOP" texts + emails, classifies
intent, and writes the revocation back to HubSpot/Salesforce/GHL with
a per-contact audit trail. Failed syncs log to a separate table your
compliance lawyers can read.

Codebase for license (not SaaS) — agency tier $4,500.

15-min demo this week. Worth a look?

— {{your_name}}
────────────────────────────────────────────────────────────────────────────────
TEMPLATE 6 — "managing TCPA across multiple clients"
{{name}} — I see you run multiple brands under one roof. TCPA exposure compounds
across them.

Built a Python service that writes opt-out status per contact, per brand, with
failover retries and a single audit log per identity. Multi-tenant friendly.

Worth 15 min to compare?

— {{your_name}}

(→ full links only if they ask; this short form avoids the spam filter)
────────────────────────────────────────────────────────────────────────────────
TEMPLATE 7 — "Twilio auto-reply dropping STOP"
{{name}} — quick question: are the STOP texts auto-responded by Twilio actually
making it into your CRM, or are they silently dropping in your Zendesk inbox?

Built a FastAPI service that bypasses that whole flow — direct HMAC-verified
webhook → intent classifier → CRM write in <2 seconds.

Demo link: {{DEMO_URL}}

— {{your_name}}
────────────────────────────────────────────────────────────────────────────────
TEMPLATE 8 — "Zapier webs + half the signals dropped"
{{name}} — saw your post on the Zapier websites losing half the opt-out signals.

I had the same issue until I wrote a FastAPI middleware that verifies the
inbound Twilio signature, pulls out the contact, and writes the DNC flag back
to HubSpot — directly, no Zapier in the loop.

Demo (works against a real mock HubSpot target):

Live demo: {{DEMO_URL}}

— {{your_name}}
────────────────────────────────────────────────────────────────────────────────
TEMPLATE 9 — "calling leads without verifying consent"
{{name}} — your question about a contact-list verification flow before calling
hits a real gap I've been working on.

If a caller hits "STOP" mid-call or your system misses the unsubscribe email,
you currently have no auto-revocation in your CRM.

Built a Python service that closes that gap with HMAC signature verification
+ AI intent classifier + CRM write in <2 seconds.

Worth a 15-min compare?

— {{your_name}}
────────────────────────────────────────────────────────────────────────────────
TEMPLATE 10 — "undisposed opt-outs in CRM"
{{name}} — saw your post on undisposed opt-outs in HubSpot.

I built a FastAPI service that ingests "STOP" / "UNSUBSCRIBE" from Twilio/SendGrid,
classifies intent (Gemini or regex fallback), writes HasOptedOutOfEmail /
DoNotCall to CRM, and queues retries indefinitely on API flake.

Single-team license $1,495.

Demo: {{DEMO_URL}}

— {{your_name}}
────────────────────────────────────────────────────────────────────────────────
TEMPLATE 11 — "HubSpot unsubscribes not propagating"
{{name}} — re: your post on HubSpot unsubscribes not propagating to SMS.

This is a TCPA nightmare. I built a Python service that's specifically the
spine for that — HMAC webhook verification (Twilio + SendGrid), AI intent
classifier, cross-channel write to HubSpot + Salesforce + GHL.

Open to a 15-min walkthrough?

— {{your_name}}
────────────────────────────────────────────────────────────────────────────────
TEMPLATE 12 — "Twilio + Salesforce bridge"
{{name}} — saw your post about needing a Twilio + Salesforce opt-out bridge.

Wrote exactly that. FastAPI + aiosqlite + Salesforce REST API +
queue + exponential backoff. ~3000 LOC, MIT-style license terms but
proprietary commercial license.

Single-team license $1,495, agency $4,500. Demo link:

{{DEMO_URL}}

— {{your_name}}
────────────────────────────────────────────────────────────────────────────────
TEMPLATE 13 — "compliance-checking outbound calls"
{{name}} — checking outbound call lists against the latest DNC list is
painful. The bigger pain is when a contact hits STOP mid-cycle.

I built a Python service that writes opt-out status in real time across
your CRMs. HubSpot + Salesforce + GHL supported out of the box.

Open to a 15-min demo?

— {{your_name}}
────────────────────────────────────────────────────────────────────────────────
TEMPLATE 14 — "consent revocation audit"
{{name}} — re: your comment on consent revocation audit gaps.

Built a FastAPI middleware that writes per-contact revocation with
a separate audit table (failed_syncs) your compliance team can
query directly. Retries 5x on API flake.

Commercial code-only license. Agency tier $4,500. Demo:

{{DEMO_URL}}

— {{your_name}}
────────────────────────────────────────────────────────────────────────────────
TEMPLATE 15 — "consent foundation for AI outreach"
{{name}} — saw your post on the AI outreach stack.

Consent foundation matters more than most folks admit. Built a Python
service that sticks between Twilio/SendGrid and your CRM, verifies
webhook signatures, classifies intent with AI, and writes revocations
back in real time.

15-min demo this week?

— {{your_name}}
────────────────────────────────────────────────────────────────────────────────
TEMPLATE 16 — "AI SDR + opt-out hygiene"
{{name}} — re: your post on AI SDR + opt-out hygiene.

I built the missing piece — a FastAPI service that catches STOP signals
across SMS + email, verifies the signature, logs the revocation to your
CRM and a parallel audit table. Your AI SDR stays compliant without
manual reconciliation.

Demo: {{DEMO_URL}}

— {{your_name}}
────────────────────────────────────────────────────────────────────────────────
TEMPLATE 17 — "dialer compliance hand-off"
{{name}} — saw you mentioned needing a dialer compliance hand-off for opt-outs.

I built a Python service that connects Twilio + SendGrid inbound opt-outs
to the dialer, in real time. State-tracked retries + audit log included.

Codebase license: commercial, not SaaS. Agency $4,500.

— {{your_name}}
────────────────────────────────────────────────────────────────────────────────
TEMPLATE 18 — "B2B cold email + suppression lists"
{{name}} — saw your post on B2B cold email + suppression list hygiene.

Built a Python service that catches unsubscribe events from SendGrid +
Twilio + your custom webhook, normalizes E.164 phone + email, and
writes the suppression back to HubSpot/Salesforce/GHL in <2 seconds.

Custom license terms. Open to a 15-min chat?

— {{your_name}}
────────────────────────────────────────────────────────────────────────────────
TEMPLATE 19 — "TCPA + state DNC combo"
{{name}} — re: your comment on TCPA + state-level DNC compliance complexity.

I built a Python service that handles federal TCPA + state DNC end to end.
Twilio SMS + SendGrid Email + HubSpot CRM all sync'd.

Code license: $1,495 single-team / $4,500 agency. Demo:

{{DEMO_URL}}

— {{your_name}}
────────────────────────────────────────────────────────────────────────────────
TEMPLATE 20 — "new client onboarding incl. compliance"
{{name}} — quick thought if you're onboarding a new agency client this quarter.

If their opt-out plumbing isn't clean, your first STOP request could turn
into a $50k TCPA fine.

I built a Python service that closes that gap in <30 minutes of install.
HMAC-verified webhooks, AI intent classifier, audit trail.

Open to a 15-min demo?

— {{your_name}}
────────────────────────────────────────────────────────────────────────────────

# Usage:
#   1. Open LinkedIn search results from the URL below.
#   2. For each prospect, glance at their latest post + headline.
#   3. Pick the template whose {{pain_hook}} matches what they recently talked about.
#   4. Hit "Connect" if not already connected, NOT a direct message unless
#      they accepted. After acceptance, click "Message" and paste.
#   5. Log each in sales/leads-tracker.csv.

# LinkedIn search (no Sales Navigator required):
# https://www.linkedin.com/search/results/people/?keywords=cold%20outreach%20agency%20founder&network=%5B%22F%22%2C%22S%22%2C%22O%22%5D

# Or for SMS marketing focus:
# https://www.linkedin.com/search/results/people/?keywords=SMS%20marketing%20agency%20founder&network=%5B%22F%22%2C%22S%22%2C%22O%22%5D
