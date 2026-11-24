# scripts/eval_skills.py
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.matching.retrieve import load_jobs

PROFILES_PATH = Path("data/eval/profiles.json")
MATCHING_PATH = Path("data/eval/matching_results.json")
OUT_PATH = Path("data/eval/skill_accuracy_results.json")


def strict_key(s: str) -> str:
    s = re.sub(r"\(.*?\)", "", s.lower())
    return re.sub(r"[^a-z0-9]", "", s)


def tokens(s: str) -> frozenset:
    s = re.sub(r"\(.*?\)", " ", s.lower())
    return frozenset(re.findall(r"[a-z0-9]+", s))


def same(a: str, b: str, lenient: bool) -> bool:
    if strict_key(a) == strict_key(b):
        return True
    if not lenient:
        return False
    ta, tb = tokens(a), tokens(b)
    return bool(ta) and bool(tb) and (ta <= tb or tb <= ta)


def student_skills(profile: dict) -> list[str]:
    skills = list(profile["skills"]["technical"])
    for pr in profile.get("projects", []):
        skills += pr.get("technologies", [])
    return skills


def evaluate(profile: dict, scored: list[dict], jobs: dict, lenient: bool) -> dict:
    mine = student_skills(profile)
    claims = correct = truth_total = truth_found = miss_total = false_missing = 0
    for item in scored:
        job = jobs[item["job_id"]]
        job_skills = job["required_skills"] + job["preferred_skills"]
        truth = [j for j in job_skills if any(same(j, s, lenient) for s in mine)]
        llm_matched = item["matched_skills"]
        claims += len(llm_matched)
        correct += sum(1 for m in llm_matched if any(same(m, t, lenient) for t in truth))
        truth_total += len(truth)
        truth_found += sum(1 for t in truth if any(same(t, m, lenient) for m in llm_matched))
        miss_total += len(item["missing_skills"])
        false_missing += sum(1 for m in item["missing_skills"] if any(same(m, s, lenient) for s in mine))
    p = correct / claims if claims else 0.0
    r = truth_found / truth_total if truth_total else 0.0
    f = 2 * p * r / (p + r) if p + r else 0.0
    return {"precision": round(p, 3), "recall": round(r, 3), "f1": round(f, 3),
            "false_missing_rate": round(false_missing / miss_total, 3) if miss_total else 0.0,
            "claims": claims, "true_matches": truth_total}


def main() -> None:
    profiles = {p["id"]: p["profile"] for p in json.loads(PROFILES_PATH.read_text(encoding="utf-8"))}
    matching = json.loads(MATCHING_PATH.read_text(encoding="utf-8"))
    jobs = load_jobs()

    results = {"strict": {}, "lenient": {}}
    for mode in ("strict", "lenient"):
        for pid, data in matching.items():
            results[mode][pid] = evaluate(profiles[pid], data["all_scored"], jobs, mode == "lenient")

    print(f"{'profile':20s} | {'STRICT P':>8s} {'R':>5s} {'F1':>5s} {'falseMiss':>9s} | {'LENIENT P':>9s} {'R':>5s} {'F1':>5s} {'falseMiss':>9s}")
    for pid in matching:
        s, l = results["strict"][pid], results["lenient"][pid]
        print(f"{pid:20s} | {s['precision']:8.2f} {s['recall']:5.2f} {s['f1']:5.2f} {s['false_missing_rate']:9.2f} | "
              f"{l['precision']:9.2f} {l['recall']:5.2f} {l['f1']:5.2f} {l['false_missing_rate']:9.2f}")
    for mode in ("strict", "lenient"):
        n = len(results[mode])
        results[mode]["AVERAGE"] = {k: round(sum(v[k] for v in results[mode].values() if isinstance(v, dict)) / n, 3)
                                    for k in ("precision", "recall", "f1", "false_missing_rate")}
    s, l = results["strict"]["AVERAGE"], results["lenient"]["AVERAGE"]
    print(f"{'AVERAGE':20s} | {s['precision']:8.2f} {s['recall']:5.2f} {s['f1']:5.2f} {s['false_missing_rate']:9.2f} | "
          f"{l['precision']:9.2f} {l['recall']:5.2f} {l['f1']:5.2f} {l['false_missing_rate']:9.2f}")

    # examples to check by hand: skills the LLM called matched but string matching does not
    print("\nSample LLM 'matched' skills that did not match a student skill (check by hand):")
    shown = 0
    for pid, data in matching.items():
        mine = student_skills(profiles[pid])
        for item in data["all_scored"]:
            for m in item["matched_skills"]:
                if not any(same(m, s, True) for s in mine) and shown < 8:
                    print(f"  {pid} {item['job_id']}: '{m}'")
                    shown += 1

    OUT_PATH.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"\nSaved: {OUT_PATH}")


if __name__ == "__main__":
    main()