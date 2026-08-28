"""GH-261: `rebalance doctor` should flag a stale shim shadowing the running
install on PATH, rather than leave the operator to debug a bare `command not
found` naming a Python interpreter that no longer exists.

`_check_rebalance_shim` is pure over `sys.executable` and `shutil.which`, both
monkeypatched here so the check is hermetic — no real PATH state involved.

Anchored on `sys.executable` rather than `sys.argv[0]`: this repo ships
`src/rebalance/__main__.py`, so `rebalance doctor` can be reached via
`python -m rebalance` as well as the installed console script, and argv[0]
differs between the two. Only the running interpreter's own venv `bin/`
directory is invariant across every invocation shape.
"""

from rebalance import doctor


def test_running_install_is_first_on_path_is_ok(tmp_path, monkeypatch):
    venv_bin = tmp_path / "venv" / "bin"
    venv_bin.mkdir(parents=True)
    python = venv_bin / "python3.13"
    python.write_text("")
    rebalance = venv_bin / "rebalance"
    rebalance.write_text("#!/bin/sh\n")

    monkeypatch.setattr(doctor.sys, "executable", str(python))
    monkeypatch.setattr(doctor.shutil, "which", lambda name: str(rebalance))

    check = doctor._check_rebalance_shim()
    assert check.status == doctor.OK
    assert "running install" in check.detail


def test_venv_python_symlinked_to_the_base_interpreter_is_still_ok(tmp_path, monkeypatch):
    """A normal `python3 -m venv` layout: `.venv/bin/python3` is a SYMLINK to
    a base interpreter outside the venv (e.g. Homebrew's). Resolving that
    symlink would walk straight out of the venv and compare against the
    wrong directory — confirmed live against this repo's own .venv, where an
    earlier version of this check false-positived on a correct invocation."""
    base_python = tmp_path / "base" / "python3.13"
    base_python.parent.mkdir(parents=True)
    base_python.write_text("")

    venv_bin = tmp_path / "venv" / "bin"
    venv_bin.mkdir(parents=True)
    venv_python = venv_bin / "python3"
    venv_python.symlink_to(base_python)
    rebalance = venv_bin / "rebalance"
    rebalance.write_text("#!/bin/sh\n")

    monkeypatch.setattr(doctor.sys, "executable", str(venv_python))
    monkeypatch.setattr(doctor.shutil, "which", lambda name: str(rebalance))

    check = doctor._check_rebalance_shim()
    assert check.status == doctor.OK, check.detail


def test_python_dash_m_invocation_is_not_a_false_positive(tmp_path, monkeypatch):
    """`python -m rebalance doctor` gives argv[0] = .../rebalance/__main__.py —
    a correct install must still read as OK, not a shadow warning."""
    venv_bin = tmp_path / "venv" / "bin"
    venv_bin.mkdir(parents=True)
    python = venv_bin / "python3.13"
    python.write_text("")
    rebalance = venv_bin / "rebalance"
    rebalance.write_text("#!/bin/sh\n")

    main_py = tmp_path / "venv" / "lib" / "rebalance" / "__main__.py"
    main_py.parent.mkdir(parents=True)
    main_py.write_text("")

    monkeypatch.setattr(doctor.sys, "executable", str(python))
    monkeypatch.setattr(doctor.sys, "argv", [str(main_py)])  # argv[0] deliberately NOT rebalance
    monkeypatch.setattr(doctor.shutil, "which", lambda name: str(rebalance))

    check = doctor._check_rebalance_shim()
    assert check.status == doctor.OK


def test_shim_reached_via_a_symlink_on_path_is_still_ok(tmp_path, monkeypatch):
    """A pipx-style install: `~/.local/bin/rebalance` is a SYMLINK to the
    real venv script. abspath alone won't follow it to a match — this is
    the same install reached a different way, not a shadow."""
    venv_bin = tmp_path / "venv" / "bin"
    venv_bin.mkdir(parents=True)
    python = venv_bin / "python3.13"
    python.write_text("")
    real_rebalance = venv_bin / "rebalance"
    real_rebalance.write_text("#!/bin/sh\n")

    local_bin = tmp_path / "local" / "bin"
    local_bin.mkdir(parents=True)
    symlinked_rebalance = local_bin / "rebalance"
    symlinked_rebalance.symlink_to(real_rebalance)

    monkeypatch.setattr(doctor.sys, "executable", str(python))
    monkeypatch.setattr(doctor.shutil, "which", lambda name: str(symlinked_rebalance))

    check = doctor._check_rebalance_shim()
    assert check.status == doctor.OK, check.detail


def test_nothing_on_path_is_ok(tmp_path, monkeypatch):
    python = tmp_path / "python3"
    python.write_text("")

    monkeypatch.setattr(doctor.sys, "executable", str(python))
    monkeypatch.setattr(doctor.shutil, "which", lambda name: None)

    check = doctor._check_rebalance_shim()
    assert check.status == doctor.OK


def test_stale_shim_with_missing_interpreter_warns_and_names_it(tmp_path, monkeypatch):
    venv_bin = tmp_path / "venv" / "bin"
    venv_bin.mkdir(parents=True)
    python = venv_bin / "python3.13"
    python.write_text("")

    stale_interpreter = tmp_path / "venv-py314-backup" / "bin" / "python3.14"
    stale_shim = tmp_path / "venv-py314-backup" / "bin" / "rebalance"
    stale_shim.parent.mkdir(parents=True)
    stale_shim.write_text(f"#!{stale_interpreter}\n")
    # deliberately never create stale_interpreter — that's the defect

    monkeypatch.setattr(doctor.sys, "executable", str(python))
    monkeypatch.setattr(doctor.shutil, "which", lambda name: str(stale_shim))

    check = doctor._check_rebalance_shim()
    assert check.status == doctor.WARN
    assert str(stale_shim) in check.detail
    assert str(stale_interpreter) in check.detail
    assert "which -a rebalance" in check.hint


def test_shadowing_entry_with_a_live_interpreter_still_warns(tmp_path, monkeypatch):
    venv_bin = tmp_path / "venv" / "bin"
    venv_bin.mkdir(parents=True)
    python = venv_bin / "python3.13"
    python.write_text("")

    other_interpreter = tmp_path / "other" / "python3"
    other_interpreter.parent.mkdir(parents=True)
    other_interpreter.write_text("")

    other_shim = tmp_path / "other" / "rebalance"
    other_shim.write_text(f"#!{other_interpreter}\n")

    monkeypatch.setattr(doctor.sys, "executable", str(python))
    monkeypatch.setattr(doctor.shutil, "which", lambda name: str(other_shim))

    check = doctor._check_rebalance_shim()
    assert check.status == doctor.WARN
    assert str(other_shim) in check.detail


def test_env_shebang_with_dead_interpreter_still_warns_specifically(tmp_path, monkeypatch):
    """`#!/usr/bin/env python3` — `env` itself always exists; the check must
    resolve the NAME it launches, not treat `env` as the interpreter."""
    venv_bin = tmp_path / "venv" / "bin"
    venv_bin.mkdir(parents=True)
    python = venv_bin / "python3.13"
    python.write_text("")

    stale_shim = tmp_path / "other" / "rebalance"
    stale_shim.parent.mkdir(parents=True)
    stale_shim.write_text("#!/usr/bin/env ghost-python-9000\n")

    monkeypatch.setattr(doctor.sys, "executable", str(python))
    monkeypatch.setattr(doctor.shutil, "which", lambda name: None if name == "ghost-python-9000" else str(stale_shim))

    check = doctor._check_rebalance_shim()
    assert check.status == doctor.WARN
    assert str(stale_shim) in check.detail


def test_env_dash_s_shebang_resolves_the_name_after_the_flag(tmp_path, monkeypatch):
    """`#!/usr/bin/env -S python3 -u` — `-S` splits the rest into env's own
    argv, so the interpreter name is the token AFTER it, not `-S` itself.

    Before the fix, `shebang_parts[1]` ("-S") was passed to `shutil.which()`
    directly — this test's `fake_which` would raise on that call (`-S` is not
    a name it recognizes), proving the wrong token was looked up."""
    venv_bin = tmp_path / "venv" / "bin"
    venv_bin.mkdir(parents=True)
    python = venv_bin / "python3.13"
    python.write_text("")

    live_interpreter = tmp_path / "other" / "python3"
    live_interpreter.parent.mkdir(parents=True)
    live_interpreter.write_text("")

    stale_shim = tmp_path / "other" / "rebalance"
    stale_shim.write_text("#!/usr/bin/env -S python3 -u\n")

    def fake_which(name):
        if name == "rebalance":
            return str(stale_shim)
        if name == "python3":
            return str(live_interpreter)
        raise AssertionError(f"unexpected shutil.which({name!r}) — wrong token resolved")

    monkeypatch.setattr(doctor.sys, "executable", str(python))
    monkeypatch.setattr(doctor.shutil, "which", fake_which)

    check = doctor._check_rebalance_shim()
    assert check.status == doctor.WARN
    assert "no longer exists" not in check.detail


def test_env_shebang_with_live_interpreter_is_generic_shadow_warn(tmp_path, monkeypatch):
    """A resolvable `env python3` shim is a real shadow, but not a *dead
    interpreter* — must not falsely claim the interpreter is missing."""
    venv_bin = tmp_path / "venv" / "bin"
    venv_bin.mkdir(parents=True)
    python = venv_bin / "python3.13"
    python.write_text("")

    live_interpreter = tmp_path / "other" / "python3"
    live_interpreter.parent.mkdir(parents=True)
    live_interpreter.write_text("")

    other_shim = tmp_path / "other" / "rebalance"
    other_shim.write_text("#!/usr/bin/env python3\n")

    def fake_which(name):
        if name == "python3":
            return str(live_interpreter)
        return str(other_shim)

    monkeypatch.setattr(doctor.sys, "executable", str(python))
    monkeypatch.setattr(doctor.shutil, "which", fake_which)

    check = doctor._check_rebalance_shim()
    assert check.status == doctor.WARN
    assert "no longer exists" not in check.detail
