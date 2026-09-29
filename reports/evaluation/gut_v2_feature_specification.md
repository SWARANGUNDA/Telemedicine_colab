# 🧬 Gut Dataset v2 Feature Specification & Biological Taxonomy

**Specification Date**: July 28, 2026  
**Target Taxa Count**: 20 Microbial Genera  
**Ecological Indices**: 4 Community Metrics  
**Derived Scores**: 5 Functional Microbiome Signatures  
**Transformation Pipelines**: Pipeline A (Relative Abundance %) vs Pipeline B (Centered Log-Ratio CLR)

---

## 1. Feature Specification Matrix

| Feature | Type | Biological rationale | Disease association | Expected direction/uncertainty | Evidence strength | Generation method | Model representation |
|---|---|---|---|---|---|---|---|
| `Akkermansia` | Taxon (Verrucomicrobia) | Mucus degrader, maintains gut barrier integrity & GLP-1 secretion. | T2D, Obesity, MetSyn, NAFLD | Depleted in metabolic disease; strong protective effect | High (Meta-analyses 2020-2024) | Latent Factor (Glycemic/Adiposity) | % Abundance / CLR |
| `Faecalibacterium` | Taxon (Firmicutes) | Major butyrate producer, anti-inflammatory via IL-10 induction. | T2D, Prediabetes, Obesity, MetSyn, NAFLD | Consistently depleted in dysbiosis | High (Meta-analyses) | Latent Factor (Fiber/Inflammation) | % Abundance / CLR |
| `Roseburia` | Taxon (Firmicutes) | Flagellated butyrate producer, enhances insulin sensitivity. | T2D, Obesity, NAFLD | Depleted in insulin resistance | Moderate-High | Latent Factor (Fiber Intake) | % Abundance / CLR |
| `Bifidobacterium` | Taxon (Actinobacteria) | Early colonizer, acetate/lactate producer, modulates immunity. | T2D, Prediabetes, Obesity | Depleted in high-fat diet / metabolic stress | High | Latent Factor (Dietary Quality) | % Abundance / CLR |
| `Bacteroides` | Taxon (Bacteroidetes) | Glycan degradation, propionate producer; complex strain variation. | Obesity, T2D, NAFLD | Context-dependent; higher in western diet | Moderate (Heterogeneous) | Latent Factor (Fat/Protein Diet) | % Abundance / CLR |
| `Prevotella` | Taxon (Bacteroidetes) | Complex carbohydrate degrader; enterotype marker. | Obesity, T2D | High variance; protective in high-fiber, inflammatory in high-fat | High (Context-dependent) | Latent Factor (Diet/Carb) | % Abundance / CLR |
| `Ruminococcus` | Taxon (Firmicutes) | Resistant starch degrader, SCFA producer. | T2D, NAFLD | Depleted in low-fiber intake | Moderate | Latent Factor (Starch/Fiber) | % Abundance / CLR |
| `Blautia` | Taxon (Firmicutes) | Acetogen, produces acetate; correlated with visceral fat. | Obesity, MetSyn | Weakly enriched in obesity, context-dependent | Moderate | Latent Factor (Adiposity) | % Abundance / CLR |
| `Collinsella` | Taxon (Actinobacteria) | Modifies bile acids, increases intestinal permeability. | T2D, NAFLD, MetSyn | Enriched in metabolic syndrome / liver fat | High | Latent Factor (Bile Acid/Fat) | % Abundance / CLR |
| `Escherichia_Shigella` | Taxon (Proteobacteria) | Pathobiont, LPS producer, drives low-grade inflammation. | T2D, NAFLD, MetSyn | Enriched in metabolic dysbiosis & systemic inflammation | High | Latent Factor (Inflammation) | % Abundance / CLR |
| `Coprococcus` | Taxon (Firmicutes) | Butyrate producer, associated with positive mood & metabolic health. | T2D, Prediabetes | Depleted in metabolic disease | Moderate | Latent Factor (Fiber/Health) | % Abundance / CLR |
| `Alistipes` | Taxon (Bacteroidetes) | Indole/sulfonate producer, bile-resistant. | NAFLD, Obesity | Protective against liver inflammation | Moderate | Latent Factor (Bile/Liver) | % Abundance / CLR |
| `Subdoligranulum` | Taxon (Firmicutes) | Closely related to *Faecalibacterium*, butyrate producer. | Obesity, Prediabetes | Depleted in impaired glucose tolerance | Moderate | Latent Factor (Glycemic) | % Abundance / CLR |
| `Enterococcus` | Taxon (Firmicutes) | Opportunistic pathobiont, drives intestinal inflammation. | T2D, NAFLD | Enriched in advanced dysbiosis | Moderate | Latent Factor (Inflammation) | % Abundance / CLR |
| `Eubacterium` | Taxon (Firmicutes) | Bile acid transformation, butyrate synthesis. | MetSyn, T2D | Depleted in metabolic syndrome | Moderate | Latent Factor (Metabolic) | % Abundance / CLR |
| `Parabacteroides` | Taxon (Bacteroidetes) | Succinate/acetate producer, anti-inflammatory. | Obesity, T2D | Depleted in obesity & hyperglycemia | Moderate | Latent Factor (Adiposity) | % Abundance / CLR |
| `Lactobacillus` | Taxon (Firmicutes) | Lactic acid producer; widely used as probiotic. | Obesity, T2D | Variable/Enriched in T2D, context-dependent | High (Heterogeneous) | Latent Factor (Lactate/Diet) | % Abundance / CLR |
| `Klebsiella` | Taxon (Proteobacteria) | Endotoxin producer, translocation into portal circulation. | NAFLD, T2D | Enriched in liver steatosis / systemic endotoxemia | High | Latent Factor (Liver Stress) | % Abundance / CLR |
| `Streptococcus` | Taxon (Firmicutes) | Oral-gut translocation taxon, drives low-grade inflammation. | T2D, NAFLD | Enriched in systemic inflammation | Moderate | Latent Factor (Translocation) | % Abundance / CLR |
| `Eggerthella` | Taxon (Actinobacteria) | Polyamine synthesis, linked with cardiac & metabolic risk. | MetSyn, T2D | Enriched in metabolic syndrome | Moderate | Latent Factor (Cardiometabolic) | % Abundance / CLR |
| `Shannon_Diversity_Index` | Ecological | Alpha-diversity (richness & evenness). | All Diseases | Reduced in dysbiosis / metabolic disease | High | Mathematical (from taxa vector) | Continuous |
| `Simpson_Diversity_Index` | Ecological | Probability that 2 individuals belong to different species. | All Diseases | Reduced in dominance by pathobionts | High | Mathematical ($1 - \sum p_i^2$) | Continuous |
| `Observed_Richness` | Ecological | Count of taxa present above detection threshold ($>0.01\%$). | Dysbiosis | Lower in restricted diets / disease | Moderate | Mathematical ($\sum \mathbb{I}(p_i > 0.01\%)$) | Integer / Cont. |
| `Pielou_Evenness` | Ecological | Equitability of abundance distribution across taxa. | Dysbiosis | Lower when few pathobionts dominate | Moderate | Mathematical ($\frac{H'}{\ln S}$) | Continuous |
| `SCFA_Producer_Score` | Functional | Composite abundance of SCFA-producing taxa. | T2D, Obesity | Depleted in insulin resistance | High | Weighted Sum (*Faec*, *Rose*, *Bif*, *Rum*, *Copr*, *Eub*) | Continuous |
| `Butyrate_Producer_Score` | Functional | Composite abundance of specific butyrate synthesizers. | T2D, NAFLD | Depleted in intestinal hyperpermeability | High | Weighted Sum (*Faec*, *Rose*, *Copr*, *Subd*) | Continuous |
| `Barrier_Support_Score` | Functional | Mucus layer & tight-junction maintenance score. | NAFLD, T2D | Depleted in systemic endotoxemia | High | Weighted Sum (*Akker*, *Faec*, *Bif*) | Continuous |
| `Inflammatory_Dysbiosis_Score` | Functional | Proteobacteria & pathobiont enrichment index. | All Diseases | Enriched in metabolic inflammation | High | Weighted Sum (*Esch*, *Coll*, *Entero*, *Kleb*, *Strep*) | Continuous |
| `Firmicutes_Bacteroidetes_Ratio` | Experimental | Ratio of Firmicutes to Bacteroidetes abundances. | Obesity | Controversial; experimental feature only | Low-Moderate (Controversial) | Ratio ($\sum \text{Firm} / \sum \text{Bact}$) | Continuous Log Ratio |

---

## 2. Compositional Data Handling (CLR Transformation)

Microbial relative abundances inherently constrain sum-to-100%, inducing spurious negative correlations if standard Euclidean metrics are applied directly.

### Centered Log-Ratio (CLR) Definition
For a compositional vector of relative abundances $\mathbf{x} = (x_1, x_2, \dots, x_D)$ with pseudocount $\epsilon = 10^{-5}$:
$$ g(\mathbf{x}) = \left( \prod_{i=1}^D (x_i + \epsilon) \right)^{1/D} $$
$$ \text{CLR}(x_i) = \ln \left( \frac{x_i + \epsilon}{g(\mathbf{x})} \right) $$

- **Pipeline A**: Raw relative abundances $x_i \in [0, 100]$.
- **Pipeline B**: Transformed CLR features $\text{CLR}(x_i) \in \mathbb{R}^D$.
- **Note**: Ecological diversity indices ($H', D, S, J'$) and functional scores are computed directly from relative abundances $x_i$ prior to CLR transformation to preserve mathematical consistency.
