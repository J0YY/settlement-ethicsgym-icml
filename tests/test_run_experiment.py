from scripts.run_experiment import condition_names


def test_condition_names_reads_top_level_strings():
    assert condition_names({"conditions": ["neutral", "shielded"]}) == ["neutral", "shielded"]


def test_condition_names_reads_top_level_dicts():
    assert condition_names({"conditions": [{"name": "zero_shot"}]}) == ["zero_shot"]
