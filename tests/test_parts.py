import os, pytest
from ps4fab.parts import PARTS

@pytest.mark.parametrize('name', list(PARTS))
def test_part_builds_and_fits_bed(name, tmp_path):
    PARTS[name](str(tmp_path))          # each builder asserts its own size limits (250 mm bed, pocket, slot)
    stls = [f for f in os.listdir(tmp_path) if f.endswith('.stl')]
    assert stls and all(os.path.getsize(tmp_path / f) > 84 for f in stls)  # 84 = empty binary STL
