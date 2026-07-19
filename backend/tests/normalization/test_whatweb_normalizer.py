from app.normalization import whatweb_normalizer


def test_extracts_name_and_first_version():
    parsed = [
        {
            "plugins": {
                "Express": {"version": ["4.17.1"]},
                "Cookies": {},
            }
        }
    ]
    result = whatweb_normalizer.normalize(parsed)
    names = {t.name: t.version for t in result.technologies}
    assert names["Express"] == "4.17.1"
    assert names["Cookies"] is None
    assert all(t.detected_by == "whatweb" for t in result.technologies)


def test_missing_version_list_is_defensive():
    parsed = [{"plugins": {"SomePlugin": {"version": "not-a-list"}}}]
    result = whatweb_normalizer.normalize(parsed)
    assert result.technologies[0].version is None


def test_missing_plugins_key():
    parsed = [{}]
    assert whatweb_normalizer.normalize(parsed).technologies == []


def test_empty_input():
    assert whatweb_normalizer.normalize([]).technologies == []
    assert whatweb_normalizer.normalize(None).technologies == []
