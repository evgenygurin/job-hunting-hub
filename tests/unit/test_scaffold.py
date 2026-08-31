def test_pyproject_has_fastmcp_floor():
    import pathlib
    text = pathlib.Path("pyproject.toml").read_text()
    assert 'fastmcp>=3.2,<4' in text
    assert 'pydantic>=2.12' in text
