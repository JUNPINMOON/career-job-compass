from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_activation_cleanup_is_scoped_to_career_compass_caches() -> None:
    source = (ROOT / "sw.js").read_text(encoding="utf-8")

    assert 'key.startsWith("career-compass-") && key !== CACHE' in source
    assert '.filter((key) => key !== CACHE ||' not in source
