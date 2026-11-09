"""Shared forecast contract. No table rank, form or momentum enters a candidate."""
import math
from datetime import date

import numpy as np
from scipy.optimize import minimize, minimize_scalar

VERSION = '1.0.0'
FLOOR = 1e-15


def outcome(m):
    return 0 if m['hg'] > m['ag'] else 2 if m['hg'] < m['ag'] else 1


def metadata(kind, history):
    return dict(model_id=kind, model_version=f'{kind}-{VERSION}',
                trained_through=max((m['date'] for m in history), default=None),
                training_sample_size=len(history))


def goal_rates(model, home, away):
    h, a = model['teams'].index(home), model['teams'].index(away)
    return (math.exp(model['intercept'] + model['home_advantage'] + model['attack'][h] - model['defence'][a]),
            math.exp(model['intercept'] + model['attack'][a] - model['defence'][h]))


def rho_bounds(rates):
    """Strictly interior valid tau region for every permitted ordered team pair."""
    lower = max(max(-1/h, -1/a) for h,a in rates)
    upper = min(min(1/(h*a), 1) for h,a in rates)
    return lower+1e-9, upper-1e-9


def tau(hg, ag, lh, la, rho):
    if hg == 0 and ag == 0: return 1-lh*la*rho
    if hg == 1 and ag == 0: return 1+la*rho
    if hg == 0 and ag == 1: return 1+lh*rho
    if hg == 1 and ag == 1: return 1-rho
    return 1.


def fit_goals(history, names, penalty=8, half_life=120, dc=False):
    if not history: raise ValueError('No training data')
    n = len(names); idx = {name:i for i,name in enumerate(names)}
    # N-1 free effects with final effect equal to negative sum: exact identifiability.
    contrast = np.vstack([np.eye(n-1), -np.ones(n-1)])
    X = np.zeros((2*len(history), 2+2*(n-1))); y=[]; weights=[]
    last = date.fromisoformat(max(m['date'] for m in history))
    for i,m in enumerate(history):
        h,a = idx[m['home']], idx[m['away']]
        X[2*i] = np.r_[1, 1, contrast[h], -contrast[a]]
        X[2*i+1] = np.r_[1, 0, contrast[a], -contrast[h]]
        y.extend([m['hg'], m['ag']])
        w = 2**(-(last-date.fromisoformat(m['date'])).days/half_life)
        weights.extend([w,w])
    y=np.array(y); weights=np.array(weights)
    Q=np.zeros((X.shape[1],X.shape[1])); C=contrast.T@contrast
    Q[2:n+1,2:n+1]=C; Q[n+1:,n+1:]=C
    # Weak proper priors on league level and home advantage keep all-zero short samples finite.
    def objective(b):
        z=X@b; mu=np.exp(z)
        val=np.sum(weights*(mu-y*z)) + penalty/2*(b@Q@b) + .05*(b[0]**2+b[1]**2)
        grad=X.T@(weights*(mu-y))+penalty*(Q@b)
        grad[:2]+=.1*b[:2]
        return float(val),grad
    b0=np.zeros(X.shape[1]); b0[0]=math.log(max(.1,float(y.mean())))
    opt=minimize(objective,b0,jac=True,method='L-BFGS-B',bounds=[(-4,3),(-2,2)]+[(-3,3)]*(2*(n-1)),
                 options={'ftol':1e-12,'gtol':1e-7,'maxiter':1000})
    if not opt.success: raise RuntimeError(f'Goal fit failed: {opt.message}')
    b=opt.x
    model=dict(**metadata('dc' if dc else 'poisson',history),teams=names,intercept=float(b[0]),
               home_advantage=float(b[1]),attack=(contrast@b[2:n+1]).tolist(),
               defence=(contrast@b[n+1:]).tolist(),rho=0.,penalty=penalty,half_life_days=half_life,
               diagnostics=dict(converged=bool(opt.success),iterations=int(opt.nit),
                                objective=float(opt.fun),gradient_max=float(np.max(np.abs(opt.jac)))))
    if dc:
        rates=[goal_rates(model,h,a) for h in names for a in names if h!=a]
        lo,hi=rho_bounds(rates)
        observed=[(*goal_rates(model,m['home'],m['away']),m['hg'],m['ag']) for m in history]
        def rho_loss(r):
            return -sum(weights[2*i]*math.log(tau(hg,ag,lh,la,r)) for i,(lh,la,hg,ag) in enumerate(observed))
        rfit=minimize_scalar(rho_loss,bounds=(lo,hi),method='bounded',options={'xatol':1e-10})
        if not rfit.success: raise RuntimeError('Rho fit failed')
        model['rho']=float(rfit.x); model['rho_bounds']=[lo,hi]
        model['diagnostics']['rho_converged']=True
        model['fit_method']='two-stage penalised Poisson followed by conditional weighted rho likelihood'
    return model


def davidson(diff, home_advantage, draw_log_weight):
    x=(diff+home_advantage)/400*math.log(10)/2
    # Symmetric Davidson: exp(x), nu, exp(-x). nu fitted, not residual draw mass.
    logits=np.array([x,draw_log_weight,-x]); e=np.exp(logits-logits.max())
    return e/e.sum()


def elo_sequence(history, names, K, home_advantage, draw_log_weight, loss=False):
    ratings={n:0. for n in names}; total=0.
    for day in sorted({m['date'] for m in history}):
        updates={n:0. for n in names}
        for m in (m for m in history if m['date']==day):
            p=davidson(ratings[m['home']]-ratings[m['away']],home_advantage,draw_log_weight)
            total-=math.log(max(FLOOR,float(p[outcome(m)])))
            actual=1 if m['hg']>m['ag'] else 0 if m['hg']<m['ag'] else .5
            delta=K*(actual-p[0]-.5*p[1])
            updates[m['home']]+=delta; updates[m['away']]-=delta
        for n in names: ratings[n]+=updates[n]
    return total if loss else ratings


def fit_elo(history, names, K=24):
    def objective(b):
        return elo_sequence(history,names,K,b[0],b[1],True)+.00001*b[0]**2+.01*b[1]**2
    fit=minimize(objective,[0,0],method='L-BFGS-B',bounds=[(-300,300),(-4,3)],options={'ftol':1e-11})
    if not fit.success: raise RuntimeError('Elo fit failed')
    ha,nu=map(float,fit.x)
    return dict(**metadata('elo',history),teams=names,K=K,home_advantage=ha,draw_log_weight=nu,
                ratings=elo_sequence(history,names,K,ha,nu),diagnostics=dict(converged=True,objective=float(fit.fun)))


def fit_frequency(history, names):
    counts=np.ones(3)
    for m in history: counts[outcome(m)]+=1
    return dict(**metadata('frequency',history), probabilities=(counts/counts.sum()).tolist(), prior=[1,1,1])


def fit(kind, history, names, config=None):
    config=config or {}
    if kind in ('poisson','dc'): return fit_goals(history,names,dc=kind=='dc',**config)
    if kind=='elo': return fit_elo(history,names,**config)
    if kind=='frequency': return fit_frequency(history,names)
    raise ValueError(kind)


def poisson_pmf(lam):
    if not math.isfinite(lam) or not 0<lam<100: raise ValueError('Unsupported intensity')
    a=[math.exp(-lam)]; total=a[0]
    while 1-total>1e-13 or len(a)<7:
        a.append(a[-1]*lam/len(a)); total+=a[-1]
        if len(a)>256: raise ValueError('Goal tail failed to converge')
    return a


def goal_distribution(model, home, away):
    lh,la=goal_rates(model,home,away); hp,ap=poisson_pmf(lh),poisson_pmf(la)
    grid=np.outer(hp,ap)
    for i,j in [(0,0),(1,0),(0,1),(1,1)]: grid[i,j]*=tau(i,j,lh,la,model['rho'])
    if np.any(grid<0) or not np.all(np.isfinite(grid)): raise ValueError('Invalid Dixon–Coles mass')
    tail=1-float(grid.sum())
    if abs(tail)>3e-12: raise ValueError(f'Tail too large: {tail}')
    # Only the explicitly reported numerical tail (<3e-12) is rescaled.
    return grid/grid.sum(),max(0.,tail)


def summarise(grid):
    ph=float(np.tril(grid,-1).sum()); pd=float(np.trace(grid)); pa=float(np.triu(grid,1).sum())
    h,a=np.indices(grid.shape)
    best=list(map(int,np.unravel_index(np.argmax(grid),grid.shape)))
    return dict(p_home=ph,p_draw=pd,p_away=pa,expected_points_home=3*ph+pd,expected_points_away=3*pa+pd,
                expected_home_goals=float((h*grid).sum()),expected_away_goals=float((a*grid).sum()),
                best_score=best,btts=float(grid[1:,1:].sum()),over_25=float(grid[h+a>=3].sum()),
                home_clean_sheet=float(grid[:,0].sum()),away_clean_sheet=float(grid[0,:].sum()),
                other_scorelines=1-float(grid[:6,:6].sum()))


def forecast(model, home, away, goal_model=None, include_grid=True):
    kind=model['model_id']; meta={k:model[k] for k in ['model_id','model_version','trained_through','training_sample_size']}
    if kind in ('poisson','dc'):
        grid,tail=goal_distribution(model,home,away)
        answer=dict(**meta,**summarise(grid),goal_model=model['model_version'],numerical_tail=tail)
    else:
        p = (davidson(model['ratings'][home]-model['ratings'][away],model['home_advantage'],model['draw_log_weight'])
             if kind=='elo' else np.array(model['probabilities']))
        answer=dict(**meta,p_home=float(p[0]),p_draw=float(p[1]),p_away=float(p[2]),
                    expected_points_home=float(3*p[0]+p[1]),expected_points_away=float(3*p[2]+p[1]),
                    best_score=None,expected_home_goals=None,expected_away_goals=None,goal_model=None)
        if goal_model:
            grid,tail=goal_distribution(goal_model,home,away)
            h,a=np.indices(grid.shape)
            for mask,prob in [(h>a,p[0]),(h==a,p[1]),(h<a,p[2])]: grid[mask]*=prob/grid[mask].sum()
            answer.update(summarise(grid),goal_model=goal_model['model_version'],numerical_tail=tail,
                          hybrid='Outcome probabilities from '+model['model_version']+'; conditional score shape from '+goal_model['model_version'])
        else:
            return answer
    if include_grid: answer['score_distribution']=grid.tolist()
    return answer


def custom_points(pred, hg, ag):
    """Original source rule: exact-score override gives 100 even if plurality differs."""
    if pred.get('best_score') is None: return None
    h,a=pred['best_score']; exact=(h==hg and a==ag)
    if exact: return 100
    pick=int(np.argmax([pred['p_home'],pred['p_draw'],pred['p_away']]))
    actual=0 if hg>ag else 2 if hg<ag else 1
    near=lambda diff,full,partial: full if diff==0 else partial if diff==1 else 0
    return 35*(pick==actual)+near(abs(h-hg),20,8)+near(abs(a-ag),20,8)+near(abs(h-a-hg+ag),10,4)
