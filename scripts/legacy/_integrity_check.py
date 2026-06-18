"""Integrity snapshot of the three pipeline scripts after the --accept-low edits.
Writes a clean report to /tmp/integrity.txt (read that, not stdout)."""
import ast, hashlib, json

files = {
    '00': 'scripts/00_prototype_one_burst.py',
    '10': 'scripts/10_spectral_fit_burst.py',
    '11': 'scripts/11_run_sample_parallel.py',
}
rep = {}
for k, p in files.items():
    s = open(p).read()
    try:
        ast.parse(s); parse = 'OK'
    except Exception as e:
        parse = f'FAIL: {e}'
    rep[k] = {
        'parse': parse,
        'lines': s.count('\n') + 1,
        'md5': hashlib.md5(s.encode()).hexdigest()[:12],
    }

s00 = open(files['00']).read()
rep['00_checks'] = {
    'accept_low_arg': "p.add_argument('--accept-low'" in s00,
    'accept_low_param': 'accept_low=False):' in s00,
    'accept_low_wired': 'accept_low=args.accept_low' in s00,
    'auto_accept_branch': "_conf != 'low' or accept_low" in s00,
    'def_phase3': s00.count('def phase3_post_ai'),
    'def_main': s00.count('def main()'),
    'plt_show_block': s00.count('plt.show(block=True)'),
}
s11 = open(files['11']).read()
rep['11_checks'] = {
    'accept_low_passed': '--accept-low' in s11,
    'auto_approve_call': "'--auto-approve'" in s11,
    'def_worker': s11.count('def worker('),
}
open('/tmp/integrity.txt', 'w').write(json.dumps(rep, indent=1))
print('done')
