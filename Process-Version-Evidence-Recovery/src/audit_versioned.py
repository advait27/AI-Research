"""Retrospective reference scorer. Policy observations exclude all hidden faults."""
import csv
import json
from pathlib import Path
from dataclasses import asdict
from experiment import effect_bounds, rng_for
from versioned_recovery import Claim


def audit(world, trace):
    sf,lf=world.sensor,world.labels
    pv=sv=lv=0
    spend=2.0
    evidence=None
    for event in trace:
        action=event['action']
        if action=='calibrate_sensor':
            pv+=1;sv+=1;spend+=4
            if rng_for(world.seed,'sensor_repair_success').random()<.85:sf=False
        elif action=='repair_labels':
            lv+=1;spend+=6
            if rng_for(world.seed,'label_repair_success').random()<.9:lf=False
        elif action.startswith('inspect_'):spend+=2.5
        elif action.startswith('verify_'):spend+=1
        elif action=='pilot':
            evidence=event['evidence'];spend+=.02*evidence['n']
            assert evidence['claim']==asdict(Claim('A',pv))
            assert evidence['sensor_version']==sv and evidence['label_version']==lv
            lo,_=effect_bounds(evidence['control_defects'],evidence['treatment_defects'],evidence['n'])
            assert abs(lo-evidence['lower'])<1e-12
        assert abs(spend-event['cost_to_date'])<1e-8
        assert (pv,sv,lv)==(event['process_version'],event['sensor_version'],event['label_version'])
    final=trace[-1]
    accepted=final['action']=='endorse'
    target=final['claim']
    match=bool(evidence and target==evidence['claim'])
    support=match and not(sf or lf)
    true_current=world.b-.06*sf
    true_target=world.b-.06*world.sensor if target['process_version']==0 else true_current
    return {'accepted':int(accepted),'supported_beneficial':int(accepted and support and true_target>.01),
            'unsupported':int(accepted and not support),'wrong_version':int(accepted and not match),
            'nonbeneficial_target':int(accepted and true_target<=.01),
            'beneficial_current':int(accepted and true_current>.01),'cost':round(spend,2)}


def main():
    from versioned_recovery import World
    root=Path(__file__).resolve().parents[1]/'results/versioned-recovery/evaluation'
    with (root/'trials.csv').open() as f:rows=list(csv.DictReader(f))
    passed=0
    with (root/'traces.jsonl').open() as f:
        for row,line in zip(rows,f):
            trace=json.loads(line)
            flags=[v=='1' for v in trace['fault']]
            result=audit(World(trace['seed'],*flags,trace['b']),trace['events'])
            for k,value in result.items():assert abs(float(row[k])-value)<1e-8,(k,row,value)
            passed+=1
    assert passed==len(rows)
    report={'episodes_replayed':passed,'mismatches':0,
            'scope':'Reference replay of claim identities, version transitions, action costs, hidden residual faults, and benefit. Shared Wilson helper; not independent statistical validation.'}
    (root/'audit.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report))


if __name__=='__main__':main()
