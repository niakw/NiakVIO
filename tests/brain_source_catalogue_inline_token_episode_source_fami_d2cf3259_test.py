from brain_layers.source_catalogue_inline_token_episode_source_fami_d2cf3259 import parse_episode_source
html = '<html><script data-x="1">var eps1 = ["lien:LEGOTEST_ALPHA_1","lien:LEGOTEST_BETA_1"];var eps2 = ["lien:LEGOTEST_ALPHA_2","lien:LEGOTEST_BETA_2"];var epsJeton = "PRIVATE_TEST_JETON";</script data-extra="1"></html>'
first = repr(parse_episode_source(html, 1))
second = repr(parse_episode_source(html, 2))
for token in ('LEGOTEST_ALPHA_1', 'LEGOTEST_ALPHA_2'):
    assert token in first and token not in second, token
for token in ('LEGOTEST_BETA_1', 'LEGOTEST_BETA_2'):
    assert token in second and token not in first, token
assert first != second
assert 'PRIVATE_TEST_JETON' not in first + second
assert 'http://' not in first + second and 'https://' not in first + second
