import json
import runpy
import sys

module = runpy.run_path(sys.argv[1])
names = ['root', 'torso', 'hip', 'head', 'neck', 'left-upper-arm', 'left-lower-arm',
         'right-upper-arm', 'right-lower-arm', 'left-upper-leg', 'left-lower-leg',
         'right-upper-leg', 'right-lower-leg']
config = {'bones': [{'name': n, **({'parent': 'root'} if n != 'root' else {})} for n in names],
          'animations': ['idle', 'walk', 'run', 'wave', 'jump', 'attack']}
result = module['build_spine_json'](config)
result['animations']['probe'] = module.get('finish_animation', lambda x: x)({'bones': {'root': {
    'rotate': [module['_kf'](2, angle=0), module['_kf'](4, angle=30)],
    'translate': [module['_kf'](2, x=0, y=10), module['_kf'](4, x=0, y=20)],
    'scale': [module['_kf'](2, x=1, y=1), module['_kf'](4, x=1, y=1)]}}})
print(json.dumps(result))
