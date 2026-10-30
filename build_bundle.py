from pathlib import Path
import json,csv,zipfile
from collections import Counter
root=Path('/mnt/data/corelab_setup_v1')
raw=r'''M01|Mathematical Basics|P0|
M02|Vectors|P0|M01
M03|Matrices|P0|M02
M04|Linear Algebra|P0|M03
M05|Calculus I|P0|M01
M06|Multivariable Calculus|P0|M03,M05
M07|Differential Equations|P0|M05
M08|Probability|P0|M01
M09|Statistical Foundations|P0|M08
M10|Optimization|P0|M06,M04
M11|Numerical Computing|P0|M03,M05
M12|Rigid-Body Geometry|P0|M02,M03
M13|Advanced Optimization|P1|M10
M14|Advanced Probability|P1|M08,M09
M15|Lie Theory|P1|M12,M06
M16|Advanced Mathematics|P2|M07,M14,M13
PY01|Python Fundamentals|P0|
PY02|Data Structures|P0|PY01
PY03|Python Semantics|P0|PY01
PY04|NumPy|P0|PY01,M03
PY05|Scientific Python|P0|PY04,M11
PY06|PyTorch Basics|P0|PY04,ML04
PY07|Testing & Debugging|P0|PY01
PY08|Research Programming|P0|PY07,T02
PY09|Performance|P1|PY04,PY08
PY10|Advanced Python|P2|PY03
CPP01|C++ Fundamentals|P0|
CPP02|Memory Model|P0|CPP01
CPP03|Resource Management|P0|CPP02
CPP04|Classes & OOP|P0|CPP01,CPP02
CPP05|STL & Algorithms|P0|CPP01
CPP06|Modern C++|P0|CPP03,CPP05
CPP07|Build Systems|P0|CPP01,T01
CPP08|Debugging & Testing|P0|CPP07,CPP02
CPP09|Complexity & Performance|P1|CPP05,CPP08
CPP10|Concurrency|P1|CPP03,CPP08
CPP11|Numerical C++|P1|CPP05,M03
CPP12|Advanced C++|P2|CPP06,CPP09
ML01|ML Problem Formulation|P0|PY04,M08
ML02|Classical ML|P0|ML01,M06
ML03|Generalization|P0|ML01,M09
ML04|Neural Networks|P0|ML02,M03
ML05|Backpropagation|P0|ML04,M06
ML06|Deep Learning Training|P0|ML05,M10
ML07|Model Evaluation|P0|ML03,M09
ML08|Representation Learning|P1|ML06
ML09|Transformers|P1|ML05,ML08
ML10|Self-Supervised Learning|P1|ML08
ML11|Generative Models|P1|ML06,M08
ML12|Advanced ML|P2|ML10,M14
T01|Linux|P0|
T02|Git|P0|
T03|Development Tools|P0|T01
T04|Software Testing|P0|PY07
T05|Reproducible Environments|P0|T02,T03
T06|Docker|P1|T01,T05
T07|Systems Performance|P1|T03,PY09
T08|Advanced Infrastructure|P2|T06,T07
R01|Mechanics Foundations|P0|M01,M02
R02|Robot Mechanisms|P0|R01
R03|Rigid-Body Transformations|P0|M12,R02
R04|Forward Kinematics|P0|R03,M04
R05|Inverse Kinematics|P0|R04,M06
R06|Robot Jacobian|P0|R04,M06
R07|Rigid-Body Dynamics|P0|R01,M07,R06
R08|Contact Mechanics|P0|R01,R07
R09|Actuators & Transmission|P0|R01,R02
R10|Mechanical Design Verification|P0|R01,R09
R11|Floating-Base Dynamics|P1|R07,R08
R12|Advanced Dynamics|P1|R07,M04
R13|Advanced Locomotion|P1|R11,C05
R14|Dexterous Manipulation|P1|R06,R08
R15|Advanced Mechanics|P2|R12,R14
C01|Control Fundamentals|P0|M05,R01
C02|Dynamic Systems|P0|C01,M07,M03
C03|PID Control|P0|C01,C02
C04|Linear Systems|P0|C02,M04,M06
C05|LQR|P0|C04,M10
C06|State Estimation|P0|C02,M08
C07|Kalman Filtering|P0|C06,M09,M03
C08|Sensor Fusion|P0|C07,R09
C09|Digital Control|P0|C03,M11
C10|Nonlinear Control|P1|R07,C04
C11|Model Predictive Control|P1|C05,M13
C12|Nonlinear State Estimation|P1|C07,M06
C13|Optimal Control|P1|C05,C11
C14|Whole-Body Control|P1|R11,C13
C15|Advanced Control|P2|C10,C11
S01|Simulation Fundamentals|P0|M07,M11
S02|MuJoCo|P0|S01,R02
S03|ROS 2 Fundamentals|P0|T01,PY01
S04|Robot Description|P0|S03,R03
S05|ROS 2 Runtime|P0|S03,CPP01
S06|Hardware Integration|P0|S03,R09
S07|Robot Safety|P0|R01,R09
S08|System Identification|P1|S02,C06
S09|Sim2Real|P1|S08,S07
S10|ROS 2 Control|P1|S05,S06
S11|Advanced Simulation|P1|S02,PY06
S12|Advanced Robotics Software|P2|S10,CPP10
V01|Digital Images|P0|PY04
V02|Image Processing|P0|V01,M03
V03|Camera Models|P0|V01,M12
V04|Camera Calibration|P0|V03,M10
V05|Feature Extraction|P1|V02,V03
V06|CNN|P0|ML05,V02
V07|Image Classification|P0|V06,ML07
V08|Object Detection|P0|V07,ML07
V09|Object Tracking|P1|V08,C07
V10|Segmentation|P1|V06,ML07
V11|Multi-View Geometry|P1|V04,M04
V12|Depth Estimation|P1|V11
V13|3D Perception|P1|V12,PY05
V14|Visual Representation Learning|P1|V07,ML08
V15|Vision Transformers|P1|ML09,V07
V16|Video Understanding|P1|V09,V14
V17|Visual Odometry & SLAM|P1|V11,C12
V18|Vision Foundation Models|P2|V14,V15
V19|3D Neural Representations|P2|V13,ML11
V20|Advanced Perception|P2|V18,V19
RL01|RL Fundamentals|P0|PY01,M08
RL02|Markov Decision Processes|P0|RL01,M08
RL03|Value Functions|P0|RL02,M08
RL04|Dynamic Programming|P0|RL03,PY02
RL05|Model-Free Prediction|P0|RL03,M09
RL06|Model-Free Control|P0|RL04,RL05
RL07|Function Approximation|P0|RL06,ML04
RL08|Policy Gradient|P0|RL02,ML05
RL09|Actor-Critic|P0|RL08,RL03
RL10|PPO|P0|RL09,ML06
RL11|Off-Policy RL|P1|RL07,RL09
RL12|RL Experimental Design|P0|RL05,RS02,ML07
RL13|Continuous Control|P1|RL09,C02
RL14|Reward Engineering|P1|RL02,RS02
RL15|Curriculum Learning|P1|RL13,RL14
RL16|Domain Randomization|P1|RL13,S02
RL17|Imitation Learning|P1|RL02,ML06
RL18|Offline RL|P1|RL11,RL17
RL19|Model-Based RL|P1|RL02,S01,ML06
RL20|Hierarchical RL|P1|RL02,RL08
RL21|Safe RL|P1|RL13,S07
RL22|Multi-Agent RL|P2|RL10,RL02
RL23|Advanced Exploration|P2|RL06,ML08
RL24|Meta-RL|P2|RL13,ML10
E01|Sequential Decision Making|P1|RL02,C02
E02|Planning Fundamentals|P1|PY02,E01
E03|Planning Under Uncertainty|P1|E02,C07
E04|Robot Skills|P1|E01,RL20
E05|Task Planning|P1|E02
E06|Task & Motion Planning|P1|E05,R05
E07|Imitation-Based Robot Policies|P1|RL17,ML09
E08|World Models|P1|RL19,ML08
E09|Object-Centric Representations|P1|V13,V14
E10|Vision-Language Models|P1|ML09,V14
E11|Diffusion/Flow Action Policies|P2|ML11,E07
E12|Vision-Language-Action Models|P2|E07,E10
E13|Long-Horizon Robot Learning|P2|E04,E06,E08
E14|Embodied Reasoning|P2|E05,E09,E10
E15|Advanced Embodied Intelligence|P2|E13,E14
RS01|Scientific Reasoning|P0|
RS02|Experimental Design|P0|RS01,M08
RS03|Statistical Inference|P0|RS02,M09
RS04|Experimental Reproducibility|P0|RS02,T02
RS05|Error Analysis|P0|RS02,M09
RS06|Paper Reading|P0|RS01
RS07|Scientific Writing|P1|RS06,RS02
RS08|Literature Review|P1|RS06
RS09|Research Software|P1|RS04,PY08
RS10|Advanced Research|P2|RS03,RS08'''
# name and roles: seven groups, research crosscutting
ranges={'M':'Mathematics','PY':'Programming','CPP':'Programming','ML':'Machine Learning','T':'Programming','R':'Robotics','C':'Robotics','S':'Robotics','V':'Computer Vision','RL':'Reinforcement & Robot Learning','E':'Embodied & Cognitive Robotics','RS':'Scientific Research'}
def group(id):
    for k in ['CPP','PY','ML','RL','RS','M','T','R','C','S','V','E']:
        if id.startswith(k):return ranges[k]
    raise KeyError(id)
records=[]
for line in raw.strip().splitlines():
    id,name,priority,deps=line.split('|')
    records.append({'id':id,'title':name,'domain':group(id),'priority':priority,'prerequisites':[x for x in deps.split(',') if x],'baseline_status':'unassessed','type':'module','target_level': 3 if id in {'M02','M03','M06','M07','PY01','PY04','CPP02','CPP03','CPP08','R04','R06','R07','C02','C03','C05','C07','S02','V03','V06','V08','RL02','RL03','RL08','RL09','RL10','RS02','RS04'} else (2 if priority=='P0' else (2 if priority=='P1' else 1))})
idx={r['id']:r for r in records}
for r in records:
    for d in r['prerequisites']:
        if d not in idx:raise ValueError(f"Missing prerequisite {d} for {r['id']}")
assert len(records)==len(idx)
# graph DAG verification
active=set();closed=set()
def visit(id):
    if id in active: raise ValueError(f'cycle: {id}')
    if id in closed: return
    active.add(id)
    for pre in idx[id]['prerequisites']:visit(pre)
    active.remove(id);closed.add(id)
for r in records: visit(r['id'])
(root/'corelab'/'curriculum_graph_v1.json').write_text(json.dumps({'schema_version':'1.0','as_of':'2026-10-30','policy':{'default_knowledge':'unassessed','prerequisites_are_recommended_not_permanent_barriers':True,'priority_semantics':{'P0':'core','P1':'applied','P2':'extension'},'progress_is_not_in_this_file':True},'modules':records},indent=2,ensure_ascii=False)+'\n')
with (root/'corelab'/'curriculum_graph_v1.csv').open('w',newline='',encoding='utf-8-sig') as f:
    w=csv.writer(f);w.writerow(['id','domain','title','priority','prerequisites','target_level','baseline_status']);
    for r in records:w.writerow([r['id'],r['domain'],r['title'],r['priority'],','.join(r['prerequisites']),r['target_level'],r['baseline_status']])
print('modules',len(records),'priority',dict(Counter(x['priority'] for x in records)),'by_domain',dict(Counter(x['domain'] for x in records)))
