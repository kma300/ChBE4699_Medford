"""Eight-gas MOF sensor-array simulator, ported from the week-2 benchmark.

Source: ~/Documents/Codex/2026-09-20/we-need-to-continue-using-true/work/medford-array/benchmark.py
(frozen protocol in weeks/02/protocol_frozen.json). The numerical functions below are
copied verbatim; only file locations changed. tests/test_sensorsim.py checks that this
module reproduces the week-2 final numbers.

Model: each MOF's signal is K @ x (dilute-limit Henry coefficients times mole fractions),
plus Gaussian noise with sigma = max(1% of the MOF's largest K, 0.1% of the median largest K).
Compositions are recovered by exact nonnegative, sum-to-one least squares (SimplexLS).
"""
from __future__ import annotations
import csv, hashlib, itertools, json
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'data/dmoph25_data/final.csv'
GASES = ['methane','ethane','ethene','propane','propene','isobutane','isopentane','2-pentene']
EXPECTED_HASH = 'a748213897204191619a43c6d6c08f80e8109b943e936233a1a0bf9e96f5d938'
SEEDS = {'random_arrays':20260920,'development':20260921,'final':20260922}
def digest(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def save_json(path, obj): Path(path).write_text(json.dumps(obj, indent=2, allow_nan=False)+'\n')
def basis(n):
    b = np.zeros((n,n-1))
    for k in range(1,n):
        b[:k,k-1]=1/np.sqrt(k*(k+1)); b[k,k-1]=-k/np.sqrt(k*(k+1))
    return b
B = basis(8)

def load_data():
    assert digest(SOURCE)==EXPECTED_HASH
    with SOURCE.open() as f: rows = list(csv.DictReader(f))
    assert len(rows)==16628 and len({(r['mof'],r['mol']) for r in rows})==16628
    pairs={(r['mof'],r['mol']):float(r['K']) for r in rows if r['mol'] in GASES}
    ids=sorted({r['mof'] for r in rows if r['mol'] in GASES})
    K=np.array([[pairs[(i,g)] for g in GASES] for i in ids])
    assert K.shape==(471,8) and len(pairs)==3768 and np.isfinite(K).all() and (K>=0).all()
    g=K.max(axis=1); ref=float(np.median(g)); assert ref==0.0467015
    return np.array(ids),K,g,ref

def noise_sigma(g, ref, relative=.01, floor=.001):
    """Week-2 primary noise model: 1% of full scale with a floor of 0.1% of g_ref."""
    return np.maximum(relative*g, floor*ref)

def candidate_pool(K):
    """The 464 MOFs with any nonzero response (week-2 prepare step)."""
    pool=np.flatnonzero((K>=1e-15).any(axis=1)); assert len(pool)==464
    return pool

def design(K, sigma, ids, pool, ridge=1e-6):
    A=(K/sigma[:,None])@B
    eye=np.sqrt(ridge)*np.eye(7)
    pool=np.array(sorted(pool),dtype=int)
    def scores(subsets):
        aa=A[np.asarray(subsets)]
        aug=np.concatenate([np.broadcast_to(eye,(len(aa),7,7)),aa],axis=1)
        s=np.linalg.svd(aug,compute_uv=False)
        return 2*np.log(s).sum(axis=1)
    def best_index(vals):
        # Input candidates are lexicographically ordered; absolute tie tolerance fixed.
        return int(np.flatnonzero(vals >= vals.max()-1e-12)[0])
    selected=[]; trace=[]
    for step in range(12):
        candidates=[i for i in pool if i not in selected]
        trial=np.array([selected+[i] for i in candidates])
        values=scores(trial); j=best_index(values); selected.append(candidates[j])
        trace.append({'operation':'add','step':step+1,'added':str(ids[candidates[j]]),'score':float(values[j])})
    selected=sorted(selected); current=float(scores([selected])[0]); stopping='100_swap_limit'
    for step in range(100):
        others=[i for i in pool if i not in selected]
        trials=[]; swaps=[]
        for removed in selected:
            for added in others:
                trials.append(sorted([i for i in selected if i!=removed]+[added])); swaps.append((removed,added))
        values=scores(trials); j=best_index(values); gain=float(values[j]-current)
        if gain<=1e-8:
            stopping='no_swap_improvement_above_1e-8'; break
        selected=trials[j]; current=float(values[j]); old,new=swaps[j]
        trace.append({'operation':'swap','step':step+1,'removed':str(ids[old]),'added':str(ids[new]),'gain':gain,'score':current})
    sv=np.linalg.svd(A[selected],compute_uv=False)
    rank=int(np.linalg.matrix_rank(A[selected])); assert rank==7
    return {'indices':[int(i) for i in selected],'mofs':ids[selected].tolist(),'ridge':ridge,
            'candidate_count':len(pool),'score':current,'rank':rank,'singular_values':sv.tolist(),
            'minimum_singular_value':float(sv[-1]),'condition_number':float(sv[0]/sv[-1]),
            'stopping_reason':stopping,'trace':trace}

class SimplexLS:
    """Enumerate all 255 nonempty faces, with direct-SVD affine least squares.

    An optimal feasible face stationary point satisfies the convex problem's KKT
    conditions. Resolve faces in descending size, then lexicographic order. Every
    returned observation has feasibility and KKT checked. No response clipping.
    """
    def __init__(self,W):
        self.W=np.asarray(W); self.faces=[];self.fallback_count=0;self.max_fallback_scaled_kkt=0.
        for size in range(8,0,-1):
            for support in itertools.combinations(range(8),size):
                idx=np.array(support); wf=self.W[:,idx]; bf=basis(size)
                if size>1:
                    u,s,vt=np.linalg.svd(wf@bf,full_matrices=False)
                    keep=s>1e-13*s[0]
                    inverse=(vt[keep].T/s[keep])@u[:,keep].T
                    mapping=bf@inverse
                else: mapping=np.zeros((1,len(W)))
                offset=wf.mean(axis=1)
                self.faces.append((idx, mapping, offset))
    def solve(self,Y):
        Y=np.asarray(Y); n=len(Y); result=np.zeros((n,8)); pending=np.arange(n)
        best=np.full(n,np.inf);best_x=np.zeros((n,8))
        # Absolute tolerances in fractions and relative to weighted gradient scale.
        for idx,mapping,offset in self.faces:
            if not len(pending): break
            x=(Y[pending]-offset)@mapping.T+1/len(idx)
            feasible=(x.min(axis=1)>=-1e-10)
            loc=np.flatnonzero(feasible)
            if not len(loc): continue
            sub=np.zeros((len(loc),8)); sub[:,idx]=x[loc]
            residual=sub@self.W.T-Y[pending[loc]]
            objective=np.sum(residual**2,axis=1)
            better=objective<best[pending[loc]]
            best[pending[loc[better]]]=objective[better];best_x[pending[loc[better]]]=sub[better]
            grad=residual@self.W
            lag=grad[:,idx].mean(axis=1)
            scale=1+np.max(np.abs(Y[pending[loc]]@self.W),axis=1)
            tol=1e-12*scale
            reduced=grad-lag[:,None]
            stationary=np.max(np.abs(reduced[:,idx]),axis=1)<=tol
            inactive=np.setdiff1d(np.arange(8),idx)
            dual=np.ones(len(loc),bool) if not len(inactive) else reduced[:,inactive].min(axis=1)>=-tol
            ok=stationary & dual
            chosen=loc[ok]
            if len(chosen):
                # Remove only roundoff-level negative coefficients; preserve unit sum.
                cleaned=np.maximum(sub[ok],0); cleaned/=cleaned.sum(axis=1,keepdims=True)
                result[pending[chosen]]=cleaned
                retain=np.ones(len(pending),bool);retain[chosen]=False;pending=pending[retain]
        if len(pending):
            # Exhaustive feasible-face objective minimization is independent of
            # the early-exit stationarity tolerance. Allow finite-precision KKT
            # residuals up to 1e-9 of gradient scale, with explicit audit counts.
            assert np.isfinite(best[pending]).all()
            h=best_x[pending];gradient=(h@self.W.T-Y[pending])@self.W
            active=h>1e-9;lag=(gradient*active).sum(axis=1)/active.sum(axis=1)
            reduced=gradient-lag[:,None]
            violation=np.maximum(np.max(np.abs(reduced)*active,axis=1),np.max(np.maximum(-reduced,0)*(~active),axis=1))
            scale=1+np.max(np.abs(Y[pending]@self.W),axis=1)
            scaled=violation/scale
            if np.max(scaled)>1e-9: raise RuntimeError(f'Exhaustive solution KKT residual {np.max(scaled)}')
            self.fallback_count+=len(pending)
            self.max_fallback_scaled_kkt=max(self.max_fallback_scaled_kkt,float(scaled.max()))
            h=np.maximum(h,0);h/=h.sum(axis=1,keepdims=True);result[pending]=h
        assert (result>=0).all() and np.allclose(result.sum(axis=1),1,atol=1e-12)
        return result

def mixtures(seed):
    rng=np.random.default_rng(seed)
    X=np.zeros((1000,8)); family=np.empty(1000,dtype='U24')
    X[:500]=rng.dirichlet(np.ones(8),size=500);family[:500]='all_eight'
    for i in range(500,900):
        n=int(rng.integers(2,8)); ix=rng.choice(8,n,replace=False)
        X[i,ix]=rng.dirichlet(np.ones(n));family[i]='subset_2_to_7'
    for start,feed,product,name in [(900,1,2,'ethane_ethylene'),(950,3,4,'propane_propylene')]:
        # Independent stratified ratios span the approved 1%-99% interval in each
        # set, avoiding reusing identical stress mixtures in development/final.
        f=.01+.98*(np.arange(50)+rng.random(50))/50;X[start:start+50]=.2/6
        X[start:start+50,feed]=.8*(1-f);X[start:start+50,product]=.8*f
        family[start:start+50]=name
    assert np.allclose(X.sum(axis=1),1) and (X>=0).all()
    Z=rng.standard_normal((1000,471))
    target=np.arange(1000)%8
    drift=[]
    for delta in [.01,.05]:
        D=X.copy(); valid=X[np.arange(1000),target]+delta<=1
        factor=(1-X[np.arange(1000),target]-delta)/(1-X[np.arange(1000),target])
        D*=factor[:,None];D[np.arange(1000),target]=X[np.arange(1000),target]+delta
        D[~valid]=X[~valid]
        assert (D>=0).all() and np.allclose(D.sum(axis=1),1)
        drift.append((delta,D,rng.standard_normal((1000,471)),target,valid))
    return X,family,Z,drift

def metrics(X,H):
    err=100*np.abs(H-X); case=err.mean(axis=1)
    return {'mae_pp':float(err.mean()),'p95_mixture_mae_pp':float(np.quantile(case,.95)),
            'worst_mixture_mae_pp':float(case.max()),'maximum_component_error_pp':float(err.max()),
            'per_gas_mae_pp':dict(zip(GASES,err.mean(axis=0).tolist()))}

def qvalue(x,q=.5): return float(np.quantile(x,q)) if len(x) else None
def meanvalue(x): return float(np.mean(x)) if len(x) else None

def presence(X,H):
    rows=[]
    for j,gas in enumerate(GASES):
        real=X[:,j]>0; predicted=H[:,j]>=.01
        tp=int((real&predicted).sum());fp=int((~real&predicted).sum());fn=int((real&~predicted).sum())
        missed=100*X[real&~predicted,j]
        rows.append({'gas':gas,'tp':tp,'fp':fp,'fn':fn,'precision':tp/(tp+fp) if tp+fp else None,
            'recall':tp/(tp+fn) if tp+fn else None,'missed_true_min_pp':float(missed.min()) if len(missed) else None,
            'missed_true_max_pp':float(missed.max()) if len(missed) else None,'missed_true_median_pp':qvalue(missed)})
    tp=sum(r['tp'] for r in rows); fp=sum(r['fp'] for r in rows); fn=sum(r['fn'] for r in rows)
    micro={'precision':tp/(tp+fp),'recall':tp/(tp+fn),'tp':tp,'fp':fp,'fn':fn}
    return rows,micro

def ratios(X,H):
    rows=[]
    for feed,product,name in [(1,2,'ethylene/ethane'),(3,4,'propylene/propane')]:
        eligible=X[:,feed]>=.01;failed=eligible&(H[:,feed]<.01);valid=eligible&~failed
        actual=X[valid,product]/X[valid,feed];predicted=H[valid,product]/H[valid,feed]
        absolute=np.abs(predicted-actual);positive=actual>0
        relative=100*absolute[positive]/actual[positive]
        rows.append({'ratio':name,'true_feed_below_1pct_n':int((~eligible).sum()),'eligible_n':int(eligible.sum()),
          'estimated_feed_below_1pct_failures':int(failed.sum()),'scored_n':int(valid.sum()),
          'absolute_error_mean':meanvalue(absolute),'absolute_error_median':qvalue(absolute),
          'relative_error_mean_pct_positive_product':meanvalue(relative),
          'relative_error_median_pct_positive_product':qvalue(relative),
          'relative_error_p95_pct_positive_product':qvalue(relative,.95),
          'relative_error_scored_n':int(positive.sum()),'zero_product_n':int((~positive).sum()),
          'zero_product_absolute_ratio_error_mean':meanvalue(absolute[~positive])})
    return rows

def simulate(K, sigma, indices, X, Z):
    """Run one array through the week-2 detection experiment; returns estimated compositions."""
    ix=np.asarray(indices); W=K[ix]/sigma[ix,None]
    return SimplexLS(W).solve(X@W.T+Z[:,ix])
