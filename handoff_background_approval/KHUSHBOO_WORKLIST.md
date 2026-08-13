# Khushboo's worklist — burst by burst, working toward ALL 106

**The point of this run (Vikas, 2026-08-13):** *"she will eventually run all 106 in her
system so that we can then finally check what differences we get in different systems."*
So this is not a division of labour — it is a **replication arm**. Both systems run the
same Skill Library on the same approved Stage-1 selections; the comparison is the result.
`scripts/47_compare_systems.py` produces the diff (winner agreement, verdict agreement,
per-parameter sigma, and the divergence bins: underspecification / judgment / execution
error). Start with the post-2020 list below, then continue through the rest of the 106.
**Do not look at our results for a burst before you finish yours** — a diff is only worth
something if the runs are independent.

## Start here (post-2020)

39 bursts. The sweep has already FITTED most of them, so for those your job is the
review pass: run `scripts/45_all_products.py` to make every figure, then look. For the
rest, run the fit first (both command blocks are in KHUSHBOO_RUN_ONE_BURST.md).

Per burst, record: does each figure look right; is the winner a real preference or a tie;
any block where the models are indistinguishable; anything that looks like an artifact.

| # | burst | dets | fit done? | your action |
|---|---|---|---|---|
| 1 | `bn200227306` | n0,n1,n3,b0 | yes | products + review |
| 2 | `bn200301320` | n0,n1,n3,n4,n5,b0 | yes | products + review |
| 3 | `bn200524211` | n0,n1,n3,b0 | no | **fit**, then products + review |
| 4 | `bn200607921` | n9,n6,n7,b1 | yes | products + review |
| 5 | `bn200826923` | n1,n2,n5,b0 | yes | products + review |
| 6 | `bn201016019` | n3,n4,n5,b0 | yes | products + review |
| 7 | `bn201104001` | n6,n7,n8,b1 | yes | products + review |
| 8 | `bn201105230` | n1,n2,n5,b0 | yes | products + review |
| 9 | `bn210410037` | n6,n7,n8,b1 | yes | products + review |
| 10 | `bn210524208` | n9,na,nb,b1 | yes | products + review |
| 11 | `bn210714331` | na,nb,b1 | yes | products + review |
| 12 | `bn210723615` | n3,n4,n5,b0 | yes | products + review |
| 13 | `bn210803497` | n2,b0,na,b1 | yes | products + review |
| 14 | `bn210812699` | nb,b1 | yes | products + review |
| 15 | `bn211116586` | n2,n5,b0 | yes | products + review |
| 16 | `bn211207416` | n7,n8,nb,b1 | yes | products + review |
| 17 | `bn220525008` | n3,n4,n5,b0 | yes | products + review |
| 18 | `bn221201517` | n2,n5,b0 | yes | products + review |
| 19 | `bn221209243` | n1,n2,n5,b0 | yes | products + review |
| 20 | `bn230320884` | n2,n5,b0 | yes | products + review |
| 21 | `bn230405832` | n7,n8,nb,b1 | yes | products + review |
| 22 | `bn230409626` | n1,n2,b0,n9,na,b1 | no | **fit**, then products + review |
| 23 | `bn230614424` | na,nb,b1 | yes | products + review |
| 24 | `bn230802285` | n2,n5,b0 | yes | products + review |
| 25 | `bn230812790` | n0,n3,b0,n6,n7,b1 | no | **fit**, then products + review |
| 26 | `bn231020790` | n9,na,b1 | no | **fit**, then products + review |
| 27 | `bn231030832` | n0,n3,n4,b0,n6,b1 | no | **fit**, then products + review |
| 28 | `bn240204630` | n9,na,nb,b1 | no | **fit**, then products + review |
| 29 | `bn240403498` | n0,n1,n2,n5,b0 | no | **fit**, then products + review |
| 30 | `bn240710643` | n7,n8,nb,b1 | no | **fit**, then products + review |
| 31 | `bn241117845` | n6,n7,n8,b1 | no | **fit**, then products + review |
| 32 | `bn241223506` | n0,n1,n2,b0 | no | **fit**, then products + review |
| 33 | `bn250313607` | n0,n1,n3,b0,n6,n7,n9,b1 | no | **fit**, then products + review |
| 34 | `bn250407659` | n4,b0 | no | **fit**, then products + review |
| 35 | `bn250702413` | n6,n7,n8,n9,nb,b1 | no | **fit**, then products + review |
| 36 | `bn250814432` | n2,n5,b0 | no | **fit**, then products + review |
| 37 | `bn250902062` | n1,n2,n3,n5,b0 | no | **fit**, then products + review |
| 38 | `bn251016999` | n0,n3,n4,b0 | no | **fit**, then products + review |
| 39 | `bn260105973` | n0,n1,n2,n5,b0 | no | **fit**, then products + review |

## The one command (fit already done)
```bash
TRIG=bn200227306
python scripts/45_all_products.py --trig $TRIG --out results/sweep106/$TRIG
cat results/sweep106/$TRIG/PRODUCTS.md
```

If the fit is NOT done, run the two commands in KHUSHBOO_RUN_ONE_BURST.md section 1 first,
with `OUT=results/mine/$TRIG`, then point `45` at that same OUT.

## Order
Take them top to bottom. Bursts already fitted come first in the list, so you can start
reviewing immediately without waiting on any compute.
