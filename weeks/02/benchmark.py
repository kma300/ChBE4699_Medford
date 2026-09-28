"""Approved D-MOPH eight-gas benchmark; deterministic, no source mutations."""
from __future__ import annotations
import argparse, csv, hashlib, itertools, json, platform, time
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path('/Users/lqod/Documents/Codex/2026-09-20/we-need-to-continue-using-true')
OUT = ROOT / 'outputs/medford-array'
WORK = ROOT / 'work/medford-array'
SOURCE = Path('/Users/lqod/Desktop/Projects/ChBE4699_Medford/data/dmoph25_data/final.csv')
GASES = ['methane','ethane','ethene','propane','propene','isobutane','isopentane','2-pentene']
EXPECTED_HASH = 'a748213897204191619a43c6d6c08f80e8109b943e936233a1a0bf9e96f5d938'
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

def drift_metrics(X,H,D,HD,target,valid,delta):
    truth=D[valid]-X[valid]; inferred=HD[valid]-H[valid]
    err=100*np.abs(inferred-truth); change=100*inferred[np.arange(valid.sum()),target[valid]]
    targeterr=np.abs(change-100*delta)
    return {'delta_pp':100*delta,'feasible_n':int(valid.sum()),'infeasible_n':int((~valid).sum()),
            'all_component_change_mae_pp':float(err.mean()),'target_change_mae_pp':float(targeterr.mean()),
            'target_change_error_p95_pp':float(np.quantile(targeterr,.95)),
            'target_estimated_change_mean_pp':float(change.mean()),
            'target_positive_change_fraction':float((change>1e-10).mean())}

def validate_solver():
    from scipy.optimize import minimize
    import scipy
    ids,K,g,ref=load_data();sigma=np.maximum(.01*g,.001*ref)
    designs=json.loads((OUT/'array_designs.json').read_text());primary=np.array(designs['primary']['indices'])
    rr=np.load(WORK/'random_arrays.npy');conds=np.array([np.linalg.cond((K[ix]/sigma[ix,None])@B) for ix in rr])
    X,f,Z,dr=mixtures(20260921)
    cases=np.array([0,7,23,52,151,299,498,499,500,501,517,599,650,701,799,850,899,900,924,949,950,974,999])
    checks=[];noiseless=[]
    for name,ix in [('primary',primary),('random_0',rr[0]),('most_ill_conditioned_random',rr[int(conds.argmax())])]:
        W=K[ix]/sigma[ix,None]; solver=SimplexLS(W)
        Y=X[cases]@W.T+Z[cases][:,ix]; H=solver.solve(Y)
        gap=[]; diff=[];success=[]
        for y,h in zip(Y,H):
            objective=lambda x: .5*float(np.sum((W@x-y)**2))
            jac=lambda x: W.T@(W@x-y)
            opt=minimize(objective,np.ones(8)/8,jac=jac,method='SLSQP',bounds=[(0,1)]*8,
                constraints=[{'type':'eq','fun':lambda x:np.sum(x)-1,'jac':lambda x:np.ones(8)}],
                options={'ftol':1e-11,'maxiter':2000})
            # Independent method may report a line-search warning at its solution.
            # Require feasible output and objective agreement; record its status.
            assert abs(opt.x.sum()-1)<1e-8 and opt.x.min()>-1e-8
            gap.append(abs(objective(h)-objective(opt.x)))
            diff.append(float(np.max(np.abs(h-opt.x))))
            success.append(bool(opt.success))
        assert max(gap)<1e-6
        checks.append({'array':name,'n':len(cases),'max_abs_objective_difference':max(gap),
                       'max_abs_fraction_difference':max(diff),'slsqp_success_count':sum(success),
                       'slsqp_nonsuccess_count':len(success)-sum(success)})
        known=np.vstack([X,np.eye(8)])
        recovered=solver.solve(known@W.T)
        error=float(np.max(np.abs(recovered-known)))
        assert error<1e-7
        noiseless.append({'array':name,'mixtures_including_pure_vertices':len(known),'max_abs_fraction_error':error})
    # Analytically solvable simplex projection: negative observations remain signed.
    W=np.vstack([np.eye(8),np.zeros((4,8))]); y=np.array([[2.,-1,0,0,0,0,0,0,0,0,0,0]])
    h=SimplexLS(W).solve(y);assert np.allclose(h,np.eye(8)[[0]],atol=1e-12)
    result={'independent_method':'scipy.optimize.minimize SLSQP with analytic gradient, uniform initial estimate',
            'scipy_version':scipy.__version__,'development_seed':20260921,'checks':checks,
            'noiseless_checks':noiseless,'analytic_signed_observation_check':'passed',
            'final_set_generated':False,'all_checks_passed':True}
    save_json(OUT/'solver_validation.json',result)
    print(json.dumps(result,indent=2),flush=True)

def evaluate(stage):
    assert stage in ['development','final']
    if stage=='final':
        freeze=json.loads((OUT/'protocol_frozen.json').read_text())
        assert digest(__file__)==freeze['benchmark_script_sha256']
        assert json.loads((OUT/'solver_validation.json').read_text())['all_checks_passed']
    ids,K,g,ref=load_data();sigma=np.maximum(.01*g,.001*ref)
    seed=20260921 if stage=='development' else 20260922
    X,f,Z,dr=mixtures(seed)
    if stage=='final':
        development_true=np.load(WORK/'development_predictions.npz')['true']
        assert len(np.unique(np.vstack([X,development_true]),axis=0))==2000
    choices=json.loads((OUT/'array_designs.json').read_text())
    primary=np.array(choices['primary']['indices']);rr=np.load(WORK/'random_arrays.npy')
    designlist=[('selected',primary)]+[(f'random_{i:03d}',ix) for i,ix in enumerate(rr)]
    rows=[];pres=[];rat=[];drifts=[];primary_details={}
    all_H=[]
    for num,(name,ix) in enumerate(designlist):
        W=K[ix]/sigma[ix,None];solver=SimplexLS(W)
        Y=X@W.T+Z[:,ix];H=solver.solve(Y)
        all_H.append(H)
        m=metrics(X,H);pp,micro=presence(X,H);ratios_list=ratios(X,H)
        sv=np.linalg.svd(W@B,compute_uv=False)
        rows.append({'array':name,'stage':stage,'rank':int(np.linalg.matrix_rank(W@B)),
            'condition_number':float(sv[0]/sv[-1]),'minimum_singular_value':float(sv[-1]),
            **{k:v for k,v in m.items() if k!='per_gas_mae_pp'},
            **{f'{gas}_mae_pp':v for gas,v in m['per_gas_mae_pp'].items()},
            'presence_precision':micro['precision'],'presence_recall':micro['recall']})
        pres.extend([{'array':name,**r} for r in pp]);rat.extend([{'array':name,**r} for r in ratios_list])
        for delta,D,ZD,target,valid in dr:
            HD=solver.solve(D@W.T+ZD[:,ix])
            dm=drift_metrics(X,H,D,HD,target,valid,delta)
            drifts.append({'array':name,'gas_changed':'balanced_cycle_all_8',**dm})
            if num==0:
                for j,gas in enumerate(GASES):
                    which=target==j
                    drifts.append({'array':name,'gas_changed':gas,**drift_metrics(X[which],H[which],D[which],HD[which],target[which],valid[which],delta)})
        if num==0:
            primary_details={'overall':m,'by_family':{family:metrics(X[f==family],H[f==family]) for family in sorted(set(f))},
                             'presence_per_gas':pp,'presence_micro':micro,'ratios':ratios_list}
            pred=pd.DataFrame({'mixture_id':np.arange(1000),'family':f})
            for j,gas in enumerate(GASES):pred[f'true_{gas}']=X[:,j];pred[f'estimated_{gas}']=H[:,j]
            pred['mixture_mae_pp']=100*np.abs(H-X).mean(axis=1)
            pred.to_csv(OUT/f'{stage}_selected_predictions.csv',index=False,float_format='%.17g')
        rows[-1]['exhaustive_fallback_n_across_base_and_drift']=solver.fallback_count
        rows[-1]['max_fallback_scaled_kkt']=solver.max_fallback_scaled_kkt
        if num%50==0:print(f'{stage}: evaluated {num+1}/201 arrays',flush=True)
    df=pd.DataFrame(rows);df.to_csv(OUT/f'{stage}_array_metrics.csv',index=False,float_format='%.17g')
    pd.DataFrame(pres).to_csv(OUT/f'{stage}_presence_metrics.csv',index=False,float_format='%.17g')
    pd.DataFrame(rat).to_csv(OUT/f'{stage}_ratio_metrics.csv',index=False,float_format='%.17g')
    pd.DataFrame(drifts).to_csv(OUT/f'{stage}_drift_metrics.csv',index=False,float_format='%.17g')
    np.savez_compressed(WORK/f'{stage}_predictions.npz',true=X,family=f,predicted=np.array(all_H))
    random_mae=df.loc[df.array!='selected','mae_pp'].to_numpy();selected_mae=rows[0]['mae_pp']
    summary={'stage':stage,'seed':seed,'mixtures':1000,'primary':primary_details,
      'random_baseline':{'n':200,'mae_pp_min':float(random_mae.min()),'mae_pp_p05':qvalue(random_mae,.05),
          'mae_pp_median':qvalue(random_mae),'mae_pp_p95':qvalue(random_mae,.95),'mae_pp_max':float(random_mae.max()),
          'selected_better_than_n':int((selected_mae<random_mae).sum()),
          'selected_mae_reduction_vs_random_median_pct':100*(1-selected_mae/np.median(random_mae))},
      'primary_drift':[r for r in drifts if r['array']=='selected'],
      'source_unchanged':digest(SOURCE)==EXPECTED_HASH}
    if stage=='final':
        noises=[]
        for rel,floor in itertools.product([.001,.01,.05],[0,.001,.01]):
            sig=np.maximum(rel*g,floor*ref);W=K[primary]/sig[primary,None]
            H=SimplexLS(W).solve(X@W.T+Z[:,primary]);mm=metrics(X,H)
            noises.append({'relative_full_scale_noise':rel,'floor_fraction_of_g_ref':floor,**{k:v for k,v in mm.items() if k!='per_gas_mae_pp'},
                           **{f'{gas}_mae_pp':v for gas,v in mm['per_gas_mae_pp'].items()}})
        W=K[primary]/sigma[primary,None];H=SimplexLS(W).solve(X@W.T);mm=metrics(X,H)
        noises.append({'relative_full_scale_noise':0,'floor_fraction_of_g_ref':0,**{k:v for k,v in mm.items() if k!='per_gas_mae_pp'},
                       **{f'{gas}_mae_pp':v for gas,v in mm['per_gas_mae_pp'].items()}})
        assert np.max(np.abs(H-X))<1e-7
        pd.DataFrame(noises).to_csv(OUT/'final_noise_sensitivity.csv',index=False,float_format='%.17g')
        summary['noise_sensitivity']=noises
        summary['noiseless_max_abs_fraction_error']=float(np.max(np.abs(H-X)))
        summary['design_sensitivity']={name:{'overlap_with_primary':len(set(v['mofs'])&set(choices['primary']['mofs'])),
              'same_array':v['mofs']==choices['primary']['mofs'],'condition_number':v['condition_number']} for name,v in choices.items()}
        assert all(v['same_array'] for v in summary['design_sensitivity'].values())
    save_json(OUT/f'{stage}_summary.json',summary)
    print(json.dumps({'stage':stage,'primary':primary_details['overall'],'random':summary['random_baseline']},indent=2),flush=True)

def freeze_protocol():
    dev=json.loads((OUT/'development_summary.json').read_text())
    assert dev['stage']=='development' and json.loads((OUT/'solver_validation.json').read_text())['all_checks_passed']
    p={'study':'Eight-gas ethylene-cracker synthetic dilute-limit benchmark',
       'authorization':'Ken approved the plain-language experiment proposal: yes sounds good.',
       'benchmark_script_sha256':digest(__file__),'source_sha256':EXPECTED_HASH,
       'designs_sha256':digest(OUT/'array_designs.json'),'random_membership_sha256':digest(OUT/'random_array_membership.csv'),
       'selected_mofs':json.loads((OUT/'array_designs.json').read_text())['primary']['mofs'],
       'gases':GASES,'temperature_K':300,'K_units':'mol kg^-1 Pa^-1',
       'model':'Ideal additive molar uptake slope K @ x, sum(x)=1, x>=0; total represented eight-gas composition only.',
       'g_ref':.0467015,'primary_relative_full_scale_noise':.01,'primary_common_floor_fraction_of_g_ref':.001,
       'seeds':{'random_arrays':20260920,'development':20260921,'final':20260922},
       'mixture_counts_per_set':{'all_eight_dirichlet_ones':500,'subsets_2_through_7':400,'feed_product_stress_each_pair':50},
       'feed_product_stress_sampling':'50 equal-width ratio bins over product share 1%-99%, one uniform draw per bin, independently per set; pair occupies 80% of mixture.',
       'drift':'One target per mixture, target index = mixture index mod 8; +1 and +5 pp; proportional rescaling of other gases; infeasible cases excluded and counted. Independent post-change Gaussian noise; base noise reused as before-change observation. Same noise per MOF and case across arrays.',
       'solver':'All simplex faces, descending support size; direct SVD affine least squares; pseudoinverse relative singular cutoff 1e-13; feasibility tolerance 1e-10; early-exit KKT tolerance 1e-12*(1+max(abs(Y@W))). If no early certificate, choose the minimum residual over every feasible face, require scaled KKT<=1e-9 and record fallback count. Only roundoff negative fraction cleanup, no observation clipping.',
       'selection':'Greedy 12, best one-for-one swaps; improvement >1e-8, maximum 100; SVD logdet with ridge1e-6; alphabetical ties at absolute1e-12.',
       'presence':'Estimate>=1% vs true>0; precision/recall, missed true ranges, no physical detection limit.',
       'ratio':'True feed>=1%; estimated feed<1% is failure; score remaining ratios with explicit denominator; relative error only for true positive product.',
       'final_set_generated_before_freeze':False,'settings_changed_after_final':False,
       'development_implementation_notes':['Infeasible composition changes are skipped as specified; implementation corrected before freezing.',
           'Stress ratios use independent stratified draws instead of a repeated deterministic grid; this preserves the specified range and avoids identical development/final mixtures. Development rerun before freezing.'],
       'versions':{'python':platform.python_version(),'numpy':np.__version__,'pandas':pd.__version__}}
    save_json(OUT/'protocol_frozen.json',p);print('Protocol frozen before final-set generation',flush=True)

def prepare():
    ids,K,g,ref=load_data();sigma=np.maximum(.01*g,.001*ref)
    pool=np.flatnonzero((K>=1e-15).any(axis=1));assert len(pool)==464
    choices={}
    variants=[('primary',pool,1e-6),('ridge_1e-8',pool,1e-8),('ridge_1e-4',pool,1e-4),
              ('all_471',np.arange(471),1e-6),('without_GOMREG_GOMRAC',np.array([i for i in pool if ids[i] not in ['GOMREG','GOMRAC']]),1e-6)]
    for name,p,r in variants:
        t=time.time();choices[name]=design(K,sigma,ids,p,r)
        print(name,json.dumps({k:choices[name][k] for k in ['mofs','score','condition_number','minimum_singular_value']}),f'{time.time()-t:.2f}s',flush=True)
    rng=np.random.default_rng(20260920)
    random=np.array([sorted(rng.choice(pool,12,replace=False).tolist()) for _ in range(200)])
    assert len({tuple(r) for r in random})==200
    save_json(OUT/'array_designs.json',choices)
    pd.DataFrame({'array_id':np.repeat(np.arange(200),12),'mof':ids[random.ravel()]}).to_csv(OUT/'random_array_membership.csv',index=False)
    np.save(WORK/'random_arrays.npy',random)
    primary=choices['primary']['indices']
    table=pd.DataFrame(K[primary],columns=GASES);table.insert(0,'mof',ids[primary]);table['primary_sigma']=sigma[primary]
    table.to_csv(OUT/'selected_12_mofs.csv',index=False,float_format='%.17g')
    pd.DataFrame({'mof':ids,'excluded_all_eight_K_below_1e_minus15':~np.isin(np.arange(471),pool)}).to_csv(OUT/'candidate_screen.csv',index=False)
    print('Preparation complete',flush=True)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('stage',choices=['prepare','validate','development','freeze','final']);args=ap.parse_args()
    if args.stage=='prepare':prepare()
    elif args.stage=='validate':validate_solver()
    elif args.stage=='freeze':freeze_protocol()
    else:evaluate(args.stage)
