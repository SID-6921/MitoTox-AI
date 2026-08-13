# Preliminary Studies paragraph (draft, post-verification)

We built a curated dataset of 8,058 chemicals from EPA's ToxCast/Tox21 program across 19
mitochondrial-relevant assay endpoints and trained baseline machine learning models
(logistic regression, Random Forest, XGBoost) to predict mitochondrial membrane-potential
disruption, the endpoint with sufficient chemical coverage (7,268 tested chemicals) to
support a scaffold-based evaluation. Using a Bemis-Murcko scaffold-separated split, which
holds out chemicals with structurally distinct scaffolds from training, the best model
(Random Forest) achieved an AUROC of 0.796 on genuinely unseen chemical structures, compared
to 0.892 under a conventional random split, confirming that random splitting alone
overstates real-world generalization. Predictive performance was unchanged when we excluded
active chemicals whose activity occurred at or above their own cytotoxicity threshold
(AUROC 0.797 versus 0.796 overall), indicating the model is not simply learning general
cytotoxicity. We built an uncertainty-quantification component using prediction disagreement
across the Random Forest's constituent trees: predictions on which the model disagreed with
itself were significantly more likely to be wrong. Referring the most uncertain 20% of
chemicals for experimental confirmation, while retaining the remaining 80%, brought the
error rate down from 20.4% to 15.7%; a more conservative referral of 80% of chemicals
brought the error rate on the retained 20% down to 1.4%. Comparing model predictions against an
orthogonal Seahorse respirometry assay measuring direct mitochondrial bioenergetic function
showed only weak concordance in chemicals the model had not seen during training, suggesting
membrane-potential disruption and respiratory-chain dysfunction reflect at least partially
distinct mitochondrial toxicity mechanisms rather than a single underlying process - a
finding that will inform Aim 2's design of separate mechanistic modules rather than one
composite endpoint. An exploratory check against a small, literature-derived external dataset
was consistent with these results but was underpowered to serve as formal validation.
Together, these results establish computational feasibility for predicting mitochondrial
liability in structurally novel chemicals and for flagging predictions that warrant
experimental follow-up, the two capabilities central to the proposed MitoTox AI platform.
