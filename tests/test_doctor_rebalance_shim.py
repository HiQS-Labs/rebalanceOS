"""GH-261: `rebalance doctor` should flag a stale shim shadowing the running
install on PATH, rather than leave the operator to debug a bare `command not
found` naming a Python interpreter that no longer exists.

`_check_rebalance_shim` is pure over `sys.argv[0]` and `shutil.which`, both
monkeypatched here so the check is hermetic — no real PATH state involved.
"""

from rebalance import doctor


def test_running_install_is_first_on_path_is_ok(tmp_path, monkeypatch):
    running = tmp_path / "venv" / "bin" / "rebalance"
    running.parent.mkdir(parents=True)
    running.write_text("#!/usr/bin/env python3\n")

    monkeypatch.setattr(doctor.sys, "argv", [str(running)])
    monkeypatch.setattr(doctor.shutil, "which", lambda name: str(running))

    check = doctor._check_rebalance_shim()
    assert check.status == doctor.OK
    assert "running install" in check.detail


def test_nothing_on_path_is_ok(tmp_path, monkeypatch):
    running = tmp_path / "rebalance"
    running.write_text("#!/usr/bin/env python3\n")

    monkeypatch.setattr(doctor.sys, "argv", [str(running)])
    monkeypatch.setattr(doctor.shutil, "which", lambda name: None)

    check = doctor._check_rebalance_shim()
    assert check.status == doctor.OK


def test_stale_shim_with_missing_interpreter_warns_and_names_it(tmp_path, monkeypatch):
    running = tmp_path / "venv" / "bin" / "rebalance"
    running.parent.mkdir(parents=True)
    running.write_text("#!/usr/bin/env python3\n")

    stale_interpreter = tmp_path / "venv-py314-backup" / "bin" / "python3.14"
    stale_shim = tmp_path / "venv-py314-backup" / "bin" / "rebalance"
    stale_shim.parent.mkdir(parents=True)
    stale_shim.write_text(f"#!{stale_interpreter}\n")
    # deliberately never create stale_interpreter — that's the defect

    monkeypatch.setattr(doctor.sys, "argv", [str(running)])
    monkeypatch.setattr(doctor.shutil, "which", lambda name: str(stale_shim))

    check = doctor._check_rebalance_shim()
    assert check.status == doctor.WARN
    assert str(stale_shim) in check.detail
    assert str(stale_interpreter) in check.detail
    assert "which -a rebalance" in check.hint


def test_shadowing_entry_with_a_live_interpreter_still_warns(tmp_path, monkeypatch):
    running = tmp_path / "venv" / "bin" / "rebalance"
    running.parent.mkdir(parents=True)
    running.write_text("#!/usr/bin/env python3\n")

    other_interpreter = tmp_path / "other" / "python3"
    other_interpreter.parent.mkdir(parents=True)
    other_interpreter.write_text("")

    other_shim = tmp_path / "other" / "rebalance"
    other_shim.write_text(f"#!{other_interpreter}\n")

    monkeypatch.setattr(doctor.sys, "argv", [str(running)])
    monkeypatch.setattr(doctor.shutil, "which", lambda name: str(other_shim))

    check = doctor._check_rebalance_shim()
    assert check.status == doctor.WARN
    assert str(other_shim) in check.detail
    assert str(running) in check.detail
