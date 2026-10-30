"""Fixed CoreLab test contract v1. Only run intentionally from your own terminal.
This imports the learner's local file. It is never called by the web server.
"""
import importlib.util, json, math, random, sys
spec=importlib.util.spec_from_file_location('learner_solution',sys.argv[1])
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
topic=sys.argv[2]
def close(a,b):
    assert isinstance(a,(int,float)) and math.isfinite(a)
    assert math.isclose(a,b,rel_tol=1e-9,abs_tol=1e-10),(a,b)
if topic=='M02':
    dot=module.dot
    close(dot([3,4],[1,0]),3)
    close(dot([-2,3],[4,-5]),-23)
    close(dot([0,0],[3,7]),0)
    close(dot([],[]),0)
    try: dot([1],[1,2])
    except ValueError: pass
    else: raise AssertionError('Mismatched dimensions must raise ValueError')
    u=[1,2,3]; v=[4,5,6]; before=(u[:],v[:]); dot(u,v); assert (u,v)==before
    rng=random.Random(941)
    for _ in range(50):
        u=[rng.uniform(-10,10) for _ in range(5)];v=[rng.uniform(-10,10) for _ in range(5)]
        close(dot(u,v),sum(u[i]*v[i] for i in range(5)))
        close(dot(u,v),dot(v,u))
    for _ in range(20):
        u=[rng.uniform(-2,2) for _ in range(7)];v=[rng.uniform(-2,2) for _ in range(7)];w=[rng.uniform(-2,2) for _ in range(7)]
        close(dot(u,[a+b for a,b in zip(v,w)]),dot(u,v)+dot(u,w))
    checks=8
elif topic=='PY01':
    mean=module.mean
    close(mean([2,4,6]),4)
    close(mean([-3,-1,7]),1)
    close(mean([.1,.2]),.15)
    close(mean([8]),8)
    try: mean([])
    except ValueError: pass
    else: raise AssertionError('Empty input must raise ValueError')
    rng=random.Random(819)
    for _ in range(50):
        values=[rng.uniform(-20,20) for _ in range(rng.randint(1,30))]; before=values[:]
        close(mean(values),math.fsum(values)/len(values));assert values==before,'Input was mutated'
    checks=6
else: raise ValueError('Unsupported fixed test contract')
print(json.dumps({'passed':True,'checks':checks}))
