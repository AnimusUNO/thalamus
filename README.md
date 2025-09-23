# Thalamus: Parallel Refinement and Flow Control for Real-Time Agentic Cognition

**Authors:** Mark “Rizzn” Hopkins — Principal Engineer — mark@rizzn.com, Animus · Athena Vernal — Research Lead — athena@rizzn.com, Animus · John Casaretto — Co‑Founder, BlackCert — john@blackcert.com

---

## Abstract
Thalamus is a middleware architecture for agentic AI systems that balances low-latency reflexive processing with parallel refinement of perceptual streams. Inspired by biological thalamic function, it enables raw sensory input to be routed immediately to reflex-level subsystems while preparing cleaned and annotated versions in parallel. The result is fast reaction without sacrificing structured context for deeper cognition. We describe the method, its lineage from accessibility-focused designs, its generalized applicability to multimodal stacks, and its implementation via the Cochlea schema.

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Repository Structure](#repository-structure)
3. [Documentation Index](docs/README.md) - Navigation guide for all documentation
4. [Introduction](#1-introduction)
5. [Related Work](#2-related-work-lineage-and-neuro-inspired-design)
6. [Method](#3-method)
7. [Implementation](#4-implementation)
8. [Data Structures](#5-data-structures-and-hygiene)
9. [Use Cases](#6-use-cases)
10. [Business Model](#7-business-model)
11. [Illustrations](#8-illustrations)
12. [Conclusion](#9-conclusion)

---

## Quick Start

To see Thalamus in action, run the interactive Forensiq demo:

```bash
cd examples/forensiq_demo
pip install textual rich
python main.py
```

The demo showcases the cognitive architecture described in this paper through a textual TUI interface, demonstrating:
- **Raw Input Processing**: Cochlea receiving sensory data
- **Parallel Refinement**: Thalamus processing raw input while preparing refined versions  
- **Reflex Processing**: Cerebellum's quick response capabilities
- **Deep Cognition**: Prime Agent's higher-order processing

For more details, see the [Forensiq Demo README](examples/forensiq_demo/README.md).

## Repository Structure

This repository contains the Thalamus whitepaper and reference implementations:

```
thalamus/
├── README.md                    # This whitepaper
├── examples/                    # Reference implementations
│   ├── forensiq_demo/          # Interactive TUI demo (main.py)
│   │   ├── main.py             # Forensiq cognitive UI demo
│   │   ├── requirements.txt    # Demo dependencies
│   │   └── README.md           # Demo documentation
│   ├── thalamus_app.py         # Data ingestion application
│   ├── transcript_refiner.py   # AI-powered transcript refinement
│   ├── database.py             # Database management
│   ├── openai_wrapper.py       # OpenAI API integration
│   ├── omi_webhook.py          # Webhook endpoint
│   ├── utils.py                # Utility functions
│   ├── init_db.py              # Database initialization
│   ├── check_db.py             # Database inspection
│   ├── audit_segment_usage.py  # Data integrity verification
│   ├── raw_data_log.json       # Sample test data
│   └── requirements.txt        # Dependencies
└── docs/                       # Additional documentation
    ├── DEMO_GUIDE.md           # Demo instructions
    ├── OMI_WEBHOOK_GUIDE.md    # Webhook integration guide
    └── CHANGELOG.md            # Version history
```

---

## 1. Introduction
Modern agentic AI systems require both immediacy and structure in their perceptual processing pipelines. Raw speech-to-text (STT) or video-derived transcripts are fast but chaotic; refined outputs are structured but slower. Thalamus was designed to bridge this gap, first for accessibility and cyborg applications, then generalized to any auditory or multimodal agentic stack. It acts as a cache-like layer, preparing meaning in parallel with reflex actions.

---

## 2. Related Work, Lineage, and Neuro-Inspired Design
The design of Thalamus is inspired by the human brain, where raw sensory input is processed at multiple speeds: e.g., fast “movement detected” signals vs. slower “that is a dog” interpretations. Technically, Thalamus draws lineage from the **Omi** project’s webhook architecture. Its data schema has been generalized and formalized as **Cochlea**, a standalone server producing structured JSON segments. Thalamus is also situated alongside other Animus middleware: **Cerebellum** (reflex processing, summarization, and escalation) and **Broca** (digital-to-digital communication middleware).

### 2.1 Neuro-Inspired Design
Biological thalamic pathways illustrate why the architecture matters: the brain routes raw, low-latency signals directly to reflex centers, while parallel cortical layers refine and contextualize sensory input. This ensures survival-level reactions occur without delay, but more structured interpretations are available when needed. Thalamus mirrors this by separating fast reflex delivery (to Cerebellum) from slower semantic refinement (Phases 1 and 2). The design thus builds computational “RAM and cache” layers into the system, allowing higher-order agents to scale without waiting for full semantic clarity.

### 2.2 Related Work
- **Omi (open-source STT webhook model):** inspiration for Cochlea’s event format and streaming behavior.
- **Letta (agent framework):** summarization, memory stratification, and sub-agent orchestration informing Cerebellum/Prime interactions.
- **LiveKit (real-time media):** representative transport for conversational audio routing into Cochlea.
- **JSON Schema (2020-12):** formal basis for the Cochlea compatibility contract.
- **Animus Middleware (Broca/Thalamus/Cerebellum):** prior internal notes on routing, flow-control, and escalation patterns.


---

## 3. Method
### 3.1 Phase 0: Raw Input
Raw perceptual segments are ingested via Cochlea JSON events and stored immediately as `RawSegment` objects. These are available to the Cerebellum for reflex-level processing.

### 3.2 Phase 1: Cleanup
Segments are grouped by speaker and time window, punctuation and filler tokens are cleaned, and finalized on either speaker change or idle boundary.

### 3.3 Phase 2: Light Semantics
Refined segments are lightly annotated with topics, tags, or intent markers. They are not immediately escalated but can be pulled on demand.

### 3.4 Reflex vs. Depth
- **Reflex:** Cerebellum processes raw input instantly for filtering, quick replies, and reflex arcs.
- **Escalation:** When the Cerebellum requires additional context, it explicitly pulls refined segments from Thalamus. These escalated segments flow up to the Prime Agent for higher-order synthesis and decision-making.

This separation ensures latency remains low while preserving structured, auditable data for deeper cognition.

![Thalamus system routing and storage tiers](docs/assets/thalamus-fig-1.png)

*Figure 1: System routing and storage tiers.* Raw input flows through Thalamus processing, then to Cerebellum for reflex handling, and finally to storage tiers for persistence and retrieval.

![Thalamus ingestion and refinement flow](docs/assets/thalamus-cerebellum-diagram.png)

*Figure 2: Thalamus ingestion and refinement flow. Raw sensory segments are stored immediately, queued, evaluated, and either escalated to Cerebellum for reflex processing or archived/tagged for later use.*

---

## 4. Flow Control
Thalamus embeds flow control mechanisms at two critical points: **ingestion** and **escalation**.

### 4.1 Ingestion Control
Incoming perceptual events (e.g., Cochlea JSON) are buffered in a lightweight queue before being written into the Thalamus database. This prevents bursts of raw segments from overwhelming storage or refinement workers. The methodology mirrors the same queuing principles used downstream: ordered intake, no overlap, and paced delivery into refinement loops.

### 4.2 Escalation Control
For outbound traffic toward the Cerebellum, Thalamus meters requests through a similar lightweight queue. This ensures the Cerebellum API is never given overlapping inference calls. Regular summarization and pruning are triggered at defined cadence using Letta’s built-in tools. Escalation events are prioritized within this queue so that context-rich requests reach the Prime Agent without delay.

### 4.3 Escalation Prioritization Algorithm (Concrete)
```text
structures:
  ingest_q          # FIFO for Cochlea→Thalamus events
  cerebellum_q      # PRIORITY queue for Thalamus→Cerebellum work

on_ingest(event):
  ingest_q.push(event)

ingest_worker():
  while ingest_q.not_empty():
    ev = ingest_q.pop()
    write_raw(ev.segments)                  # DB: raw_segments
    schedule_refine(ev.session_id)          # async Phase 1/2 jobs
    if triggers_reflex(ev):                 # wakeword, safety, interrupt
      cerebellum_q.push(PRIO_REFLEX, {kind: "raw", ev})

refine_worker():
  for batch in next_batches():
    refined = refine(batch)                 # group-by speaker/time, cleanup
    ridxs   = [seg._raw_index for seg in batch]
    write_refined(refined, source_segments=ridxs)
    if triggers_escalation(refined):        # confidence<τ, user-addressed agent, long-span, device heuristics
      cerebellum_q.push(PRIO_ESCALATE, {kind: "refined", refined, source_segments: ridxs})

cerebellum_worker():
  while cerebellum_q.not_empty():
    job = cerebellum_q.pop_highest_priority()
    block_overlaps_until_done()
    maybe_trigger_summarize()               # cadence/idle
    if job.kind == "raw":
      call_cerebellum(job.ev)               # reflex path
    else:                                   # refined escalation
      attach_provenance(job.refined, job.source_segments)
      send_to_prime(job.refined)            # escalation path
```
*Figure 3: Concrete escalation algorithm with ingestion/refinement producers and a prioritized Cerebellum queue. Guarantees: ordered intake, no overlapping inference calls, provenance preserved on escalation.*

### 4.4 What Users See in the Demo (Operational Semantics)
*See the [Forensiq Demo](examples/forensiq_demo/README.md) for the interactive implementation.*

- **Thalamus (right console pane):** background chatter scrolls continuously; any item highlighted as noteworthy renders with a "→ CEREBELLUM" marker. Those are reflex triggers.
- **Cerebellum (upper-left chat):** receives reflex items instantly (no typing effect). When it **escalates**, the outgoing message streams as if being typed (to convey deliberation).
- **Prime Agent (lower-left chat):** receives escalations **instantly** (no typing), then streams its own responses. Tool actions (block IP, write report) render immediately as bracketed tool lines.
- **Memory Core (center pane):** when Prime commits decisions, a new **memory block** card appears (title + summary). This is the visible artifact of escalation resolution.

---

## 5. Data Structures and Hygiene
### 5.1 Separation of Stores
- **Thalamus DB:** high-churn sensory buffers (`raw_segments`, `refined_segments`, `segment_usage`).
- **Queue DB:** a lightweight store for managing ingestion and escalation queues. This database ensures orderly flow control and avoids contention with the high-volume sensory tables.
- **Cerebellum Storage:** as a Letta-based sub-agent of the Prime Agent, the Cerebellum maintains its own storage system for conversation summaries and working state. This is distinct from both the Thalamus DB and the queue DB.

This separation mirrors biological perception vs. working memory and ensures that rapid sensory churn, orderly queue pacing, and longer-lived agent state remain isolated from one another.

### 5.2 Provenance Provenance
Refined segments maintain provenance via `segment_usage`, linking each refined record back to its raw sources. Escalated queries preserve this lineage, ensuring Prime Agent decisions are auditable to the raw perceptual level.

---

## 6. Interface Contract: Cochlea JSON
Thalamus standardizes on a minimal schema:

**Event:**
- `session_id: string`
- `log_timestamp: ISO-8601 string`
- `segments: Segment[]`

**Segment:**
- `text: string`
- `speaker: string`
- `speaker_id: int`
- `is_user: boolean (optional)`
- `person_id: string|int|null (optional)`
- `start: float`
- `end: float`

*Table 1: Cochlea JSON Schema (field list).*  

### 6.1 Formal JSON Schema (v0.1)
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "Cochlea Event v0.1",
  "type": "object",
  "additionalProperties": false,
  "required": ["session_id", "log_timestamp", "segments"],
  "properties": {
    "session_id": { "type": "string" },
    "log_timestamp": { "type": "string", "format": "date-time" },
    "segments": {
      "type": "array",
      "minItems": 1,
      "items": { "$ref": "#/definitions/Segment" }
    }
  },
  "definitions": {
    "Segment": {
      "type": "object",
      "additionalProperties": true,
      "required": ["text", "speaker", "speaker_id", "start", "end"],
      "properties": {
        "text": { "type": "string", "minLength": 1 },
        "speaker": { "type": "string" },
        "speaker_id": { "type": "integer" },
        "is_user": { "type": "boolean" },
        "person_id": { "type": ["integer", "string", "null"] },
        "start": { "type": "number", "minimum": 0 },
        "end": { "type": "number", "minimum": 0 }
      }
    }
  }
}
```
*Validation note:* `additionalProperties` is **true** on `Segment` to allow forward-compatible fields from different STT/video sources. Required fields remain strict for portability.

---

## 7. Applications
Thalamus was designed for accessibility and cyborg-style human-to-agent communication, but its methodology applies broadly across auditory, visual, and multimodal stacks. Below we detail key contexts.

### 7.1 Accessibility / Cyborg AI
Original use case; real-world human-to-agent conversation where low-latency reflexes matter but structured transcripts are required for context. Thalamus refines speech input and ensures that Prime Agent cognition remains structured while responses remain immediate.

### 7.2 Digital Audio Conversations
```
Cochlea → Thalamus → Broca → Prime Agent
```
- **Cochlea**: takes in audio (via LiveKit or other STT engines).
- **Thalamus**: cleans, refines, and structures raw transcripts.
- **Broca**: routes text events across Animus's communication channels.
- **Prime Agent**: consumes the refined stream as if it were chat, generating responses.
- **Voicebox**: on the return leg, converts agent replies back into speech.

In this mode, *everything* is transcribed and handed to the agent in real-time for full-duplex interaction.

### 7.3 Ear Devices (Omi-Style, Ambient Microphone)
```
Cochlea → Thalamus → Cerebellum → Prime Agent
```
- **Cochlea**: performs STT on audio.
- **Thalamus**: filters and refines noisy, ambient inputs.
- **Cerebellum**: applies device-specific heuristics: wake-word detection, noise gating, proximity rules.
- **Prime Agent**: receives only meaningful, device-relevant text events.

In this mode, the Cerebellum provides selective hearing: gating what reaches the Prime Agent so it is not overwhelmed by background chatter.

### 7.4 Digital Communication Channels
When applied to digital-to-digital communication, Thalamus refines and regulates text-based message streams before Broca routes them across systems. This allows the same methodology—parallel refinement and pacing—to be reused in machine-to-machine contexts.

### 7.5 General Perceptual Stacks
Audio, video, or multimodal pipelines benefit from the same architecture: raw perception flows immediately for reflex processing, while parallel refinement prepares structured context for escalation to higher-order agents.

### 7.6 Why the Distinction Matters
- **Conversations**: require full real-time transcription with minimal filtering, ensuring the agent perceives everything.
- **Ambient device mode**: requires selective hearing and heuristics to avoid overwhelming the agent with irrelevant input.

⚡ **BLUF**: Cerebellum adds device-contextual filtering and heuristics, while Broca remains the general-purpose router. Thalamus enables both by providing structured, auditable input streams that can flow into either path.

---

## 7.7 Patent-Pending Cybersecurity Application
Beyond conversational and perceptual contexts, the Thalamus–Cerebellum relationship extends naturally to domains where complex systems produce large volumes of unstructured or semi-structured data. One active line of work—currently in a patent-pending state (provisional application filed by Mark Hopkins and John Casaretto)—applies this architecture to **adaptive cybersecurity enforcement and retrospective forensic analysis**.

### 7.7.1 Motivation
Traditional EDR and forensic tools operate in silos: real-time detection is brittle and retrospective analysis is slow and incomplete. Modern threat surfaces require both low-latency response and structured long-term memory.

### 7.7.2 Thalamus–Cerebellum Analogy
- **Thalamus (Data Refinement):** Streams raw system and user telemetry, cleaning, tagging, and structuring events in real time.
- **Cerebellum (Reflex & Escalation):** Applies inline policy enforcement, reflexive blocking or isolation, and schedules summarization of events to prevent overload.
- **Prime Agent:** Escalated, refined context flows upward for synthesis, anomaly interpretation, and forensic reconstruction.

### 7.7.3 Key Features
- Real-time monitoring and behavioral deviation response.
- Structured, tamper-evident forensic records suitable for replay.
- Dual-mode memory: ephemeral for detection, archival for compliance-grade audits.
- Middleware governance layer for task coordination, summarization, and pruning.
- Optional hardware-persistence module for cryptographic anchoring and attestation.

### 7.7.4 Applications
- Intelligent threat mitigation and inline enforcement.
- Zero-trust conditional access.
- Forensic replay of system states and user behaviors.
- Insider threat detection and long-term behavioral drift analysis.
- Secure audit support for compliance-heavy environments.

This illustrates the generality of the Thalamus–Cerebellum relationship: any system facing high-volume, noisy data streams can adopt this parallel refinement and escalation model to achieve both immediacy and structured depth.

## 7.8 Credential Security Application ("Sentry")
Another active collaboration between Mark Hopkins and John Casaretto extends the Thalamus–Cerebellum model into **identity and credential security**. The project, currently under development, is provisionally titled *Sentry*.

### 7.8.1 Core Idea
Sentry provides a lightweight, AI-powered detection layer focused specifically on credential theft and token misuse. Rather than replacing full SIEM/SOC platforms, it offers targeted protection against one of the most common breach vectors—stolen credentials.

### 7.8.2 How It Works
- **Easy Integration:** Connects directly to cloud identity platforms (e.g., Entra ID, Okta) via API.
- **AI-Enhanced Detection:** Feeds real-time login/session telemetry into AI models for anomaly detection.
- **Autonomous Response:** Locks down access or triggers forensic capture upon detection of suspicious behavior.
- **Cloud-Native Delivery:** Offered as a SaaS subscription, deployable within hours.

### 7.8.3 Integration with Thalamus–Cerebellum Model
- **Thalamus (Telemetry Refinement):** Ingests raw credential/session events, cleans and structures them, applies anomaly tags.
- **Cerebellum (Reflex & Escalation):** Executes immediate responses (block, isolate) while escalating enriched anomaly context to the Prime Agent.
- **Prime Agent:** Interprets escalated anomalies, correlates across tenants, and generates higher-order security insights.

### 7.8.4 Market and Opportunity
- Over 80% of breaches involve compromised credentials.
- SMBs lack budget for full SOC coverage, and enterprises face alert fatigue.
- Existing tools are expensive or incomplete; token/session hijacking remains underserved.
- Market projected at $20B+ by 2027, with investor appetite demonstrated by peers raising Series A–C rounds.

### 7.8.5 Positioning
- **SMBs:** Enterprise-grade identity security without SOC overhead.
- **Enterprises:** Targeted bolt-on to cover credential gaps.
- **Partners/Resellers:** Fast-deploy, ROI-driven security service.

### 7.8.6 Demo Observables (TUI Simulation)
*See the [Forensiq Demo](examples/forensiq_demo/README.md) for the interactive implementation.*

- **Ingress:** right console logs show AUTH/NET/SEC events; those marked as WARN/ERROR/CRITICAL and highlighted are forwarded to Cerebellum instantly (reflex).
- **Reflex decisions:** appear in Cerebellum pane as instant "Cerebellum:" messages (e.g., dismissing false positives like scheduled backups or log rotation).
- **Escalations:** render twice—streaming in Cerebellum as the outgoing message, and instantly in Prime as the incoming item—followed by a streamed **Prime** response.
- **Tooling:** Prime tool actions (e.g., block IP, create report) appear as immediate bracketed tool lines; they often precede a new **Memory Core** block with the incident summary.
- **Cadence:** the background chatter continues throughout to emphasize that reflex and escalation do not block intake.

Sentry illustrates another vertical where Thalamus’ refinement + Cerebellum’s escalation together enable fast, structured, auditable defense against high-volume, high-noise threats—in this case, credential misuse.

---

## 8. Illustrations
### 8.1 Example Code (Ingress)
```py
@app.route("/omi", methods=["POST"])
def omi_webhook():
    data = request.get_json(force=True)
    print("Cerebellum Input [UNRESTRICTED]:", data)
    return "OK", 200
```

### 8.2 Example Transformation
| From Cochlea (raw) | Thalamus (refined) | Notes |
|---|---|---|
| `"uh testing testing"` (SPEAKER_0, 0.0–2.74s) | `"Testing. Testing."` (SPEAKER_0, 0.0–2.74s) | filler dropped, punctuation repaired |

*Figure 3: Example raw vs. refined transcript segment.*

### 8.3 Pseudocode for Flow Control and Escalation
```text
on_raw_segment(event):
  enqueue(event.segment)

cerebellum_worker():
  while queue.not_empty():
    seg = dequeue_one()
    maybe_trigger_summarize()
    if escalation_required(seg):
        refined = get_refined(seg.session_id)
        send_to_prime(refined)
    else:
        call_cerebellum(seg)
```
*Figure 2: Queue-based pacing with explicit escalation to Prime Agent.*

### 8.4 Full Before/After with Provenance (from `raw_data_log.json`)
**Raw (first three records of session):**

| Raw Idx | Speaker | Time (s) | Text | Timestamp |
|---:|---|---|---|---|
| 0 | SPEAKER_0 (0) | 0.00–2.74 | Testing. Testing. Or do we have live connection? | 2025-03-26T22:48:11.021743Z |
| 1 | SPEAKER_0 (0) | 4.22–5.84 | Hello. Hello. Testing. Testing. | 2025-03-26T22:48:11.917772Z |
| 2 | SPEAKER_0 (0) | 8.51–9.01 | Okay. | 2025-03-26T22:48:14.865628Z |

**Refined (constructed by Thalamus Phase 1/2 grouping):**
```json
{
  "session_id": "jTbLZFVyJjduPPvf0KQDqqPYhyU2",
  "speaker": "SPEAKER_0",
  "speaker_id": 0,
  "start": 0.0,
  "end": 9.01,
  "text": "Testing. Testing. Or do we have live connection? Hello. Hello. Testing. Testing. Okay.",
  "source_segments": [0, 1, 2]
}
```
*Provenance:* `source_segments` maps the refined record to the raw indices listed above; in the database, these correspond to ingestion-time primary keys for auditable backtracking.

### 8.5 Demo Timeline (Security Simulation)
*See the [Forensiq Demo](examples/forensiq_demo/README.md) for the interactive implementation.*
1. **Unusual file access** (HR after-hours) → reflex note in Cerebellum → **escalation** to Prime → Prime streams analysis → tool writes **SECURITY INCIDENT** memory block.
2. **False positives** (network spike, log rotation, mobile sync) → Cerebellum dismisses reflexively; no escalation, no memory blocks.
3. **Brute force attack** → Cerebellum blocks IP reflexively → **escalation** declares coordinated attack → Prime cross-references intel, blocks globally, writes **BRUTE FORCE ATTEMPT** memory block.
4. **Privilege escalation attempt** → urgent reflex notice → **critical escalation** → Prime initiates lockdown & forensics, notifies authorities, writes **CRITICAL ALERT** memory block.

**Figure 4 (placeholder):** *Three-pane TUI screenshot with arrows overlaid: highlight→Cerebellum, Cerebellum→Prime (incoming), Prime→Tool/Memory.*

### 8.3 Pseudocode for Flow Control and Escalation
```text
on_raw_segment(event):
  enqueue(event.segment)

cerebellum_worker():
  while queue.not_empty():
    seg = dequeue_one()
    maybe_trigger_summarize()
    if escalation_required(seg):
        refined = get_refined(seg.session_id)
        send_to_prime(refined)
    else:
        call_cerebellum(seg)
```
*Figure 2: Queue-based pacing with explicit escalation to Prime Agent.*

### 8.4 Full Before/After with Provenance (from `raw_data_log.json`)
**Raw (first three records of session):**

| Raw Idx | Speaker | Time (s) | Text | Timestamp |
|---:|---|---|---|---|
| 0 | SPEAKER_0 (0) | 0.00–2.74 | Testing. Testing. Or do we have live connection? | 2025-03-26T22:48:11.021743Z |
| 1 | SPEAKER_0 (0) | 4.22–5.84 | Hello. Hello. Testing. Testing. | 2025-03-26T22:48:11.917772Z |
| 2 | SPEAKER_0 (0) | 8.51–9.01 | Okay. | 2025-03-26T22:48:14.865628Z |

**Refined (constructed by Thalamus Phase 1/2 grouping):**
```json
{
  "session_id": "jTbLZFVyJjduPPvf0KQDqqPYhyU2",
  "speaker": "SPEAKER_0",
  "speaker_id": 0,
  "start": 0.0,
  "end": 9.01,
  "text": "Testing. Testing. Or do we have live connection? Hello. Hello. Testing. Testing. Okay.",
  "source_segments": [0, 1, 2]
}
```
*Provenance:* `source_segments` maps the refined record to the raw indices listed above; in the database, these correspond to ingestion-time primary keys for auditable backtracking.

---|---|---|
| `"uh testing testing"` (SPEAKER_0, 0.0–2.74s) | `"Testing. Testing."` (SPEAKER_0, 0.0–2.74s) | filler dropped, punctuation repaired |

*Figure 1: Example raw vs. refined transcript segment.*

### 8.3 Pseudocode for Flow Control and Escalation
```text
on_raw_segment(event):
  enqueue(event.segment)

cerebellum_worker():
  while queue.not_empty():
    seg = dequeue_one()
    maybe_trigger_summarize()
    if escalation_required(seg):
        refined = get_refined(seg.session_id)
        send_to_prime(refined)
    else:
        call_cerebellum(seg)
```

*Figure 2: Queue-based pacing with explicit escalation to Prime Agent.*

---

## 9. Discussion
Thalamus provides reflex-speed responsiveness while preparing structured, auditable context for deeper cognition. Its design is model-agnostic, schema-driven, and applicable across real-world and digital communication contexts. Explicit escalation pathways ensure the Prime Agent only consumes meaningful, context-rich data when required. Limitations include untested concurrency scaling and integration overhead, though architectural safeguards mitigate these risks.

---

## 10. Conclusion
Thalamus demonstrates how parallel refinement, flow control, and explicit escalation can be combined to scale cognition. By grounding in a shared schema (Cochlea) and separating sensory buffers from conversation state, it ensures agentic systems remain both fast and structured.

---

## References

[1] Omi Project. *Open Source Streaming STT & Webhook Patterns.* Available at: [https://github.com/openai/omi](https://github.com/openai/omi)

[2] Letta Framework. *Agentic AI Middleware, Memory & Summarization.* Available at: [https://docs.letta.com](https://docs.letta.com)

[3] Sanctum Architecture Notes. *Broca, Cerebellum, Thalamus Design.* Internal documentation.

[4] LiveKit. *Real-Time Media Transport for Conversational AI.* Available at: [https://livekit.io](https://livekit.io)

[5] JSON Schema (2020-12). *A Vocabulary for Structural Validation of JSON.* Available at: [https://json-schema.org/specification-links.html#2020-12](https://json-schema.org/specification-links.html#2020-12)

[6] Hopkins, M. A., & Casaretto, J. (2025). *System and Method for Adaptive Agent-Based Cybersecurity Enforcement and Retrospective Forensic Analysis.* Provisional Patent Application (unpublished).

[7] Sanctum Thalamus Notes. *Parallel Refinement, Flow Control, and Escalation.* Internal documentation.

[8] Sanctum Broca Notes. *Digital-to-Digital Routing and Message Governance.* Internal documentation.

[9] Cochlea v0.1 Schema. *Compatibility Contract for Perception→Thalamus Events.* Available at: [https://github.com/sanctumos/cochlea](https://github.com/sanctumos/cochlea)

---

## License

**Code**: All software code in this repository is licensed under the [GNU Affero General Public License v3.0](LICENSE) (AGPL-3.0).

**Documentation**: All documentation, whitepapers, and non-code content is licensed under [Creative Commons Attribution-ShareAlike 4.0 International](https://creativecommons.org/licenses/by-sa/4.0/) (CC BY-SA 4.0).

### Summary
- **AGPL-3.0** ensures that any derivative works or network services using this code must also be open source
- **CC BY-SA 4.0** allows sharing and adaptation of the documentation with proper attribution and share-alike terms

For full license terms, see the [LICENSE](LICENSE) file for code licensing and the [LICENSE-DOCS](LICENSE-DOCS) file for documentation licensing.

