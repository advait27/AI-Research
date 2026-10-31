"""Frozen-protocol, version-aware recovery extension. No LLM or plant data."""
import argparse
import csv
import hashlib
import itertools
import json
import math
import random
from dataclasses import dataclass, replace, asdict
from functools import lru_cache
from pathlib import Path
from statistics import NormalDist
from experiment import count_defects, effect_bounds, rng_for

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / 'research' / 'VERSIONED_PROTOCOL.json'
POLICIES = ['stop', 'screen_targeted', 'full_revalidation', 'cheapest',
            'information_gain', 'decision_loss', 'decision_loss_no_version', 'full_revalidation_no_version']
ACTIONS = ['inspect_sensor', 'inspect_labels', 'calibrate_sensor', 'repair_labels',
           'verify_sensor', 'verify_labels']
COSTS = [2.5, 2.5, 4.0, 6.0, 1.0, 1.0]
EFFECTS = [.04, .0, -.02]
SIZES = [400, 800, 1600]


@dataclass(frozen=True)
class Claim:
    line: str
    process_version: int
    comparator_version: int = 0
    population: str = 'fixed_factory_population'
    outcome: str = 'binary_defect_v0'
    minimum: float = .01


@dataclass(frozen=True)
class Evidence:
    claim: Claim
    sensor_version: int
    label_version: int
    control_defects: int
    treatment_defects: int
    n: int
    lower: float
    sensor_pass: bool
    label_pass: bool


def same_target(a, b):
    return a == b


def endorsement_allowed(claim, evidence, sensor_version, label_version, version_guard=True):
    # This monitor receives declared tests and identities, never hidden fault flags.
    return (evidence.sensor_pass and evidence.label_pass and
            evidence.sensor_version == sensor_version and evidence.label_version == label_version and
            evidence.lower > claim.minimum and
            (not version_guard or same_target(claim, evidence.claim)))


@dataclass(frozen=True)
class State:
    ps: float
    pl: float
    gs: bool
    gl: bool
    mask: int
    budget: float


def round_state(ps, pl, gs, gl, mask, budget):
    return State(round(ps, 12), round(pl, 12), gs, gl, mask, round(budget, 2))


def pass_probability(p, sensitivity, specificity):
    return p * (1-sensitivity) + (1-p) * specificity


def posterior(p, passed, sensitivity, specificity):
    likelihood_fault = 1-sensitivity if passed else sensitivity
    likelihood_clean = specificity if passed else 1-specificity
    return p * likelihood_fault / (p * likelihood_fault + (1-p) * likelihood_clean)


def available(s):
    for i in range(6):
        if s.mask & (1 << i) or COSTS[i] > s.budget:
            continue
        if i == 4 and not s.mask & (1 << 2):
            continue
        if i == 5 and not s.mask & (1 << 3):
            continue
        yield i


def observation_parameters(i):
    return (.98, .98) if i < 2 else (.9, .95)


def transition(s, i, passed=None):
    ps, pl, gs, gl = s.ps, s.pl, s.gs, s.gl
    if i == 2:
        ps *= .15
        gs = False
    elif i == 3:
        pl *= .1
        gl = False
    else:
        sensitivity, specificity = observation_parameters(i)
        if i in (0, 4):
            ps = posterior(ps, passed, sensitivity, specificity)
            gs = passed
        else:
            pl = posterior(pl, passed, sensitivity, specificity)
            gl = passed
    return round_state(ps, pl, gs, gl, s.mask | (1 << i), s.budget-COSTS[i])


@lru_cache(None)
def forecast(n, sensor_fault, label_fault, b):
    """Planning approximation only. Evaluation always draws actual Bernoulli data."""
    p0 = .12
    measured = b - .06*sensor_fault + .05*label_fault
    p1 = max(.001, min(.99, p0-measured))
    margin = 1.959963984540054 * (math.sqrt(p0*(1-p0)/n)+math.sqrt(p1*(1-p1)/n))
    sd = math.sqrt((p0*(1-p0)+p1*(1-p1))/n)
    return NormalDist().cdf((p0-p1-.01-margin)/sd)


@lru_cache(None)
def terminal(s):
    best = (0.0, 'stop')
    if not (s.gs and s.gl):
        return best
    for n in SIZES:
        cost = .02*n
        if cost > s.budget:
            continue
        utility = -cost
        for sf, lf, b in itertools.product([0, 1], [0, 1], EFFECTS):
            prob = (s.ps if sf else 1-s.ps) * (s.pl if lf else 1-s.pl) / 3
            supported_benefit = not (sf or lf) and b > .01
            utility += prob*forecast(n, sf, lf, b)*(300 if supported_benefit else -1000)
        if utility > best[0] + 1e-10:
            best = (utility, 'pilot_'+str(n))
    return best


@lru_cache(None)
def best_action(s, depth=4):
    best = terminal(s)
    if depth <= 0:
        return best
    for i in available(s):
        value = -COSTS[i]
        if i in (2, 3):
            value += best_action(transition(s, i), depth-1)[0]
        else:
            p = s.ps if i in (0, 4) else s.pl
            sensitivity, specificity = observation_parameters(i)
            pp = pass_probability(p, sensitivity, specificity)
            value += pp*best_action(transition(s, i, True), depth-1)[0]
            value += (1-pp)*best_action(transition(s, i, False), depth-1)[0]
        if value > best[0] + 1e-10:
            best = (value, ACTIONS[i])
    return best


def entropy(p):
    if p <= 0 or p >= 1:
        return 0
    return -p*math.log2(p)-(1-p)*math.log2(1-p)


def choose_information(s):
    sizes = [n for n in SIZES if .02*n <= s.budget]
    if s.gs and s.gl and (1-s.ps)*(1-s.pl) >= .95 and sizes:
        return 'pilot_'+str(max(sizes))
    tests = [i for i in available(s) if i not in (2, 3)]
    if tests:
        def gain(i):
            p = s.ps if i in (0, 4) else s.pl
            se, sp = observation_parameters(i)
            pp = pass_probability(p, se, sp)
            e = pp*entropy(posterior(p, True, se, sp)) + (1-pp)*entropy(posterior(p, False, se, sp))
            return (entropy(p)-e)/COSTS[i]
        return ACTIONS[max(tests, key=gain)]
    repairs = [i for i in available(s) if i in (2, 3)]
    if repairs:
        return ACTIONS[max(repairs, key=lambda i:(s.ps if i == 2 else s.pl)/COSTS[i])]
    return 'stop'


@dataclass(frozen=True)
class World:
    seed: int
    sensor: bool
    labels: bool
    history: bool
    b: float


class Environment:
    def __init__(self, world, budget):
        self.__world = world
        self.sensor = world.sensor
        self.labels = world.labels
        self.process_version = self.sensor_version = self.label_version = 0
        self.budget = float(budget)
        self.cost = 0.0
        self.trace = []
        self.claim_validity = {'A': False, 'B': True}
        self.evidence = None

    @property
    def independent_line_b(self):
        return self.claim_validity['B']

    def invalidate_claim(self, line):
        self.claim_validity[line] = False

    def claim(self):
        return Claim('A', self.process_version)

    def _log(self, action, **kwargs):
        self.trace.append({'step':len(self.trace), 'action':action, 'cost_to_date':self.cost,
                           'process_version':self.process_version,
                           'sensor_version':self.sensor_version, 'label_version':self.label_version, **kwargs})

    def _charge(self, cost):
        if self.cost + cost > self.budget + 1e-9:
            raise ValueError('Budget violation')
        self.cost += cost

    def _test(self, dimension, sensitivity, specificity, channel):
        faulty = self.sensor if dimension == 'sensor' else self.labels
        # Same independent potential observation channel across paired policies.
        u = rng_for(self.__world.seed, channel).random()
        return not (u < (sensitivity if faulty else 1-specificity))

    def start(self):
        self._charge(2)
        gs = self._test('sensor', .8, .9, 'screen_sensor')
        gl = self._test('labels', .8, .9, 'screen_labels')
        self._log('screens', sensor_pass=gs, label_pass=gl,
                  identical_reported_historical_reduction=.04)
        return round_state(posterior(.5, gs, .8, .9), posterior(.5, gl, .8, .9), gs, gl, 0, self.budget-self.cost)

    def act(self, s, action):
        i = ACTIONS.index(action)
        if i not in list(available(s)):
            raise ValueError('Inadmissible action: '+action)
        self._charge(COSTS[i])
        if i == 2:
            # Calibrating the controller creates a new physical configuration even if
            # a repair attempt fails. The outcome remains hidden until checked.
            self.invalidate_claim('A')
            self.process_version += 1
            self.sensor_version += 1
            if rng_for(self.__world.seed, 'sensor_repair_success').random() < .85:
                self.sensor = False
            self._log(action, invalidates=['A.effect', 'A.claim'], preserves=['B.claim'])
            return transition(s, i)
        if i == 3:
            self.invalidate_claim('A')
            self.label_version += 1
            if rng_for(self.__world.seed, 'label_repair_success').random() < .9:
                self.labels = False
            self._log(action, invalidates=['A.evidence'], preserves=['B.claim'])
            return transition(s, i)
        dimension = 'sensor' if i in (0, 4) else 'labels'
        se, sp = observation_parameters(i)
        passed = self._test(dimension, se, sp, action)
        self._log(action, passed=passed)
        return transition(s, i, passed)

    def pilot(self, s, n):
        if not (s.gs and s.gl):
            raise ValueError('Pilot without passing declared prerequisites')
        self._charge(.02*n)
        w = self.__world
        observed_benefit = w.b - .06*self.sensor + .05*self.labels
        c = count_defects(w.seed, 'version_pilot_control', .12, n)
        t = count_defects(w.seed, 'version_pilot_treatment', .12-observed_benefit, n)
        lower, _ = effect_bounds(c, t, n)
        self.evidence = Evidence(self.claim(), self.sensor_version, self.label_version,
                                 c, t, n, lower, s.gs, s.gl)
        self._log('pilot', n=n, control=c, treatment=t, lower=lower,
                  evidence_process_version=self.process_version, evidence=asdict(self.evidence))
        return self.evidence

    def endorse_and_score(self, policy, evidence):
        # Policies do not receive the fields below; scoring is retrospective.
        request = Claim('A', 0) if policy.endswith('_no_version') else self.claim()
        accepted = bool(evidence and endorsement_allowed(request, evidence, self.sensor_version,
                            self.label_version, version_guard=not policy.endswith('_no_version')))
        self._log('endorse' if accepted else 'abstain', target_process_version=request.process_version, claim=asdict(request))
        match = bool(evidence and same_target(request, evidence.claim))
        residual_fault = bool(self.sensor or self.labels)
        benefit_current = self.__world.b - .06*self.sensor
        benefit_original = self.__world.b - .06*self.__world.sensor
        target_benefit = benefit_original if request.process_version == 0 else benefit_current
        support = match and not residual_fault
        return {
            'accepted':int(accepted), 'supported_beneficial':int(accepted and support and target_benefit > .01),
            'unsupported':int(accepted and not support),
            'wrong_version':int(accepted and not match),
            'nonbeneficial_target':int(accepted and target_benefit <= .01),
            'beneficial_current':int(accepted and benefit_current > .01),
            'current_risk_reduction':benefit_current if accepted else 0.0,
            'cost':round(self.cost, 2), 'n':evidence.n if evidence else 0,
            'target_version':request.process_version, 'evidence_version':evidence.claim.process_version if evidence else -1,
            'line_b_preserved':int(self.independent_line_b),
            'has_residual_fault':int(residual_fault),
        }


def run(world, budget, policy):
    env = Environment(world, budget)
    s = env.start()
    evidence = None
    if policy in ('stop', 'screen_targeted', 'full_revalidation', 'full_revalidation_no_version'):
        repairs = []
        if policy.startswith('full_revalidation'):
            repairs = [2, 3]
        elif policy == 'screen_targeted':
            repairs = ([2] if not s.gs else []) + ([3] if not s.gl else [])
        required = sum(COSTS[i]+1 for i in repairs)+8
        if (policy != 'stop' or (s.gs and s.gl)) and required <= s.budget:
            for i in repairs:
                s = env.act(s, ACTIONS[i]); s = env.act(s, ACTIONS[i+2])
            sizes = [n for n in SIZES if .02*n <= s.budget]
            if s.gs and s.gl and sizes:
                evidence = env.pilot(s, max(sizes))
    else:
        depth = 4
        # A bounded episode also keeps the non-planning baselines finite.
        for _ in range(6):
            if policy.startswith('decision_loss'):
                action = best_action(s, depth)[1]
                depth -= 1
            elif policy == 'information_gain':
                action = choose_information(s)
            elif policy == 'cheapest':
                sizes = [n for n in SIZES if .02*n <= s.budget]
                if s.gs and s.gl and sizes:
                    action = 'pilot_'+str(max(sizes))
                else:
                    actions = list(available(s))
                    action = ACTIONS[min(actions, key=lambda i:(COSTS[i],i))] if actions else 'stop'
            else:
                raise ValueError(policy)
            if action == 'stop':
                break
            if action.startswith('pilot_'):
                evidence = env.pilot(s, int(action.split('_')[1]))
                break
            s = env.act(s, action)
    result = env.endorse_and_score(policy, evidence)
    return result, env.trace


def summarize(rows):
    out=[]
    for p in POLICIES:
        rr=[r for r in rows if r['policy']==p]
        out.append({'policy':p, 'episodes':len(rr),
                    **{k:sum(r[k] for r in rr) for k in ['accepted','supported_beneficial','unsupported','wrong_version','nonbeneficial_target','beneficial_current']},
                    'mean_cost':sum(r['cost'] for r in rr)/len(rr),
                    'mean_risk_reduction':sum(r['current_risk_reduction'] for r in rr)/len(rr)})
    return out


def paired_bootstrap(rows, metric, first='decision_loss', second='full_revalidation'):
    clusters={}
    for r in rows:
        if r['policy'] not in (first,second):continue
        clusters.setdefault(r['seed'],{})[r['fault']+':'+str(r['budget'])+':'+r['policy']]=r[metric]
    deltas=[]
    for values in clusters.values():
        a=sum(v for k,v in values.items() if k.endswith(':'+first))
        b=sum(v for k,v in values.items() if k.endswith(':'+second))
        count=sum(k.endswith(':'+first) for k in values)
        deltas.append((a-b)/count)
    rng=random.Random(901731)
    means=sorted(sum(rng.choice(deltas) for _ in deltas)/len(deltas) for _ in range(2000))
    return {'comparison':first+' minus '+second, 'metric':metric,
            'mean_difference':sum(deltas)/len(deltas),'lower_95':means[49],'upper_95':means[1949],
            'clusters':len(deltas),'resamples':2000}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--split',choices=['development','evaluation'],default='development')
    args=parser.parse_args()
    protocol=json.loads(PROTOCOL.read_text())
    reps=protocol['development_repetitions_per_effect'] if args.split=='development' else protocol['evaluation_repetitions_per_effect']
    base=protocol[args.split+'_seed']
    out=ROOT/'results/versioned-recovery'/args.split;out.mkdir(parents=True,exist_ok=True)
    rows=[];traces=[]
    for flags in itertools.product([False,True],repeat=3):
        fault=''.join('1' if f else '0' for f in flags)
        for effect_id,b in enumerate(EFFECTS):
            for rep in range(reps):
                seed=base+effect_id*1000+rep
                world=World(seed,*flags,b)
                for budget in protocol['budgets']:
                    for policy in POLICIES:
                        result,trace=run(world,budget,policy)
                        row={'seed':seed,'fault':fault,'b':b,'budget':budget,'policy':policy,**result}
                        rows.append(row)
                        traces.append({'seed':seed,'fault':fault,'b':b,'budget':budget,'policy':policy,'events':trace})
    assert all(r['cost']<=r['budget']+1e-9 for r in rows)
    assert all(r['line_b_preserved'] for r in rows)
    payload={'split':args.split,'protocol_sha256':hashlib.sha256(PROTOCOL.read_bytes()).hexdigest(),
             'worlds_per_policy':len(rows)//len(POLICIES),'base_seed_effect_clusters':reps*3,
             'summary':summarize(rows),
             'by_budget':{str(b):summarize([r for r in rows if r['budget']==b]) for b in protocol['budgets']},
             'paired_intervals':[paired_bootstrap(rows,k) for k in ['supported_beneficial','unsupported','cost']]}
    with (out/'trials.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    with (out/'traces.jsonl').open('w') as f:
        for trace in traces:f.write(json.dumps(trace)+'\n')
    (out/'summary.json').write_text(json.dumps(payload,indent=2)+'\n')
    print(json.dumps(payload,indent=2))
    print('Planner cache:',best_action.cache_info())


if __name__=='__main__':main()
