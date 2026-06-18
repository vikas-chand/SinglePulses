import warnings; warnings.filterwarnings('ignore')
import numpy as np, json
from astropy.table import Table


def main():
    am = Table.read('results/sample_all_models.ecsv', format='ascii.ecsv')
    SINGLE = {'Band': 'BAND', 'CPL': 'CPL', 'SBPL': 'SBPL'}
    TB = {'DSBPL': 'DSBPL'}
    TH = {'Band+BB': 'BANDBB', 'CPL+BB': 'CPLBB'}

    def a(r, p):
        c = f'{p}_AIC'
        return float(r[c]) if (c in r.colnames and np.isfinite(r[c])) else np.inf

    def best(r, g):
        v = {n: a(r, p) for n, p in g.items()}
        k = min(v, key=v.get)
        return k, v[k]

    rows = []
    for r in am:
        _, sa = best(r, SINGLE)
        tbn, tba = best(r, TB)
        thn, tha = best(r, TH)
        ca = min(tba, tha)
        if not (np.isfinite(ca) and np.isfinite(sa)):
            continue
        if sa - ca > 6:
            d = tba - tha
            v = 'DEGEN' if abs(d) < 4 else ('2break' if d < 0 else 'thermal')
            rows.append([str(r['TRIGGER_NAME']), int(r['BLOCK']),
                         round(sa - ca, 1), round(tba, 1), round(tha, 1), v])
    rows.sort(key=lambda x: -x[2])
    with open('/tmp/curv_top.json', 'w') as f:
        json.dump(rows[:18], f)


if __name__ == '__main__':
    main()
