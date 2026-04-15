"""Test script: run TSP statistical pipeline and print results."""
import django
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dss_project.settings')
django.setup()

from core.utils.tsp_db import solve_routes_from_db

print("=" * 60)
print("  RUNNING TSP PIPELINE TEST")
print("=" * 60)

result = solve_routes_from_db()

if result.get('error'):
    print(f"ERROR: {result['error']}")
else:
    print("\n=== ALGORITHMS ===")
    for k, v in result['algorithms'].items():
        best_flag = " * BEST" if v.get('is_best') else ""
        print(f"  {k}: {v['total_km']} km{best_flag}")

    print(f"\n=== STAT BEST ALGORITHM: {result['stat_best_algo']} ===")

    print(f"\n=== PAIRWISE T-TEST ({len(result['stat_pairwise'])} pairs) ===")
    for p in result['stat_pairwise']:
        sig = "***" if p['p_value'] < 0.05 else "   "
        print(f"  {sig} {p['Algo_A']:>5} vs {p['Algo_B']:>5}: "
              f"Mean({p['Mean_A']:.4f} vs {p['Mean_B']:.4f}) "
              f"p={p['p_value']:.6f} -> {p['Winner']}")

    print(f"\n=== SUMMARY (WINS) ===")
    for s in result['stat_summary']:
        best_flag = " *" if s['Algorithm'] == result['stat_best_algo'] else ""
        print(f"  {s['Algorithm']:>5}: {s['Wins']} wins{best_flag}")

    print(f"\n=== EXCEL FILE ===")
    print(f"  Exists: {os.path.exists('tsp_results.xlsx')}")

    # Print conclusion (ASCII-safe)
    conclusion = result.get('stat_conclusion', '')
    try:
        print(f"\n=== CONCLUSION ===")
        print(f"  {conclusion}")
    except UnicodeEncodeError:
        print(f"  (Conclusion contains non-ASCII chars, see Excel for details)")

print("\n" + "=" * 60)
print("  TEST COMPLETE")
print("=" * 60)
