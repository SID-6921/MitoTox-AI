# Preliminary Studies paragraph (draft, post-verification)

We built a dataset of 8,058 chemicals from EPA's ToxCast/Tox21 program. It covers 19
mitochondrial-relevant assay endpoints. We trained three baseline models (logistic
regression, Random Forest, XGBoost) to predict mitochondrial membrane-potential disruption.
This endpoint had enough tested chemicals (7,268) to support a scaffold-based evaluation.

We split the data with a Bemis-Murcko scaffold split. This method holds out chemicals with
structurally distinct scaffolds from training. The best model (Random Forest) scored an
AUROC of 0.796 on these unseen scaffolds. Under a conventional random split, the same model
scored 0.892. This gap shows that random splitting overstates real-world performance.

Performance held when we removed active chemicals whose activity occurred at or above their
own cytotoxicity threshold (AUROC 0.797 vs. 0.796 overall). This shows the model is not
simply learning general cytotoxicity.

We built an uncertainty score from prediction disagreement across the Random Forest's trees.
Predictions with high disagreement were more likely to be wrong. Referring the most uncertain
20% of chemicals for confirmation, while keeping the other 80%, brought the error rate down
from 20.4% to 15.7%. A more conservative referral of 80% of chemicals brought the error rate
on the retained 20% down to 1.4%. At the default 0.5 threshold, sensitivity is 0.35 at
specificity 0.91. A screening-mode threshold of 0.382 reaches sensitivity 0.70 at specificity
0.76, meeting the Aim 1 milestone target.

We compared model predictions against an orthogonal Seahorse respirometry assay that
measures direct mitochondrial bioenergetic function. Concordance was weak in chemicals the
model had not seen during training (AUROC 0.47-0.56). This suggests membrane-potential
disruption and respiratory-chain dysfunction are at least partly distinct mechanisms, not one
underlying process. This finding supports Aim 2's plan to build separate mechanistic modules
instead of one composite endpoint.

An exploratory check against a small, literature-derived external dataset was consistent
with these results. The dataset was too small and too imbalanced to serve as formal
validation.

Together, these results show computational feasibility for two things: predicting
mitochondrial liability in structurally novel chemicals, and flagging predictions that need
experimental follow-up. Both capabilities are central to the proposed MitoTox AI platform.
