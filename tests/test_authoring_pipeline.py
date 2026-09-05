import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from PIL import Image
import numpy as np
from slotspine_tools import canonical_layout, build_skeleton_v2, build_spine_json, make_atlas


class AuthoringTests(unittest.TestCase):
    def test_positioning_recovers_a_known_translation(self):
        from slotspine_tools import position_parts
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);parts=root/'parts';parts.mkdir()
            image=Image.fromarray(np.random.default_rng(7).integers(30,220,(160,160,3),dtype=np.uint8)).convert('RGBA')
            image.save(parts/'part.png')
            reference=Image.new('RGB',(320,320),'white');reference.paste(image,(80,64));reference.save(root/'reference.png')
            positions,_=position_parts.find_all_positions(str(root/'reference.png'),str(parts),.8,4)
            self.assertIn('part',positions)
            self.assertAlmostEqual(positions['part']['x'],80,delta=2)
            self.assertAlmostEqual(positions['part']['y'],64,delta=2)

    def test_layout_to_six_animation_skeleton_and_lossless_source_atlas(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);parts=root/'parts';parts.mkdir()
            images={}
            for index,name in enumerate(canonical_layout.CENTRES):
                image=Image.new('RGBA',(16,16),(index*7,80,150,128))
                image.save(parts/(name+'.png'));images[name]=image
            layout=root/'layout.json'
            canonical_layout.build(str(parts),str(layout))
            config_path=build_skeleton_v2.build(str(layout),str(parts),str(root/'rig'))
            config=json.loads(Path(config_path).read_text())
            skeleton=build_spine_json.build_spine_json(config)
            self.assertEqual(set(skeleton['animations']),{'idle','walk','run','wave','jump','attack'})
            self.assertEqual(len(skeleton['slots']),len(images))
            names={bone['name'] for bone in skeleton['bones']}
            self.assertTrue({'left-upper-arm','right-lower-leg','head','torso'}<=names)
            width,height,placements=make_atlas.pack(images)
            packed=Image.new('RGBA',(width,height))
            for name,(x,y,w,h) in placements.items():packed.paste(images[name],(x,y))
            for name,(x,y,w,h) in placements.items():
                self.assertEqual(packed.crop((x,y,x+w,y+h)).tobytes(),images[name].tobytes())
