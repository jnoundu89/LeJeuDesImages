def test_app_exists(app):
    assert app is not None
    assert app.secret_key is not None


def test_app_has_routes(app):
    rules = [rule.rule for rule in app.url_map.iter_rules()]
    assert '/' in rules
