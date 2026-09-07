# Gate 09R-V Result — Verification Gap Closure and Web Availability Triage

Status: **COMPLETE — CAPACITY classification; read-only observation**

Date: 2026-09-02

## Decision

Gate 09R-V closes the authorized observation gaps and stops here. The public
web static-module failure is classified as **CAPACITY**. The current HTTP
client loaded the root and every root-referenced JavaScript/CSS asset
successfully, and a fresh single-tab Codex In-app Browser load rendered the
Question widget. However, the last-24-hour Cloud Run logs contain 31 static
asset 429 responses across 26 paths on the active web revision while the
service is configured with minScale=0, maxScale=2, and
containerConcurrency=1. This is an intermittent capacity observation, not a
permanent SERVICE_DEFECT finding.

The target budget configuration was observed and matches the frozen control.
Current spend was not observable from the Budgets API. The identity-token
failure was reproduced and has the expected user-account root cause. No source,
deployment, IAM, budget, API, secret, provider, Firecrawl, ACL, or other
GCP mutation occurred. No question was submitted, no second product tab was
opened, and no push occurred.

Gate 09R remains **PASS**. Gate 08 remains **NEGATIVE** and unadopted. Gate 10
remains unauthorized.

## V0 — Entry gate and freeze

Working directory:

~~~text
D:\Project cua Dat\VietRAGOps\ROOT\VietRagOps
~~~

| Check | Observation |
|---|---|
| git rev-parse HEAD | 55bb73ab4ff7553988c9b9d9aa14b5a95d6052f1 |
| SHA-256 GATE_09RM_PROTOCOL.json | 8212F0AC4C0895D1D281DF30B46D51B378C0DBF401B5A691455157E3498D4685 |
| SHA-256 GATE_09R_PROTOCOL.json | F4C78F2E392D1BA55E030788E9255EB82944756DDB589316EC140008444C9E23 |
| Pre-freeze git status --short | Exactly 30 paths |
| Pre-freeze index | Empty |
| Default git ls-remote origin main | Failed with Schannel SEC_E_NO_CREDENTIALS (0x8009030e) |
| Bounded retry | git -c http.sslBackend=openssl ls-remote origin main returned 3ceba474fc0c80fe88b44a2c4157b60ce37291be refs/heads/main |
| New protocol | gates/baselines/GATE_09RV_PROTOCOL.json, valid JSON |
| SHA-256 GATE_09RV_PROTOCOL.json | D9A4160201A7A47DD6D2193783CB1C01FD082290453E4A6B4DED9A9CB29FE114 |

The 30-path overlay was preserved and not staged. The post-freeze status count
is 31 because the new protocol is a separate untracked gate artifact; the
pre-existing overlay remains untouched except for the explicitly authorized
RISK-0024 record.

## V1 — Public web availability triage

### V1.a Cold-path HTTP root GETs

Windows curl.exe was first run exactly as requested. Its Schannel backend
returned 000 and SEC_E_NO_CREDENTIALS, so the three valid HTTP observations
used the repository interpreter's Python 3.13 OpenSSL client as a bounded
transport fallback. The curl failure is a host transport observation, not a
Cloud Run status.

| Root GET | Observed at (Asia/Bangkok) | Client | HTTP status | Time | Content type | Bytes |
|---|---|---|---:|---:|---|---:|
| 1 | 2026-09-02T18:32:37.617191+07:00 | Python urllib/OpenSSL | 200 | 7.792729 s | text/html; charset=utf-8 | 11,141 |
| 2 | 2026-09-02T18:39:24.061186+07:00 | Python urllib/OpenSSL | 200 | 0.271133 s | text/html; charset=utf-8 | 11,141 |
| 3 | 2026-09-02T18:41:12.421965+07:00 | Python urllib/OpenSSL | 200 | 0.352992 s | text/html; charset=utf-8 | 11,141 |

The gaps were approximately 406.444 s and 108.361 s. The first latency is
consistent with a cold start, but the instance state was not directly exposed;
no cold-fail/warm-pass split occurred.

### V1.b Chunk enumeration

The root HTML fetched at 2026-09-02T18:34:18.564621+07:00 was 200,
text/html; charset=utf-8, and 11,141 bytes. It referenced 112 unique
/static/js/*.js or /static/css/*.css assets. Each was requested individually.
The complete receipt follows.

| # | Path | Status | Content type | Bytes |
|---:|---|---:|---|---:|
| 1 | /static/js/index.dZusM_HY.js | 200 | application/javascript | 451569 |
| 2 | /static/js/rolldown-runtime.C0FnF6B9.js | 200 | application/javascript | 1291 |
| 3 | /static/js/emotion-is-prop-valid.esm.CuYlOKOk.js | 200 | application/javascript | 10871 |
| 4 | /static/js/emotion-styled.browser.esm.BYv_Qzcq.js | 200 | application/javascript | 21904 |
| 5 | /static/js/loglevel.xXLtmX_e.js | 200 | application/javascript | 3257 |
| 6 | /static/js/react-dom.BzV73oHg.js | 200 | application/javascript | 132699 |
| 7 | /static/js/emotion-react.browser.esm.CnqdHrzD.js | 200 | application/javascript | 1451 |
| 8 | /static/js/protobuf.Ckf-kxfD.js | 200 | application/javascript | 786335 |
| 9 | /static/js/types.cZoyy9Y-.js | 200 | application/javascript | 75 |
| 10 | /static/js/isSymbol.CmW3dkoN.js | 200 | application/javascript | 750 |
| 11 | /static/js/isArrayLike.Crw2F5li.js | 200 | application/javascript | 668 |
| 12 | /static/js/toString.tRXNBxtF.js | 200 | application/javascript | 419 |
| 13 | /static/js/_isIterateeCall.BUStsXAd.js | 200 | application/javascript | 854 |
| 14 | /static/js/isArrayLikeObject.B3Zf3PTL.js | 200 | application/javascript | 9715 |
| 15 | /static/js/_baseClone.Bcnb-YL-.js | 200 | application/javascript | 4965 |
| 16 | /static/js/merge.CV9itYNj.js | 200 | application/javascript | 1820 |
| 17 | /static/js/getColors.DtAxY2Hd.js | 200 | application/javascript | 15857 |
| 18 | /static/js/utils.Vs712G4Z.js | 200 | application/javascript | 45944 |
| 19 | /static/js/uri.UNMuXGg5.js | 200 | application/javascript | 104 |
| 20 | /static/js/_baseFlatten.IOj0lc7G.js | 200 | application/javascript | 386 |
| 21 | /static/js/last.DfjdtCRp.js | 200 | application/javascript | 284 |
| 22 | /static/js/UriUtil.FYzIdBsL.js | 200 | application/javascript | 19051 |
| 23 | /static/js/useCrossOriginAttribute.K-ObP1Bx.js | 200 | application/javascript | 267 |
| 24 | /static/js/useEmotionTheme.Dmt_qJ4x.js | 200 | application/javascript | 85 |
| 25 | /static/js/useFloatingOverlay.Cpeg7fG2.js | 200 | application/javascript | 41887 |
| 26 | /static/js/Tooltip.CcubhKj6.js | 200 | application/javascript | 38361 |
| 27 | /static/js/lib.DaUKNU-6.js | 200 | application/javascript | 1601 |
| 28 | /static/js/lib.DuoFSfCJ.js | 200 | application/javascript | 1362 |
| 29 | /static/js/lib.CMmWlZtt.js | 200 | application/javascript | 3222 |
| 30 | /static/js/space-separated-tokens.BqhiSyze.js | 200 | application/javascript | 19061 |
| 31 | /static/js/ErrorElement.Bn6KKjq6.js | 200 | application/javascript | 6924 |
| 32 | /static/js/preload-helper.HclGiUj8.js | 200 | application/javascript | 1211 |
| 33 | /static/js/StreamlitMarkdown.BYA62LKI.js | 200 | application/javascript | 222855 |
| 34 | /static/js/_baseIsEqual.sdZCjgvS.js | 200 | application/javascript | 3361 |
| 35 | /static/js/_baseProperty.BV6HSwpm.js | 200 | application/javascript | 63 |
| 36 | /static/js/_baseEach.PLhpSRgM.js | 200 | application/javascript | 1823 |
| 37 | /static/js/isEqual.CgNOpGTC.js | 200 | application/javascript | 87 |
| 38 | /static/js/pick.CbtWtxHL.js | 200 | application/javascript | 760 |
| 39 | /static/js/classnames.CRvvUuc_.js | 200 | application/javascript | 755 |
| 40 | /static/js/utils.C5rmUD0V.js | 200 | application/javascript | 752 |
| 41 | /static/js/FlexContext.CiIL1cCY.js | 200 | application/javascript | 698 |
| 42 | /static/js/index.esm.BUFMYQEK.js | 200 | application/javascript | 2645 |
| 43 | /static/js/extends.To_WgASY.js | 200 | application/javascript | 231 |
| 44 | /static/js/Close.esm.C9UX1nP9.js | 200 | application/javascript | 1144 |
| 45 | /static/js/Icon.BwNwD-ho.js | 200 | application/javascript | 2492 |
| 46 | /static/js/DynamicIcon.qdIiJ9dI.js | 200 | application/javascript | 3060 |
| 47 | /static/js/useFocusRing.DKgtHVTa.js | 200 | application/javascript | 9807 |
| 48 | /static/js/useDescription.D44v6Ed8.js | 200 | application/javascript | 3475 |
| 49 | /static/js/useFocusable.BMuUTJBc.js | 200 | application/javascript | 662 |
| 50 | /static/js/Hidden.tKmNEkoU.js | 200 | application/javascript | 1176 |
| 51 | /static/js/shim.BbyJgaa_.js | 200 | application/javascript | 884 |
| 52 | /static/js/textSelection.DgmAmjoW.js | 200 | application/javascript | 977 |
| 53 | /static/js/usePress.efhlSQnF.js | 200 | application/javascript | 8078 |
| 54 | /static/js/FocusScope.iQ9jRcfz.js | 200 | application/javascript | 13363 |
| 55 | /static/js/useCollection.ChFCPfFU.js | 200 | application/javascript | 40518 |
| 56 | /static/js/useLabel.DizWobrd.js | 200 | application/javascript | 724 |
| 57 | /static/js/getScrollParent.DcXPel1L.js | 200 | application/javascript | 4025 |
| 58 | /static/js/SharedElementTransition.D-H-TuM3.js | 200 | application/javascript | 1971 |
| 59 | /static/js/SelectionIndicator.Bj4Tikfi.js | 200 | application/javascript | 1706 |
| 60 | /static/js/NumberFormatter.CHYrjPj-.js | 200 | application/javascript | 2672 |
| 61 | /static/js/useNumberFormatter.C74S3dgX.js | 200 | application/javascript | 310 |
| 62 | /static/js/ProgressBar.Dnq9p48R.js | 200 | application/javascript | 1399 |
| 63 | /static/js/Text.CLxOerZw.js | 200 | application/javascript | 163 |
| 64 | /static/js/VisuallyHidden.BzpdCoAc.js | 200 | application/javascript | 731 |
| 65 | /static/js/extends.CvVTau-c.js | 200 | application/javascript | 231 |
| 66 | /static/js/KeyboardArrowDown.esm.CTwXU0Q8.js | 200 | application/javascript | 16112 |
| 67 | /static/js/useFormValidation.BcvRvPA1.js | 200 | application/javascript | 4105 |
| 68 | /static/js/useFormReset.Dm_0HjET.js | 200 | application/javascript | 372 |
| 69 | /static/js/useSlot.BgZLzoY2.js | 200 | application/javascript | 412 |
| 70 | /static/js/useToggleState.RbyUIfC3.js | 200 | application/javascript | 422 |
| 71 | /static/js/styled-components.3il69GG_.js | 200 | application/javascript | 10744 |
| 72 | /static/js/toastQueue.CeWtco9l.js | 200 | application/javascript | 1877 |
| 73 | /static/js/styled-components.BjKbfR5p.js | 200 | application/javascript | 18458 |
| 74 | /static/js/BaseButton.eTlHCX_j.js | 200 | application/javascript | 1182 |
| 75 | /static/js/useExecuteWhenChanged.1O5Ch07q.js | 200 | application/javascript | 273 |
| 76 | /static/js/FormClearHelper.G2WY61Ig.js | 200 | application/javascript | 771 |
| 77 | /static/js/useWidgetManagerElementState.pqPEebW5.js | 200 | application/javascript | 637 |
| 78 | /static/js/useTimeout.DgWF0Nme.js | 200 | application/javascript | 649 |
| 79 | /static/js/constants.M-X9ULkd.js | 200 | application/javascript | 65 |
| 80 | /static/js/BaseButtonTooltip.B83DZSNb.js | 200 | application/javascript | 431 |
| 81 | /static/js/useLabelTitleTooltip.VS7apAPP.js | 200 | application/javascript | 536 |
| 82 | /static/js/DynamicButtonLabel.BTjDBnmI.js | 200 | application/javascript | 11082 |
| 83 | /static/js/useResolvedWrap.DnjqnyWR.js | 200 | application/javascript | 266 |
| 84 | /static/js/useResizeObserver.3kyCQ1g6.js | 200 | application/javascript | 1311 |
| 85 | /static/js/useCalculatedDimensions.DmyA6xJn.js | 200 | application/javascript | 339 |
| 86 | /static/js/FormsContext.C6bVDc7u.js | 200 | application/javascript | 578 |
| 87 | /static/js/AlertElement.jnyaBsKJ.js | 200 | application/javascript | 1585 |
| 88 | /static/js/useCopyToClipboard.C-ywP4Jl.js | 200 | application/javascript | 619 |
| 89 | /static/js/katex.min.CvAXSeo_.js | 200 | application/javascript | 73 |
| 90 | /static/js/useRequiredContext.DBsQavvD.js | 200 | application/javascript | 267 |
| 91 | /static/js/ViewStateContext.BWrgx8uF.js | 200 | application/javascript | 232 |
| 92 | /static/js/BackendOperationContext.BhY2-GLf.js | 200 | application/javascript | 232 |
| 93 | /static/js/NavigationContext.4T7w2rIe.js | 200 | application/javascript | 287 |
| 94 | /static/js/src.D7mXJKB_.js | 200 | application/javascript | 70 |
| 95 | /static/js/styled-components.C8Nbdcp-.js | 200 | application/javascript | 604 |
| 96 | /static/js/PortalContext.DiHTlKpY.js | 200 | application/javascript | 195 |
| 97 | /static/js/Check.esm.tHOxRXBO.js | 200 | application/javascript | 583 |
| 98 | /static/js/ContentCopy.esm.Ccfy7DwA.js | 200 | application/javascript | 659 |
| 99 | /static/js/Toolbar.C5O8pUCg.js | 200 | application/javascript | 2315 |
| 100 | /static/js/CodeBlockCopyToolbar.B63lmxFm.js | 200 | application/javascript | 645 |
| 101 | /static/js/isMobile.BrviDGEH.js | 200 | application/javascript | 19915 |
| 102 | /static/js/useWindowDimensionsContext.Bq7b7Xl1.js | 200 | application/javascript | 280 |
| 103 | /static/js/v4.DDdyfk2q.js | 200 | application/javascript | 770 |
| 104 | /static/js/useOverlayDismissal.Pckd1piy.js | 200 | application/javascript | 1093 |
| 105 | /static/js/useScrollbarGutterSize.Dz-mAUy7.js | 200 | application/javascript | 605 |
| 106 | /static/js/ErrorHandling.H5STbbYb.js | 200 | application/javascript | 71 |
| 107 | /static/js/ResizeObserver.es.B3NkmA6c.js | 200 | application/javascript | 7693 |
| 108 | /static/js/query-string.CE9hiqqO.js | 200 | application/javascript | 8387 |
| 109 | /static/js/lib.BQWveI8K.js | 200 | application/javascript | 16370 |
| 110 | /static/js/extends.SdklyJLW.js | 200 | application/javascript | 231 |
| 111 | /static/css/katex.CAfVENUR.css | 200 | text/css; charset=utf-8 | 28894 |
| 112 | /static/css/index.DHyCV7PK.css | 200 | text/css; charset=utf-8 | 1069 |

No direct chunk failure was observed: BAD_CHUNKS=0.

### V1.c Warm repeat

The immediate warm repeat at 2026-09-02T18:38:58.882188+07:00 returned:

| Check | Warm result |
|---|---|
| Root | 200, text/html; charset=utf-8, 11,141 bytes, 0.249848 s |
| Referenced chunks | 112 |
| Wrong status or content type | 0 |
| Total chunk bytes | 2,122,214 |

The warm pass had the same root size and referenced path set as V1.b and no
status/MIME failure. Therefore no cold-fail/warm-pass split was observed in
the bounded direct HTTP checks.

### V1.d Cloud Run configuration

Read-only gcloud run services describe vietragops-web --region=asia-southeast1
returned:

| Field | Observed value |
|---|---|
| minScale | 0 |
| maxScale | 2 |
| containerConcurrency | 1 |
| CPU limit | 1 |
| CPU allocation mode | Not explicit in the response: no run.googleapis.com/cpu-throttling annotation and no cpuIdle field; exact throttled versus always-allocated mode is not independently claimed |
| Memory | 512Mi |
| Startup probe | TCP port 8501; failure threshold 1; period 240 s; timeout 240 s |
| Timeout | 120 s |
| Execution environment | gen2 |

The configuration supports a capacity explanation. H2 specifically cannot be
confirmed from the exposed CPU allocation fields.

### V1.e Server-side logs

Read-only gcloud logging read for vietragops-web with --freshness=24h returned
986 entries:

| HTTP status | Entries |
|---:|---:|
| 200 | 918 |
| 429 | 31 |
| 304 | 2 |
| 101 | 6 |
| No status in selected projection | 38 |

All 31 static 429 entries were on revision vietragops-web-00002-wp9, used the
Chrome 151 user-agent, and occurred between 2026-09-02T09:12:15Z and
2026-09-02T09:13:29Z. The 26 distinct static paths were:

~~~text
/static/js/_baseMap.OhVc4KF-.js
/static/js/Cancel.esm.Dl28HDUU.js
/static/js/Checkbox.-4urQUut.js
/static/js/dist.M42-4E3x.js
/static/js/ErrorOutline.esm.CeVVFX3b.js
/static/js/FileDownload.esm.B01WmOa3.js
/static/js/getItemCount.DByO3ocf.js
/static/js/Input.Bqq6kcs8.js
/static/js/InputInstructions.BdRjLMGx.js
/static/js/isEmpty.DjruDP6v.js
/static/js/Metric.BEvnGqRJ.js
/static/js/path.C_SyPjZC.js
/static/js/range.EplFIxc7.js
/static/js/resolveDefaultExport.DJbX7TqQ.js
/static/js/Selectbox.DTwsqAB2.js
/static/js/serialization.BdCe8Hfp.js
/static/js/TextInput.DHKamV9Y.js
/static/js/time.BEzQW4ce.js
/static/js/unzip.BaBcYNJz.js
/static/js/useTextField.CS2ef5HH.js
/static/js/useUpdateUiValue.p9BcgoMl.js
/static/js/value.D6n4OHqi.js
/static/js/web-namespaces.BxZ_GhEx.js
/static/js/WidgetLabel.Cr4ld6Ih.js
/static/js/WidgetLabelHelpIconInline.CxEaud35.js
/static/js/withCalculatedWidth.Ckt1PQuG.js
~~~

The logs are direct evidence that the web service has returned static-module
429s, including widget modules, but they do not by themselves prove that the
current single-client request would fail. No second tab was opened to recreate
the known saturation condition.

### V1.f Host isolation

The prior browser proof was Chrome. This check used the Codex In-app Browser,
which had no existing tab; one new tab only was created and kept on the public
web URL. The load was performed in a fresh browser surface and no second tab
was opened.

After the bounded load:

| Browser observation | Result |
|---|---|
| Question textbox | Present, count 1 |
| Generate grounded answer button | Present, count 1, enabled |
| Console errors | 0 |
| Console warnings | 3 WebSocket onclose warnings |
| API status pill | API unavailable visible |
| Answer/refusal submission | Not executed |

The widget itself therefore loaded in the alternate browser surface. The
visible API unavailable state is a separate authenticated API-readiness gap;
it is not used to label the static chunk failure as a service defect.

### V1.g Classification

**Classification: CAPACITY — Medium/Open.**

The decisive evidence is the combination of 31 Cloud Run static-asset 429
responses on the active revision, including TextInput, Checkbox, and Metric,
with minScale=0, maxScale=2, and containerConcurrency=1, against clean current
direct HTTP and alternate-browser widget passes. This shows intermittent
service capacity behavior. It does not support SERVICE_DEFECT, because no
current chunk returned 429/404/503 or an incorrect MIME type, and the widget
loaded in the alternate browser. It is not classified as HOST_OR_BROWSER,
because the server logs contain actual same-revision static 429 responses. It
is not INCONCLUSIVE, because the server-side 429 evidence and configuration
provide a specific capacity class.

## V2 — Budget and cost observation

The billing account identifier was captured only in an in-session shell
variable for the read-only query. It is not present in this artifact, any
transcript record, or any committed file.

gcloud billing budgets list --billing-account=<shell-only-value> returned four
budget configurations:

| Display name | Amount | Threshold rules |
|---|---:|---|
| VietRAGOps Gate 09R USD30 ceiling | 750,000 VND | 50% / 80% / 100% |
| (three unrelated budgets, withheld) | withheld | withheld |

The billing account is shared with three budgets belonging to projects outside
this gate's scope. Their display names and amounts are deliberately withheld
from this public artifact as out-of-scope private data; only their count is
recorded, because the count is what establishes that the target budget is one
of four on a shared billing account. None of them filters this project.

### Frozen-control comparison

| Control | Disposition | Evidence and exact delta |
|---|---|---|
| Target budget 750,000 VND | MATCH | Observed target amount 750,000 VND; delta 0 VND |
| Target alerts 50% / 80% / 100% | MATCH | Observed thresholds exact; deltas 0 / 0 / 0 percentage points |
| Cloud Run control 375,000 VND | MATCH as derived control; not an independent budget object | 750,000 / 2 = 375,000 VND; arithmetic delta 0 VND. No separate 375,000-VND budget object was observed |
| USD 15 warning/stop policy | UNCHANGED | Frozen policy remains USD 15 warning/stop, with no ceiling raise or policy mutation |

The target budget filter was project-scoped and had no Cloud Run service filter;
this is why the 375,000-VND Cloud Run value is reported as a derived control,
not fabricated as a separate budget. The Budgets API response exposed
configuration fields only (amount, budgetFilter, displayName,
notificationsRule, thresholdRules, and metadata); it had no current-spend,
usage, or forecast field. The previous Console path required interactive sign-in
and no current cost figure was reachable from the approved CLI path.

**Current cost: UNVERIFIED.** The historical 0.00 VND observation from
2026-08-31 is not restated as a current number. No BigQuery billing export was
created.

## V3 — Identity-token root cause

### Exact read-only observations

| Check | Result |
|---|---|
| gcloud auth list account type | user only; account identifier not recorded |
| gcloud auth print-identity-token with no --audiences | Exit 0; token stdout was discarded and never read |
| gcloud auth print-identity-token --audiences=https://vietragops-api-ohtmo6zgoq-as.a.run.app | Exit 1 |
| Exact stderr | ERROR: (gcloud.auth.print-identity-token) Invalid account type for `--audiences`. Requires valid service account. |

The leading hypothesis is confirmed. A user account can mint the default
identity token in this environment, but gcloud rejects an arbitrary audience
for that account type. This is expected gcloud behavior, not evidence of an IAM
change or an API defect.

The Git Schannel observation is independent. Git failed while Windows Schannel
tried to acquire TLS credentials; the OpenSSL Git retry succeeded. The gcloud
audience failure occurs after gcloud authentication is available and is a
semantic account-type restriction. The earlier local gcloud WinError 5 on
credentials.db was a separate host file-permission blocker; the successful
read-only run used elevated execution and did not repair that ACL.

### Impersonation approval request — not executed

To verify private API readiness and authenticated MCP behavior later, approve
only the following least-privilege service-account grant if needed. The active
user principal is intentionally a placeholder and must be entered by the
account owner at approval time; it is not written here.

~~~text
gcloud iam service-accounts add-iam-policy-binding vietragops-web-runtime@vietragops-evolve-20260831.iam.gserviceaccount.com --project=vietragops-evolve-20260831 --member="user:<ACTIVE_USER_PRINCIPAL_ENTERED_AT_APPROVAL>" --role="roles/iam.serviceAccountTokenCreator"
~~~

Then the read-only token test would be:

~~~text
gcloud auth print-identity-token --impersonate-service-account=vietragops-web-runtime@vietragops-evolve-20260831.iam.gserviceaccount.com --audiences=https://vietragops-api-ohtmo6zgoq-as.a.run.app
~~~

Scope: one active operator principal, one existing web runtime service
account, one service-account-level roles/iam.serviceAccountTokenCreator
binding. Do not grant a project-wide role, create a key, change Cloud Run
IAM, or execute either command in this gate.

**STOP condition reached.** Authenticated API readiness, MCP wrong-Origin,
MCP approved-Origin, and the live MCP tool list remain **unverified** until
the grant is separately approved or a Console-based check is authorized. The
frozen Gate 09R receipt is not a fresh observation.

## V4 — Gate 09R disposition

Appended to gates/results/GATE_09R_RESULT.md:

~~~text
## Post-release addendum — Gate 09R-V (2026-09-02)
~~~

The addendum records the CAPACITY classification and states explicitly that
the “browser grounded/refusal flows passed with zero errors” claim is
time-scoped to **2026-08-31 on a warmed instance**, not a continuing
availability guarantee. The Gate 09R status line remains PASS.

Added RISK-0024 to _agent_ops/RISK_REGISTER.md:

~~~text
Severity: Medium
Status: Open
Area: Public web dynamic-module availability
~~~

Because the classification is CAPACITY, _agent_ops/PHASE_ROADMAP.md and
_agent_ops/phase_context_cards/evolve_2026_08_26/GATE_09R.md were not changed;
the prompt required those updates only for SERVICE_DEFECT.

## V5 — Pending user decisions

No decision below was executed.

| Decision | Recommendation | Reason / trade-off |
|---|---|---|
| tests/test_groq_rotation.py versus RISK-0009 | Recommend (d) security review first; then choose (a) delete or (c) track with a DEC stating rotation is tested but deliberately not shipped | The test implements multi-key discovery, round-robin, cooldown skipping, and retry-after-429. Deleting is cleanest; tracking preserves evidence but carries policy confusion unless reviewed |
| Push 55bb73a | Hold for a separate explicit push approval, now that the 09R-V result exists | Push remains an external release action and is separate from local commit/result creation |
| Approve V3 impersonation grant | Approve only if authenticated API/MCP verification is needed; use the service-account-level least-privilege request above | It enables the missing observation, but changes IAM and must remain a separate approval |
| Approve WinError 5 ACL repair on app/api/__pycache__/routes_documents.cpython-313.pyc | Defer unless a fresh compileall proof is required; if approved, repair only the owning principal's Modify permission on that file/inherited ACL | No ownership change, blind cache deletion, or broad ACL rewrite is justified |

## Cost and mutation receipt

- New GCP spend: 0 VND.
- Groq calls initiated by this gate: 0.
- Firecrawl calls initiated by this gate: 0.
- Product source and deploy files: unchanged.
- No GCP mutation, IAM grant, budget edit, API enablement, billing export,
  deployment, traffic update, scaling change, image rebuild, rollback, or
  cleanup occurred.
- No secret value, token, key, password, MFA code, payment data, or billing
  account identifier was read into the result or any artifact.
- No overlay path was staged, restored, deleted, stashed, reset, amended,
  rebased, or pushed.

## Limitations

1. Windows curl and initial non-elevated gcloud calls were blocked by host
   credential/file-permission behavior. Python OpenSSL HTTP and an approved
   elevated read-only gcloud execution supplied the valid observations.
2. The Cloud Run response did not expose an explicit CPU allocation mode, so H2
   is not confirmed.
3. Current HTTP and the alternate-browser widget pass do not guarantee future
   availability; the log evidence shows intermittent static 429 behavior.
4. The alternate browser displayed API unavailable; no question/refusal flow
   was submitted because authenticated API readiness was outside the verified
   scope.
5. Current billing spend is unverified. The historical 2026-08-31 zero-cost
   receipt is not current proof.
6. Authenticated API readiness and cloud MCP Origin/tool behavior remain
   unverified pending the explicit impersonation/Console decision.

## Exact next action

Stop after this result artifact. Await the four pending user decisions. Do not
repair, scale, deploy, rebuild, change IAM, edit budgets, enable APIs, create a
billing export, push, rerun Gate 07/08, revisit Gate 08, start Gate 09/10, or
stage the overlay without a new explicit approval and protocol.

## Closure Receipt

Closure Receipt
- CURRENT_TASK.md      : updated (Gate 09R-V complete, classification, limitations, and stop condition)
- IMPLEMENTATION_LOG.md: appended 2026-09-02 Gate 09R-V V0–V3 evidence and no-mutation receipt
- SESSION_BRIEF.md     : updated (current Gate 09R-V state, Last Verified Commit remains 55bb73a, pending decisions)
- PROJECT_CONTEXT_CARD : not needed (no architecture or durable milestone change; gate result and risk/decision records contain the scoped observation)
- DECISION_LOG.md      : updated (DEC-0029 added)
- RISK_REGISTER.md     : updated (RISK-0024 added as Medium/Open; explicit gate instruction, not staged)
- REPO_MAP.md          : not needed (no code file added, moved, or removed)

Additional gate records:
- GATE_09RV_PROTOCOL.json : updated (created and frozen; SHA-256 recorded above)
- GATE_09R_RESULT.md      : updated (post-release addendum appended; status line remains PASS)
- PHASE_ROADMAP.md        : not needed (CAPACITY; conditional update was only for SERVICE_DEFECT)
- GATE_09R.md             : not needed (CAPACITY; conditional update was only for SERVICE_DEFECT)
- INDEX.md                : not needed (read order unchanged)
- GATE_09R_PROTOCOL.json  : not needed (frozen protocol unchanged)

## Final stop

Gate 09R-V is complete. No further action is authorized in this gate.
