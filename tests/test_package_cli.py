from __future__ import annotations

from forge.__main__ import main


def test_once_bootstrap_is_contract_only(capsys) -> None:
    assert main(["--once"]) == 0
    assert "physical dispatch remains disabled" in capsys.readouterr().out
