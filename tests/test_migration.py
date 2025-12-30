import os
from pathlib import Path

import auth.auth_service as auth_service


def test_migrate_legacy_files(monkeypatch, tmp_path):
    # Set appdata to a different directory so session dir is distinct
    monkeypatch.setenv("APPDATA", str(tmp_path / "appdata"))

    # Create a legacy session files in cwd and write content
    legacy_dir = tmp_path / "cwd"
    legacy_dir.mkdir()
    monkeypatch.chdir(legacy_dir)

    (legacy_dir / "session.token").write_text("legacy-token")
    (legacy_dir / "session.user").write_text("legacy-user@example.com")

    # Ensure migration occurs when reading
    token = auth_service.get_token()
    user = auth_service.get_current_user()

    assert token == "legacy-token"
    assert user == "legacy-user@example.com"

    # Verify files were written into the per-user dir and removed from cwd
    sess_dir = Path(str(tmp_path / "appdata")) / ".my_design"
    assert (sess_dir / "session.token").exists()
    assert (sess_dir / "session.user").exists()
    assert not (legacy_dir / "session.token").exists()
    assert not (legacy_dir / "session.user").exists()