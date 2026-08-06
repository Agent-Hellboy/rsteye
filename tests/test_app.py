from pathlib import Path

from rsteye import app


def test_read_int_env_uses_default_for_invalid_values(monkeypatch):
    monkeypatch.setenv("RSTEYE_TEST_VALUE", "not-a-number")

    assert app.read_int_env("RSTEYE_TEST_VALUE", 12) == 12


def test_read_int_env_clamps_values_below_one(monkeypatch):
    monkeypatch.setenv("RSTEYE_TEST_VALUE", "0")

    assert app.read_int_env("RSTEYE_TEST_VALUE", 12) == 1


def test_config_override_is_expanded(monkeypatch, tmp_path):
    config_file = tmp_path / "config" / ".env"
    monkeypatch.setenv("RSTEYE_CONFIG_FILE", str(config_file))

    assert app.config_file_path() == config_file


def test_macos_paths_are_user_scoped(monkeypatch, tmp_path):
    monkeypatch.delenv("RSTEYE_CONFIG_FILE", raising=False)
    monkeypatch.delenv("RSTEYE_LOG_FILE", raising=False)
    monkeypatch.setattr(app.sys, "platform", "darwin")
    monkeypatch.setattr(Path, "home", lambda: tmp_path)

    assert app.config_file_path() == (
        tmp_path / "Library" / "Application Support" / "RstEye" / ".env"
    )
    assert app.log_file_path() == (
        tmp_path / "Library" / "Logs" / "RstEye" / "rsteye.log"
    )


def test_resource_path_points_inside_package(monkeypatch):
    monkeypatch.delattr(app.sys, "_MEIPASS", raising=False)

    path = Path(app.resource_path("resources/med.gif"))

    assert path.name == "med.gif"
    assert path.parent.name == "resources"
