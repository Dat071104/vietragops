# Implementation Log

<!-- newest first -->

## 2026-08-28 — Gate 07 V4 audit remediation and fresh headline run

### Goal

Retract the unsupported v3 mechanism claim, freeze a new measurement protocol,
recollect the graded benchmark, and close the audit findings without mutating
v3 raw artifacts or the protected overlay.

### Files changed

- `research/gate07/dataset/`: isolated V4 candidate-order permutation variant.
- `research/gate07/protocol/`: V4 prompt contract, freeze helpers, and ledger.
- `research/gate07/baselines/`: V4 parser, controls, offline outputs, and CUDA
  runtime support.
- `research/gate07/metrics/`: abstention-decoupled scoring, Wilson intervals,
  explicit degeneracy, supplied-value execution, applicability, and report.
- `gates/results/GATE_07_RESULT.md`, V4 tests, and this implementation log.
- `_agent_ops/DECISION_LOG.md` could not be changed because the user-protected
  overlay rule remained enforced.

### Phase evidence

- Step 0 reproduction: v3 direct 120b `argument_split` had 12/13 abstentions;
  all 198 answerable cases had the correct tool at index 0; constant-vector
  bootstrap CIs were zero-width.
- Implementation commit: `6130584`; CUDA runtime fix: `ecd391d`.
- CUDA verification: `torch 2.11.0+cu128`, `cuda_available=True`, one RTX 3050
  Ti device; V4 offline protocol records CUDA, FP16, batch size 8.
- Final protocol freeze: `GATE_07_PROTOCOL_V4.json`, freeze commit `206b18b`,
  ledger commit `dda8f32`; preflight returned `status=passed` at HEAD `dda8f32`.
- Offline V4: lexical, controls, BGE embedding, and cross-encoder each ran on
  180 graded tasks; embedding and cross-encoder used the pinned CUDA runtime.
- Live V4: 1,800 unique rows; 1,016 success, 60 parse failures, 180 provider
  errors, 544 rate-limited outcomes; zero held-out rows.
- Report: `GATE_07_METRICS_V4.json` SHA-256
  `cda1fcc184f39c114a112a0369556ccfd251942029ee5b232529ca53d992ba5f`; an
  independent regeneration produced the identical hash.
- Full suite command:
  `.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider -q --basetemp D:\GRADUATION_THESIS\gate07_v4_fulltest_temp2`
  returned **489 passed, 2 warnings, 0 failed**.

### Decision and remaining risk

V4 re-earns only a narrow `argument_split` GO: observed strongest applicable
forced-selection Arg F1 is 0.500, best-case imputation is 0.733, and the
forced carrier beats positional/random Tool@1 controls. The high typed
missingness and two no-success 20b arms remain explicit limitations; no claim
is made that a model cannot split arguments.

## 2026-06-02 15:01 - [unknown_phase/bugfix] Isolate Local Agent provider to Ollama

### Goal
- not specified

### Files changed
- none

### Bug or issue fixed
- Symptom: Local Agent tab mistakenly used Groq when LLM_PROVIDER=groq was set, breaking the local tool calling demo.
- Root cause: routes_agent.py used the global get_provider_router() which inherits the environment's LLM_PROVIDER, instead of strictly enforcing Ollama.
- Fix: Added get_agent_provider_router() and get_agent_answer_generator() in config.py hardcoded to 'ollama'. Updated routes_agent.py to use these specific instances.
- Why this fix is safe: not specified

### Commands run
```bash
not run
```

### Verification
- not verified

### Decisions
- none

### Remaining risks / next step
- none



## 2026-06-02 14:51 - [unknown_phase/bugfix] Enable python-dotenv for API startup

### Goal
- not specified

### Files changed
- none

### Bug or issue fixed
- Symptom: Adding GROQ_API_KEY to .env does not take effect when running uvicorn directly.
- Root cause: The app/main.py script did not load the .env file explicitly, causing local environment variables to not be registered on Windows.
- Fix: Imported and called load_dotenv() in app/main.py.
- Why this fix is safe: not specified

### Commands run
```bash
not run
```

### Verification
- not verified

### Decisions
- none

### Remaining risks / next step
- none



## 2026-06-02 14:39 - [unknown_phase/bugfix] Fix Streamlit API timeout for local agent

### Goal
- not specified

### Files changed
- none

### Bug or issue fixed
- Symptom: Web UI Local Agent tab hangs or fails to generate appropriate answer
- Root cause: The local Ollama generation for agent tasks takes ~60s, but frontend requests.post had a hardcoded 30s timeout, causing it to fail and trigger a duplicate fallback.
- Fix: Increased timeout in frontend/streamlit_app.py api_post to 120 seconds.
- Why this fix is safe: not specified

### Commands run
```bash
not run
```

### Verification
- not verified

### Decisions
- none

### Remaining risks / next step
- none


