"""
validate_latent_matrix.py — Find Nearest Valid Positive Definite Correlation Matrix.
"""

import numpy as np

def nearPD(A, nit=100):
    """Higham's nearest positive definite matrix algorithm."""
    n = A.shape[0]
    W = np.identity(n)
    delta_S = np.zeros((n, n))
    Y = A.copy()
    for k in range(nit):
        R = Y - delta_S
        # Eigendecomposition
        vals, vecs = np.linalg.eigh(R)
        vals = np.maximum(vals, 1e-6)
        X = vecs @ np.diag(vals) @ vecs.T
        delta_S = X - R
        Y = X.copy()
        # Enforce unit diagonal
        np.fill_diagonal(Y, 1.0)
    return Y

def validate_matrix():
    # 11 Latent Factors:
    # 0: L_glyc, 1: L_IR, 2: L_adip, 3: L_visc, 4: L_vasc, 5: L_dyslip, 
    # 6: L_hep,  7: L_infl, 8: L_fit,  9: L_auto, 10: L_dysb

    R = np.eye(11)

    # Off-diagonal correlations based on physiology:
    R[0, 1] = R[1, 0] = 0.55 # L_glyc <-> L_IR
    R[0, 2] = R[2, 0] = 0.35 # L_glyc <-> L_adip
    R[0, 3] = R[3, 0] = 0.45 # L_glyc <-> L_visc
    R[0, 5] = R[5, 0] = 0.30 # L_glyc <-> L_dyslip
    R[0, 6] = R[6, 0] = 0.25 # L_glyc <-> L_hep
    R[0, 7] = R[7, 0] = 0.25 # L_glyc <-> L_infl
    R[0, 8] = R[8, 0] = -0.30# L_glyc <-> L_fit
    R[0, 10] = R[10, 0] = 0.30# L_glyc <-> L_dysb

    R[1, 2] = R[2, 1] = 0.40 # L_IR <-> L_adip
    R[1, 3] = R[3, 1] = 0.50 # L_IR <-> L_visc
    R[1, 5] = R[5, 1] = 0.35 # L_IR <-> L_dyslip
    R[1, 6] = R[6, 1] = 0.40 # L_IR <-> L_hep
    R[1, 7] = R[7, 1] = 0.30 # L_IR <-> L_infl
    R[1, 8] = R[8, 1] = -0.35# L_IR <-> L_fit

    R[2, 3] = R[3, 2] = 0.65 # L_adip <-> L_visc
    R[2, 4] = R[4, 2] = 0.30 # L_adip <-> L_vasc
    R[2, 5] = R[5, 2] = 0.35 # L_adip <-> L_dyslip
    R[2, 8] = R[8, 2] = -0.45# L_adip <-> L_fit

    R[3, 4] = R[4, 3] = 0.35 # L_visc <-> L_vasc
    R[3, 5] = R[5, 3] = 0.45 # L_visc <-> L_dyslip
    R[3, 6] = R[6, 3] = 0.50 # L_visc <-> L_hep
    R[3, 7] = R[7, 3] = 0.35 # L_visc <-> L_infl
    R[3, 8] = R[8, 3] = -0.40# L_visc <-> L_fit
    R[3, 10] = R[10, 3] = 0.30# L_visc <-> L_dysb

    R[4, 5] = R[5, 4] = 0.25 # L_vasc <-> L_dyslip
    R[4, 9] = R[9, 4] = 0.35 # L_vasc <-> L_auto

    R[5, 6] = R[6, 5] = 0.45 # L_dyslip <-> L_hep
    R[5, 7] = R[7, 5] = 0.30 # L_dyslip <-> L_infl

    R[6, 7] = R[7, 6] = 0.35 # L_hep <-> L_infl
    R[6, 10] = R[10, 6] = 0.25# L_hep <-> L_dysb

    R[7, 8] = R[8, 7] = -0.30# L_infl <-> L_fit
    R[7, 9] = R[9, 7] = 0.25 # L_infl <-> L_auto
    R[7, 10] = R[10, 7] = 0.40# L_infl <-> L_dysb

    R[8, 9] = R[9, 8] = -0.35# L_fit <-> L_auto
    R[8, 10] = R[10, 8] = -0.25# L_fit <-> L_dysb

    R[9, 10] = R[10, 9] = 0.20# L_auto <-> L_dysb

    # Eigenvalues
    eigvals = np.linalg.eigvalsh(R)
    is_psd = np.all(eigvals > 0)

    if not is_psd:
        R = nearPD(R)
        eigvals = np.linalg.eigvalsh(R)
        is_psd = np.all(eigvals > 0)

    print("=== 11x11 LATENT CORRELATION MATRIX VALIDATION ===")
    print(f"Symmetric: {np.allclose(R, R.T)}")
    print(f"Diagonal = 1.0: {np.allclose(np.diag(R), 1.0)}")
    print(f"In Bounds [-1, 1]: {np.all((R >= -1.0) & (R <= 1.0))}")
    print(f"Positive Definite: {is_psd}")
    print(f"Minimum Eigenvalue: {np.min(eigvals):.6f}")
    print(f"Maximum Eigenvalue: {np.max(eigvals):.6f}\n")
    print("Matrix R:")
    print(np.round(R, 3))

if __name__ == "__main__":
    validate_matrix()
