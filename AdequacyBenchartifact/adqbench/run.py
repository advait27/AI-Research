"""Experiment driver. Produces every number reported in the paper."""
from __future__ import annotations
import json, gzip, time, random, os, statistics
from math import sqrt
from scipy.stats import binomtest, norm as _norm
from .generate import build_corpus, FAMILIES
from .emit import emit, serialise, attr_count, CONDITIONS, BARE, OTEL, GUARD, TYPED
from .resolve import CONSERVATIVE, HEURISTIC

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")
os.makedirs(OUT, exist_ok=True)
N_PER_FAMILY = 200
SEED = 20260820


def wilson(k, n, z=1.96):
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def mcnemar(a, b):
    """Paired comparison of two boolean outcome vectors. Exact binomial."""
    n01 = sum(1 for x, y in zip(a, b) if (not x) and y)
    n10 = sum(1 for x, y in zip(a, b) if x and (not y))
    if n01 + n10 == 0:
        return {"b": n10, "c": n01, "p": 1.0}
    r = binomtest(n10, n10 + n01, 0.5)
    return {"b": n10, "c": n01, "p": float(r.pvalue)}


def question(tr):
    return {"home_tenant": tr.session_tenant, "candidate": tr.meta.get("candidate")}


def evaluate(corpus):
    """Returns per-(det,cond) outcome vectors aligned by trajectory."""
    recs = {}
    for tr in corpus:
        recs[tr.tid] = {c: emit(tr, c) for c in CONDITIONS}
    data = {}
    for fam, (det, _) in FAMILIES.items():
        sub = [t for t in corpus if t.family == fam]
        data[det] = {"n": len(sub), "base_rate": sum(t.truth[det] for t in sub) / len(sub),
                     "cond": {}}
        for cond in CONDITIONS:
            resolved, correct, joint, hfd, hall = [], [], [], [], []
            for t in sub:
                q = question(t)
                ok, ans = CONSERVATIVE[det](recs[t.tid][cond], cond, q)
                resolved.append(ok)
                if ok:
                    correct.append(ans == t.truth[det])
                joint.append(ok and ans == t.truth[det])
                _, hans = HEURISTIC[det](recs[t.tid][cond], cond, q)
                hall.append(hans == t.truth[det])
                if not ok:
                    hfd.append(hans != t.truth[det])
            nres = sum(resolved)
            data[det]["cond"][cond] = {
                "coverage": nres / len(sub),
                "coverage_ci": wilson(nres, len(sub)),
                "soundness": (sum(correct) / nres) if nres else None,
                "soundness_ci": wilson(sum(correct), nres) if nres else None,
                "joint": sum(joint) / len(sub),
                "unresolved_n": len(hfd),
                "heur_fdr_on_unresolved": (sum(hfd) / len(hfd)) if hfd else None,
                "heur_error_all": 1 - sum(hall) / len(sub),
                "_joint_vec": joint,
            }
    return data, recs


def overhead(corpus, recs):
    rows = {}
    for cond in CONDITIONS:
        raw, gz, attrs, spans, steps = 0, 0, 0, 0, 0
        for tr in corpus:
            s = serialise(recs[tr.tid][cond])
            raw += len(s.encode())
            gz += len(gzip.compress(s.encode()))
            attrs += attr_count(recs[tr.tid][cond])
            spans += len(recs[tr.tid][cond])
            steps += tr.n_steps()
        reps = []
        for _ in range(5):
            t0 = time.perf_counter()
            for tr in corpus:
                emit(tr, cond)
            reps.append(time.perf_counter() - t0)
        el = statistics.median(reps)
        rows[cond] = {"bytes_per_traj": raw / len(corpus),
                      "gzip_bytes_per_traj": gz / len(corpus),
                      "bytes_per_step": raw / steps,
                      "fields_per_span": attrs / spans,
                      "emit_ms_per_1k_steps": 1000 * el / steps * 1000}
    base = rows[OTEL]["bytes_per_traj"]
    for c in rows:
        rows[c]["bytes_ratio_vs_otel"] = rows[c]["bytes_per_traj"] / base
    return rows


def degradation(corpus, recs, fractions=(0.0, 0.05, 0.10, 0.20, 0.40), seed=7):
    out = {}
    for p in fractions:
        r = random.Random(seed)
        agg = {}
        for cond in CONDITIONS:
            res = cor = tot = 0
            for tr in corpus:
                det = FAMILIES[tr.family][0]
                rows = [x for x in recs[tr.tid][cond] if r.random() >= p]
                ok, ans = CONSERVATIVE[det](rows, cond, question(tr))
                tot += 1
                if ok:
                    res += 1
                    cor += (ans == tr.truth[det])
            agg[cond] = {"coverage": res / tot,
                         "soundness": (cor / res) if res else None}
        out[str(p)] = agg
    return out


def proxy_sweep(levels=((0.95, 0.02), (0.90, 0.05), (0.80, 0.15), (0.70, 0.30), (0.60, 0.45))):
    out = []
    for pp, po in levels:
        corpus = build_corpus(N_PER_FAMILY, seed=SEED, p_sens_prot=pp, p_sens_open=po)
        sub = [t for t in corpus if t.family == "F1"]
        # proxy precision measured on the corpus itself
        tp = fp = 0
        for t in sub:
            for e in t.events:
                if e.kind == "retrieve":
                    from .resolve import _sensitive_title
                    flag = _sensitive_title(f"title={e.display_name}")
                    prot = t.values[e.produces].classification >= 2
                    if flag and prot:
                        tp += 1
                    elif flag and not prot:
                        fp += 1
        prec = tp / (tp + fp) if (tp + fp) else float("nan")
        row = {"p_sens_given_protected": pp, "p_sens_given_open": po,
               "proxy_precision": prec}
        for cond in CONDITIONS:
            err = 0
            for t in sub:
                rows = emit(t, cond)
                ok, ans = CONSERVATIVE["D1"](rows, cond, question(t))
                if ok:
                    err += (ans != t.truth["D1"])
                else:
                    _, h = HEURISTIC["D1"](rows, cond, question(t))
                    err += (h != t.truth["D1"])
            row[cond] = err / len(sub)
        out.append(row)
    return out


def oracle_control(corpus):
    """Perfect typing, no relation: does knowing every document's true
    classification suffice without a derivation relation?"""
    sub = [t for t in corpus if t.family == "F1"]

    def oracle(tr):
        send = next(i for i, e in enumerate(tr.events) if e.kind == "external_send")
        return any(e.kind == "retrieve"
                   and tr.values[e.produces].classification >= 2
                   for e in tr.events[:send])

    err = sum(1 for t in sub if oracle(t) != t.truth["D1"])
    fp = sum(1 for t in sub if oracle(t) and not t.truth["D1"])
    fn = sum(1 for t in sub if (not oracle(t)) and t.truth["D1"])
    dv = [t for t in sub if not t.meta["single_hop"]]
    dr = [t for t in sub if t.meta["single_hop"]]
    return {"n": len(sub), "oracle_typing_error_rate": err / len(sub),
            "false_positive": fp / len(sub), "false_negative": fn / len(sub),
            "n_derived": len(dv),
            "error_on_derived": sum(1 for t in dv if oracle(t) != t.truth["D1"]) / len(dv),
            "n_direct": len(dr),
            "error_on_direct": sum(1 for t in dr if oracle(t) != t.truth["D1"]) / len(dr)}


def composition(corpus):
    key = {"F1": ("direct_send", lambda t: t.meta["single_hop"]),
           "F2": ("single_effecting", lambda t: t.meta["n_effecting"] == 1),
           "F3": ("single_tenant", lambda t: t.meta["single_tenant"]),
           "F4": ("mean_chain_depth", lambda t: t.meta["chain_depth"]),
           "F5": ("name_decidable", lambda t: t.meta["name_decidable"]),
           "F6": ("single_principal", lambda t: t.meta["single_principal"])}
    out = {}
    for fam, (name, fn) in key.items():
        s = [t for t in corpus if t.family == fam]
        out[fam] = {"n": len(s), "mean_steps": sum(t.n_steps() for t in s) / len(s),
                    name: sum(fn(t) for t in s) / len(s)}
    return out


def main():
    t0 = time.time()
    corpus = build_corpus(N_PER_FAMILY, seed=SEED)
    data, recs = evaluate(corpus)

    # paired significance tests on the joint outcome
    tests = {}
    for det in data:
        v = data[det]["cond"]
        tests[det] = {
            "TYPED_vs_GUARD": mcnemar(v[TYPED]["_joint_vec"], v[GUARD]["_joint_vec"]),
            "GUARD_vs_OTEL": mcnemar(v[GUARD]["_joint_vec"], v[OTEL]["_joint_vec"]),
            "OTEL_vs_BARE": mcnemar(v[OTEL]["_joint_vec"], v[BARE]["_joint_vec"]),
        }
    # pooled across determinations
    pooled = {}
    for cond in CONDITIONS:
        vec = []
        for det in data:
            vec += data[det]["cond"][cond]["_joint_vec"]
        pooled[cond] = vec
    pooled_tests = {
        "TYPED_vs_GUARD": mcnemar(pooled[TYPED], pooled[GUARD]),
        "GUARD_vs_OTEL": mcnemar(pooled[GUARD], pooled[OTEL]),
        "OTEL_vs_BARE": mcnemar(pooled[OTEL], pooled[BARE]),
    }
    pooled_rate = {c: (sum(pooled[c]) / len(pooled[c]),
                       wilson(sum(pooled[c]), len(pooled[c]))) for c in CONDITIONS}

    ov = overhead(corpus, recs)
    deg = degradation(corpus, recs)
    sweep = proxy_sweep()

    for det in data:
        for c in data[det]["cond"]:
            data[det]["cond"][c].pop("_joint_vec", None)

    res = {"config": {"n_per_family": N_PER_FAMILY, "seed": SEED,
                      "n_trajectories": len(corpus),
                      "total_steps": sum(t.n_steps() for t in corpus),
                      "mean_steps": statistics.mean(t.n_steps() for t in corpus)},
           "per_determination": data, "tests": tests,
           "pooled": {"rate": pooled_rate, "tests": pooled_tests},
           "overhead": ov, "degradation": deg, "proxy_sweep": sweep,
           "oracle_typing_control": oracle_control(corpus),
           "corpus_composition": composition(corpus),
           "runtime_s": time.time() - t0}
    with open(os.path.join(OUT, "results.json"), "w") as f:
        json.dump(res, f, indent=1, default=str)
    return res


if __name__ == "__main__":
    r = main()
    print(json.dumps(r["config"], indent=1))
    print("runtime", round(r["runtime_s"], 1), "s")
