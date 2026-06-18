"""
Patch scripts/11_run_sample_parallel.py per the audit:
 1. LLE local-presence + download globs must accept gll_pt_* (the filename
    3ML actually ships), not only gll_ft2_*  -> HAS_LAT bursts were all
    marked 'unavailable'.
 2. NO SHORTCUTS: remove the heuristic ai_selections fallback. Phase 2 now
    REQUIRES a real <trigger>_ai_selections.json (produced by the AI-vision
    step). If absent -> fail_no_ai_selection (never fabricate windows).
 3. Phase-3 skip gate must NOT read the shared background_intervals ECSV
    (race with concurrent atomic replaces). Gate on the per-burst bb_spec only.
 4. Force MPLBACKEND=Agg in SUBPROC_ENV so no child can block on a GUI.
 5. trigger[2:] prefix-strip (not lstrip('bn') char-strip).
Fail-safe: every replacement asserts exactly one match.
"""
import ast
P = 'scripts/11_run_sample_parallel.py'
s = open(P).read()
orig = s

def sub1(old, new):
    global s
    c = s.count(old)
    assert c == 1, f'EXPECTED 1, got {c} for:\n---\n{old}\n---'
    s = s.replace(old, new, 1)

# 1. _has_lle_locally accept gll_pt_*
sub1("    ft2 = glob.glob(os.path.join(base, 'gll_ft2_*.fit*'))\n"
     "    rsp = (glob.glob(os.path.join(base, 'gll_lle_*.rsp*'))",
     "    ft2 = (glob.glob(os.path.join(base, 'gll_ft2_*.fit*'))\n"
     "           + glob.glob(os.path.join(base, 'gll_pt_*.fit*')))\n"
     "    rsp = (glob.glob(os.path.join(base, 'gll_lle_*.rsp*'))")

# 5. prefix-strip
sub1("        trig_num = trigger.lstrip('bn')",
     "        trig_num = trigger[2:] if trigger.startswith('bn') else trigger")

# 4. MPLBACKEND=Agg
sub1("    'PYTHONUNBUFFERED': '1',",
     "    'PYTHONUNBUFFERED': '1',\n    'MPLBACKEND': 'Agg',")

# 2. NO heuristic — require real ai_selections.json
old_phase2 = """        # Phase 2 (heuristic): write ai_selections.json
        ai_path = os.path.join(LC_FOR_AI, f'{trigger}_ai_selections.json')
        if not os.path.exists(ai_path):
            with open(pending_path) as f:
                manifest = json.load(f)
            t90 = manifest.get('t90_s')
            t90_start = manifest.get('t90_start_s')
            sel = _heuristic_ai_selections(pending_path, t90, t90_start)
            with open(ai_path, 'w') as f:
                json.dump(sel, f, indent=2)
            with open(log_path, 'a') as lf:
                lf.write(f'\\n[runner] Phase 2 (heuristic): wrote {ai_path}\\n')
            result['phases']['p2'] = 'heuristic'
        else:
            result['phases']['p2'] = 'skip'"""
new_phase2 = """        # Phase 2: REQUIRE a real AI-vision ai_selections.json. No heuristic
        # fallback (no shortcuts) — the vision step must have produced it.
        ai_path = os.path.join(LC_FOR_AI, f'{trigger}_ai_selections.json')
        if not os.path.exists(ai_path):
            with open(log_path, 'a') as lf:
                lf.write(f'\\n[runner] Phase 2: MISSING {ai_path} '
                         f'- AI-vision selection not run for this burst.\\n')
            result['phases']['p2'] = 'missing_ai_selection'
            result['status'] = 'fail_no_ai_selection'
            return result
        result['phases']['p2'] = 'ai_vision'"""
sub1(old_phase2, new_phase2)

# 3. Phase-3 gate on per-burst bb_spec only (drop shared-ECSV race read)
old_p3 = """        bb_spec = os.path.join(RESULTS, f'bb_blocks_spectral_{trigger}.ecsv')
        bkg_ecsv = os.path.join(RESULTS, 'background_intervals_prototype.ecsv')
        needs_p3 = not os.path.exists(bb_spec)
        if not needs_p3 and os.path.exists(bkg_ecsv):
            t = Table.read(bkg_ecsv, format='ascii.ecsv')
            needs_p3 = not (t['TRIGGER_NAME'] == trigger).any()
        if needs_p3:"""
new_p3 = """        # Gate ONLY on the per-burst bb_spec (written atomically per trigger);
        # do NOT read the shared background_intervals ECSV here - concurrent
        # workers atomically replace it, so an unlocked read can race.
        bb_spec = os.path.join(RESULTS, f'bb_blocks_spectral_{trigger}.ecsv')
        needs_p3 = not os.path.exists(bb_spec)
        if needs_p3:"""
sub1(old_p3, new_p3)

ast.parse(s)
open(P, 'w').write(s)
print(f'Patched {P}: {len(orig)} -> {len(s)} bytes, ast OK')
