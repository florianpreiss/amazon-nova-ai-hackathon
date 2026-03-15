from src.core.safety import apply_anti_shame_filter, build_identity_addendum


def test_apply_anti_shame_filter_rewrites_shaming_language() -> None:
    filtered = apply_anti_shame_filter("Obviously, everyone knows this is basic.")

    assert "obviously" not in filtered.lower()
    assert "everyone knows" not in filtered.lower()
    assert "this is basic" not in filtered.lower()


def test_build_identity_addendum_includes_inclusion_guidance() -> None:
    addendum = build_identity_addendum({"first_generation_student": True})

    assert "inclusive" in addendum.lower()
    assert "anti-racist" in addendum.lower()
    assert "first_generation_student: True" in addendum
