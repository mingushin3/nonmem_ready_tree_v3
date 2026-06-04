"""Phase 5 orchestrator — slice-scoped (DECISION-D2 family interleave).

입력 strand의 c_sequence를 registry 통해 순차 dispatch한다. registry에 배선된 c만 실행하고,
없는 c_id를 만나면 SliceBoundary(NotImplementedError)를 던져 슬라이스 경계를 명시한다
(PROMPTS L298). 영구 stub 금지 — 미구현 c는 진짜로 미구현이다.
slice 1 = MERGED_CELL(c0340/c0341). slice 2 = TIME family(축 detect c0203 + verify c0213
+ ROUTE c0251 + 하류 mess c0310/c0311/c0314/c0315). slice 3 = TIMEZONE(c0312/c0313, TIME mess
블록 마무리; can_route_to_q=[] → no Q). slice 4 = COVARIATE_LAYOUT(c0380/c0381 + 기구현 c0121 PIVOT
활성화, GAP-16 종결). slice 5 = PLACEBO_SUBJECT(c0392/c0393, 자기완결·하류 transform 없음; no Q).
slice 6 = BLQ_TOKEN(mess detect+normalize c0305/c0306 + A5 axis c0205 + ROUTE c0253→Q01/Q15D/INVALID;
GAP-15 종결: c0306 산출 blq_detected/lloq_value가 기구현 c0020/c0021을 cross-layer 활성화). ★ Q01 strand
라우팅 실주체=c0253(c0306 아님; c0306.can_route_to_q=[Q01]은 Phase 7 D-S4 선언, GAP-28/GAP-26 동형).

D-S1 (detection-mandatory): transform·route c의 requires_detection_by가 가리키는 DETECT/VERIFY c가
먼저 실행(meta에 '{req}_ran' 기록)되지 않으면 dispatch가 거부한다(cut-vertex). 즉 runtime은
mess_profile을 모른 채 DETECT 결과로만 fix-c/route-c에 도달한다.

terminal 도출: ROUTE c가 a3_state fail → Q-terminal(QUARANTINE + q_code)을 도출하면
run_strand가 거기서 종료한다(D-S4 conditional routing의 strand-내 실현; cost는
strands.json 정합으로 Σc.cost만 누적, Q.routing_cost 비가산). ROUTE 없는 경로의 terminal은
하류 c 구현 후로 보류(None) — 날조 금지.
"""

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.c_units.c0340_detect_merged_cell import detect_merged_cell
from src.c_units.c0341_propagate_merged_cell import propagate_merged_cell
# slice 2: TIME family routing chain (축 detect/verify + ROUTE)
from src.c_units.c0203_detect_time_format import detect_time_format
from src.c_units.c0213_verify_time_anchor import verify_time_anchor
from src.c_units.c0251_route_time_format import route_time_format
# slice 2: TIME mess normalization (L-4->L-5 detect+convert)
from src.c_units.c0310_detect_time_format import detect_time_format_mess
from src.c_units.c0311_convert_time_format import convert_time_format
from src.c_units.c0314_detect_time_anchor import detect_time_anchor
from src.c_units.c0315_convert_time_anchor import convert_time_anchor
# slice 3: TIMEZONE mess normalization (L-4->L-5 detect+normalize) — TIME mess 블록 마무리
from src.c_units.c0312_detect_timezone import detect_timezone
from src.c_units.c0313_normalize_timezone import normalize_timezone
# slice 4: COVARIATE_LAYOUT mess(L-4->L-5 detect+classify) + 기구현 자산 c0121 활성화(GAP-16 종결)
from src.c_units.c0380_detect_covariate_layout import detect_covariate_layout
from src.c_units.c0381_classify_covariate_layout import classify_covariate_layout_mess
from src.c_units.c0207_classify_covariate_layout import classify_covariate_layout
from src.c_units.c0121_pivot_covariate_layout import pivot_covariate_layout
# slice 5: PLACEBO_SUBJECT mess(L-4->L-5 detect+classify) — 자기완결(하류 transform·활성화 없음)
from src.c_units.c0392_detect_placebo_subject import detect_placebo_subject
from src.c_units.c0393_classify_placebo_subject import classify_placebo_subject
# slice 6: BLQ_TOKEN mess(detect+normalize) + A5 axis(c0205) + ROUTE→Q01(c0253) + GAP-15 활성화(c0020/c0021)
from src.c_units.c0305_detect_blq_token import detect_blq_token_mess
from src.c_units.c0306_normalize_blq_token import normalize_blq_token
from src.c_units.c0205_detect_blq_token import detect_blq_token
from src.c_units.c0253_route_blq_token import route_blq_token
from src.c_units.c0020_assign_blq_flag import assign_blq_flag
from src.c_units.c0021_assign_lloq import assign_lloq
# slice 7a — backbone activation (순수 배선, 신규 c 0): 기구현·미배선 backbone 23c를 REGISTRY에 배선.
#   axis A0–A10(c0200–c0210; c0203/c0205/c0207은 기배선) + L-1→L-2 NONMEM 컬럼(c0001/c0010–c0019)
#   + covariate(c0022/c0023 L-1→L-2, c0140/c0141 L-2→L-3). dispatch/run_strand 로직 무변경.
#   ★ GAP-29 RESOLVED(slice 7b): c0001/c0010/c0011/c0012/c0014/c0016/c0017/c0018에 meta=None 기본인자를
#     추가(본문 무변경)해 fn(df,meta) 호출규약과 정합. 8c는 meta를 read하지 않아(cite-verify) meta=None으로
#     충분 — 후방호환(fn(df) 단위테스트 green) 유지. 측정: tests/test_integration_slice7b.py.
# axis A0–A10 (kind verify/detect, reqdet=None — D-S1 gate 비대상)
from src.c_units.c0200_verify_a0_analysis_intent import verify_a0_analysis_intent
from src.c_units.c0201_detect_sheet_inventory import detect_sheet_inventory
from src.c_units.c0202_classify_regimen_descriptor import classify_regimen_descriptor
from src.c_units.c0204_verify_amt import verify_amt
from src.c_units.c0206_classify_row_ordering import classify_row_ordering
from src.c_units.c0208_classify_analyte_column import classify_analyte_column
from src.c_units.c0209_verify_cross_column_invariant import verify_cross_column_invariant
from src.c_units.c0210_detect_source_format import detect_source_format
# L-1→L-2 NONMEM 컬럼 부여 (전부 (df,meta) 정합; 8c는 GAP-29 RESOLVED로 meta=None 정규화 — slice 7b)
from src.c_units.c0001_verify_column_schema import verify_column_schema
from src.c_units.c0010_assign_evid import assign_evid
from src.c_units.c0011_assign_mdv import assign_mdv
from src.c_units.c0012_assign_amt import assign_amt
from src.c_units.c0013_assign_cmt import assign_cmt
from src.c_units.c0014_assign_rate import assign_rate
from src.c_units.c0015_assign_addl import assign_addl
from src.c_units.c0016_assign_ii import assign_ii
from src.c_units.c0017_assign_dv import assign_dv
from src.c_units.c0018_assign_id import assign_id
from src.c_units.c0019_assign_time import assign_time
# covariate 부여 — c0022/c0140은 assign_baseline_covariate, c0023/c0141은 assign_time_varying_covariate
#   동명 함수 충돌 → c_id alias.
from src.c_units.c0022_assign_baseline_covariate import assign_baseline_covariate as assign_baseline_covariate_c0022
from src.c_units.c0023_assign_time_varying_covariate import assign_time_varying_covariate as assign_time_varying_covariate_c0023
from src.c_units.c0140_assign_baseline_covariate import assign_baseline_covariate as assign_baseline_covariate_c0140
from src.c_units.c0141_assign_time_varying_covariate import assign_time_varying_covariate as assign_time_varying_covariate_c0141
# ===== slice 8 — Batch A: L-3->L-4 axis-fail ROUTE c (column-path 백로그 최고 레버리지) =====
#   axis req_det(c0200/c0204/c0206/c0207/c0208/c0209)는 전부 slice 7a 기배선 → 신규 detection 불요.
#   순수 ROUTE 구현+배선만으로 완주 173→312(A1)→353(A2). c0251/c0253 패턴 동형.
#   ★ 발견(cite-verify): empty meta에서도 c0200→AIC-MISSING·c0204→MISSING-NO-POLICY(df-default가 fail-state)라
#     c0250(74×Q11)·c0252(14×Q08)가 외부 meta 없이 부분 실현(GAP-30 ① 영향 노트 갱신; backbone-only 특성 아님).
#   ★ GAP-31 RESOLVED (Phase 7 결정 A): c0252 precond/postcond/can_route_to_q/매핑에 INFUSION-STOP-RESTART→Q04 정합
#     (cite universe_sm §3 A4 '無 Q04'). strands↔spec divergence 해소. 단 실현(168)은 c0204 verify가 INFUSION을
#     fail-route해야 하므로 ① 재배선 범위(미해소). c0257 Q03 4-state는 postcond 내 → clean(c0251 선례).
from src.c_units.c0250_route_column_schema import route_column_schema
from src.c_units.c0252_route_amt import route_amt
from src.c_units.c0254_route_covariate_layout import route_covariate_layout
from src.c_units.c0255_route_analyte_column import route_analyte_column
from src.c_units.c0256_route_cross_column_invariant import route_cross_column_invariant
from src.c_units.c0257_route_row_ordering import route_row_ordering
# ===== slice 9 — Batch B: L-3->L-4 axis DETECT/VERIFY (req_det None → D-S1 gate 비대상) =====
#   A5 sub(c0211 ABOVE_ULOQ·c0212 REPLICATE_OBS, can_route_to_q=[Q01]) + unit(c0214, →Q10)
#   + A9 helper(c0215 DUPLICATE_ROW·c0216 ENCODING, can_route_to_q=[]). detect/verify는 terminal 키
#   미반환 → run_strand 완주 path만 +86(353→439), Q 실현은 c0253/축 ROUTE·② D-S4 소관(GAP-30/32).
from src.c_units.c0211_detect_above_uloq import detect_above_uloq
from src.c_units.c0212_detect_replicate_obs import detect_replicate_obs
from src.c_units.c0214_verify_unit_declaration import verify_unit_declaration
from src.c_units.c0215_detect_duplicate_row import detect_duplicate_row
from src.c_units.c0216_detect_encoding import detect_encoding

_CUNITS_PATH = PROJECT_ROOT / "spec" / "c_units.json"
_CUNITS = json.loads(_CUNITS_PATH.read_text(encoding="utf-8"))
COST = {c["c_id"]: c["cost"] for c in _CUNITS}
REQUIRES_DETECTION = {c["c_id"]: c.get("requires_detection_by") for c in _CUNITS}

# registry: 구현·배선된 c만. 이후 슬라이스가 확장한다(stub 금지).
REGISTRY = {
    # slice 1 — MERGED_CELL
    "c0340": ("detect", detect_merged_cell),
    "c0341": ("transform", propagate_merged_cell),
    # slice 2 — TIME: 축 detect(c0203, 기구현) + verify(c0213) + ROUTE(c0251)
    "c0203": ("detect", detect_time_format),
    "c0213": ("verify", verify_time_anchor),
    "c0251": ("route", route_time_format),
    # slice 2 — TIME mess 정규화(L-4->L-5): detect+convert 쌍 (time_value 생산 chain, GAP-18)
    "c0310": ("detect", detect_time_format_mess),
    "c0311": ("transform", convert_time_format),
    "c0314": ("detect", detect_time_anchor),
    "c0315": ("transform", convert_time_anchor),
    # slice 3 — TIMEZONE 정규화(L-4->L-5): detect+normalize 쌍 (D-S1: c0313 reqdet=c0312, 자동 gate)
    "c0312": ("detect", detect_timezone),
    "c0313": ("transform", normalize_timezone),
    # slice 4 — COVARIATE_LAYOUT: mess detect+classify(c0380/c0381) + 활성화 chain(c0207 A7 axis → c0121 PIVOT)
    # c0381은 detect 등록(D-S1 orchestrator gate는 transform/route 대상) — c0380 의존은 impl artifact-guard(GAP-27).
    # c0121(transform, reqdet=c0207)는 c0207_ran D-S1 gate 자동; c0380 산출 cov_layout='wide'로 실제 pivot(GAP-16 종결).
    "c0380": ("detect", detect_covariate_layout),
    "c0381": ("detect", classify_covariate_layout_mess),
    "c0207": ("detect", classify_covariate_layout),
    "c0121": ("transform", pivot_covariate_layout),
    # slice 5 — PLACEBO_SUBJECT: mess detect+classify(c0392/c0393). can_route_to_q=[] → no Q.
    # 자기완결(하류 transform/활성화 없음, mess_catalog M103–105). c0393은 detect 등록(D-S1 orchestrator
    # gate는 transform/route 대상) — c0392 의존(has_placebo)은 impl artifact-guard(GAP-27 동형, c0381 선례).
    "c0392": ("detect", detect_placebo_subject),
    "c0393": ("detect", classify_placebo_subject),
    # slice 6 — BLQ_TOKEN: mess detect+normalize(c0305/c0306) + A5 axis(c0205, 기구현) + ROUTE→Q01(c0253).
    #   ★ Q01 strand 라우팅 실주체 = c0253(ROUTE, 645 last-c: Q01 445/Q15D 89/INVALID 111). c0306은
    #   transform이고 can_route_to_q=[Q01]은 Phase 7 D-S4 선언(GAP-28, slice 2 GAP-26 동형).
    #   ★ GAP-15 종결: c0306 산출(blq_detected/lloq_value)이 기구현 c0020/c0021을 cross-layer 활성화
    #   (c0205 axis gate 경유; blq_policy는 외부입력=통합 시 주입, 잔여 by-design).
    "c0305": ("detect", detect_blq_token_mess),       # mess DETECT (verify_visualization pass→c0306)
    "c0306": ("transform", normalize_blq_token),      # D-S1 gate: c0305_ran
    "c0205": ("detect", detect_blq_token),            # 기구현, 배선(c0253 + c0020/c0021의 reqdet)
    "c0253": ("route", route_blq_token),              # D-S1 gate: c0205_ran → Q01/Q15D/INVALID
    "c0020": ("transform", assign_blq_flag),          # 기구현, 활성화(GAP-15; reqdet c0205)
    "c0021": ("transform", assign_lloq),              # 기구현, 활성화(GAP-15; reqdet c0205)
    # ===== slice 7a — backbone activation (배선만, dispatch 무변경) =====
    # axis A0–A10 evaluators(verify/detect). route_to_q를 반환하나 run_strand은 terminal 키만 실현 →
    # INVALID/UNSUPPORTED/축-Q는 미실현(Phase 7 D-S4 conditional edge 소관, GAP-5/8/12/13).
    "c0200": ("verify", verify_a0_analysis_intent),     # A0 (→Q11)
    "c0201": ("detect", detect_sheet_inventory),        # A1 (→Q05)
    "c0202": ("detect", classify_regimen_descriptor),   # A2
    "c0204": ("verify", verify_amt),                    # A4 (→Q08/Q14)
    "c0206": ("detect", classify_row_ordering),         # A6 (→Q03/Q04)
    "c0208": ("detect", classify_analyte_column),       # A8 (→Q09; c0013 reqdet)
    "c0209": ("verify", verify_cross_column_invariant), # A9 (→Q06/Q15D)
    "c0210": ("detect", detect_source_format),          # A10 (UNSUPPORTED/INVALID)
    # L-1→L-2 NONMEM 컬럼 부여. ★ GAP-29 RESOLVED(slice 7b): c0001/c0010/c0011/c0012/c0014/c0016/c0017/c0018에
    #   meta=None 추가(본문 무변경)로 fn(df,meta) 정합. 완주 strand 미포함은 여전(27c 상류 미구현) — green 유지.
    "c0001": ("verify", verify_column_schema),          # reqdet None  [GAP-29✓ meta=None]
    "c0010": ("transform", assign_evid),                # reqdet c0001 [GAP-29✓ meta=None]
    "c0011": ("transform", assign_mdv),                 # reqdet c0010 [GAP-29✓ meta=None]
    "c0012": ("transform", assign_amt),                 # reqdet c0010 [GAP-29✓ meta=None]
    "c0013": ("transform", assign_cmt),                 # reqdet c0208
    "c0014": ("transform", assign_rate),                # reqdet c0010 [GAP-29✓ meta=None]
    "c0015": ("transform", assign_addl),                # reqdet c0010
    "c0016": ("transform", assign_ii),                  # reqdet c0015 [GAP-29✓ meta=None]
    "c0017": ("transform", assign_dv),                  # reqdet c0011 [GAP-29✓ meta=None]
    "c0018": ("transform", assign_id),                  # reqdet c0001 [GAP-29✓ meta=None]
    "c0019": ("transform", assign_time),                # reqdet c0203 (기배선)
    # covariate 부여 (reqdet c0207, 기배선). 동명함수 c_id alias.
    "c0022": ("transform", assign_baseline_covariate_c0022),     # L-1→L-2
    "c0023": ("transform", assign_time_varying_covariate_c0023), # L-1→L-2
    "c0140": ("transform", assign_baseline_covariate_c0140),     # L-2→L-3
    "c0141": ("transform", assign_time_varying_covariate_c0141), # L-2→L-3
    # ===== slice 8 — Batch A: L-3->L-4 axis-fail ROUTE c (46→52). D-S1 gate: req_det axis가 strand 내 선행 =====
    "c0250": ("route", route_column_schema),          # A0 → Q11 (reqdet c0200, 기배선)
    "c0252": ("route", route_amt),                    # A4 → Q04/Q08/Q14/INVALID (reqdet c0204; GAP-31 RESOLVED: INFUSION→Q04)
    "c0254": ("route", route_covariate_layout),       # A7 → Q07/Q13 (reqdet c0207)
    "c0255": ("route", route_analyte_column),         # A8 → Q09 (reqdet c0208)
    "c0256": ("route", route_cross_column_invariant), # A9 → Q06/Q15D/INVALID (reqdet c0209)
    "c0257": ("route", route_row_ordering),           # A6 → Q04/Q03 (reqdet c0206; Q03 4-state c0251 선례)
    # ===== slice 9 — Batch B: L-3->L-4 axis DETECT/VERIFY (52→57). req_det None → no D-S1 gate =====
    #   detect/verify는 meta 플래그만 세팅·terminal 키 미반환 → 완주 path +86(353→439). Q 미실현(②/GAP-30/32).
    "c0211": ("detect", detect_above_uloq),           # A5 ABOVE-ULOQ sub (can_route_to_q=[Q01]; runtime Q01=c0253)
    "c0212": ("detect", detect_replicate_obs),        # A5 REPLICATE sub (can_route_to_q=[Q01]; runtime Q01=c0253)
    "c0214": ("verify", verify_unit_declaration),     # unit (→Q10; df-default=fail, GAP-32; runtime 미실현 ②)
    "c0215": ("detect", detect_duplicate_row),        # A9 DUPLICATE-EXACT helper (can_route_to_q=[])
    "c0216": ("detect", detect_encoding),             # A9 ENCODING-FIX helper (can_route_to_q=[])
}


class SliceBoundary(NotImplementedError):
    """registry에 없는(=이 슬라이스 미구현) c 호출 — 슬라이스 경계 표식."""


def dispatch(c_id: str, df, meta: dict):
    """단일 c 실행. 미구현이면 SliceBoundary, D-S1 위반이면 RuntimeError."""
    if c_id not in COST:
        raise SliceBoundary(f"{c_id}: c_units.json에 없음")
    if c_id not in REGISTRY:
        raise SliceBoundary(f"{c_id}: 이 슬라이스에서 미구현 (slice boundary)")
    kind, fn = REGISTRY[c_id]
    req = REQUIRES_DETECTION.get(c_id)
    # D-S1: transform·route는 대응 DETECT/VERIFY 선행 필수(cut-vertex).
    if kind in ("transform", "route") and req is not None and not meta.get(f"{req}_ran"):
        raise RuntimeError(f"D-S1 위반: {c_id}가 detection {req} 이전에 호출됨")
    result = fn(df, meta)
    meta[f"{c_id}_ran"] = True
    return result


def run_strand(c_sequence, df, meta=None, stop_at_boundary=True):
    """strand의 c_sequence를 dispatch. 구현된 prefix를 실행하고, ROUTE c가 Q-terminal을
    도출하면 거기서 종료, 미구현 c(경계)에서도 멈춘다."""
    meta = {} if meta is None else meta
    df_cur = df
    actual = []
    cost = 0
    boundary_at = None
    terminal = None
    q_code = None
    for c_id in c_sequence:
        try:
            result = dispatch(c_id, df_cur, meta)
        except SliceBoundary:
            boundary_at = c_id
            if stop_at_boundary:
                break
            raise
        actual.append(c_id)
        cost += COST[c_id]
        if isinstance(result, dict) and result.get("df") is not None:
            df_cur = result["df"]
        # ROUTE c가 terminal(QUARANTINE/INVALID)을 도출하면 그 지점에서 strand 종료(D-S4).
        # detect/verify/transform 결과엔 'terminal' 키가 없어 통과한다(날조 금지).
        if isinstance(result, dict) and result.get("terminal") is not None:
            terminal = result["terminal"]
            q_code = result.get("q_code")
            break
    return {
        "actual_c_sequence": actual,
        "total_cost": cost,
        "terminal": terminal,
        "q_code": q_code,
        "boundary_at": boundary_at,
        "df": df_cur,
        "meta": meta,
    }


def record_path(record: dict, sc_id: str) -> Path:
    """슬라이스에서 실제 실행한 sc의 경로 기록 (canonical layout: fixtures/actual/)."""
    out_dir = PROJECT_ROOT / "fixtures" / "actual"
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{sc_id}_path.json"
    serializable = {
        "sc_id": sc_id,
        "actual_c_sequence": record["actual_c_sequence"],
        "total_cost": record["total_cost"],
        "terminal": record["terminal"],
        "q_code": record.get("q_code"),
        "boundary_at": record["boundary_at"],
    }
    path.write_text(json.dumps(serializable, ensure_ascii=False, indent=2), encoding="utf-8")
    return path
