"""The install mark names FQKIT and the authors' first names."""

import io

from fqkit.banner import AUTHOR_FIRST_NAMES, BANNER, show
from fqkit.__main__ import main


def test_banner_names_the_authors():
    assert AUTHOR_FIRST_NAMES == ("Felix", "Dorcas")
    assert "Felix" in BANNER
    assert "Dorcas" in BANNER
    assert BANNER.splitlines()[0].startswith("-")
    assert BANNER.splitlines()[-1].startswith("-")
    widths = {len(line) for line in BANNER.splitlines()}
    assert len(widths) == 1


def test_show_is_plain_text_when_not_a_terminal():
    buffer = io.StringIO()
    show(buffer)
    assert buffer.getvalue() == BANNER + "\n"
    assert "\033" not in buffer.getvalue()


def test_show_uses_color_on_a_terminal(monkeypatch):
    class _TTY(io.StringIO):
        def isatty(self):
            return True

    monkeypatch.delenv("NO_COLOR", raising=False)
    buffer = _TTY()
    show(buffer)
    text = buffer.getvalue()
    assert "Felix" in text
    assert text.startswith("\033[38;5;39m")


def test_command_prints_the_mark(capsys):
    main()
    captured = capsys.readouterr()
    assert "Felix" in captured.out
    assert "Dorcas" in captured.out
