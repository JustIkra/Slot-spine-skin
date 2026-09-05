import runpy
import unittest
from pathlib import Path
from PIL import Image


preview = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'scripts/preview_spine.py'))


class PreviewTests(unittest.TestCase):
    def test_additive_light_is_visible_outside_a_body(self):
        data = {'bones': [{'name': 'root'}], 'slots': [{'name': 'glow', 'bone': 'root', 'attachment': 'glow', 'blend': 'additive'}]}
        result = preview['render_frame'](data, {}, 0, {'glow': Image.new('RGBA', (2, 2), (100, 80, 0, 255))}, {'glow': {'glow': {}}}, 4, 4, (10, 20, 30))
        self.assertEqual(result.getpixel((2, 2)), (110, 100, 30))

    def test_absolute_curve_uses_nonzero_interval(self):
        keys = [{'time': 2, 'value': 10, 'curve': [2.5, 10, 3.5, 20]}, {'time': 4, 'value': 20}]
        self.assertAlmostEqual(preview['ev'](keys, 3, 'value'), 15, places=4)

    def test_mesh_is_rejected_instead_of_rendered_as_a_region(self):
        with self.assertRaises(ValueError):
            preview['validate_subset']({'bones': [], 'skins': [{'attachments': {'s': {'m': {'type': 'mesh'}}}}]}, {})
