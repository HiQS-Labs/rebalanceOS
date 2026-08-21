"""Tests for the shared web components (rebalance.web_components)."""

from __future__ import annotations

import unittest

from rebalance.web_components import (
    RB_BUTTON_CSS,
    _NAV_LINKS,
    badge_html,
    button_link,
    render_shell,
    render_sidebar,
)


class ButtonLinkTests(unittest.TestCase):
    def test_renders_label_href_and_arrow(self) -> None:
        out = button_link("Open", "vscode://file/x")
        self.assertIn('class="rb-btn"', out)
        self.assertIn('href="vscode://file/x"', out)
        self.assertIn("Open", out)
        self.assertIn("↗", out)  # the standard affordance
        self.assertIn('class="rb-btn-arrow"', out)

    def test_external_adds_new_tab_rel(self) -> None:
        out = button_link("Open in Gmail", "https://mail.google.com", external=True)
        self.assertIn('target="_blank"', out)
        self.assertIn('rel="noopener noreferrer"', out)

    def test_internal_has_no_target(self) -> None:
        self.assertNotIn("target=", button_link("Refresh", "/focus-5"))

    def test_arrow_can_be_suppressed(self) -> None:
        self.assertNotIn("↗", button_link("Plain", "/x", arrow=False))

    def test_extra_class_is_appended(self) -> None:
        self.assertIn('class="rb-btn hero-open"', button_link("Open in Obsidian", "obsidian://x", cls="hero-open"))

    def test_title_and_values_are_escaped(self) -> None:
        out = button_link('a"b', 'https://x/?q="&z', title='t"<>')
        self.assertNotIn('q="&z"', out)  # href quote/amp escaped
        self.assertIn("&amp;", out)
        self.assertIn("&quot;", out)  # the quote in label/href/title
        self.assertNotIn("<>", out)  # title angle brackets escaped

    def test_css_targets_the_class_and_themes_via_accent(self) -> None:
        self.assertIn(".rb-btn", RB_BUTTON_CSS)
        self.assertIn("var(--accent", RB_BUTTON_CSS)  # falls back to app blue off-theme


class BadgeHtmlTests(unittest.TestCase):
    def test_known_variant_emits_class_and_label(self) -> None:
        out = badge_html("ok", "x")
        self.assertEqual(out, '<span class="badge badge-ok">x</span>')

    def test_each_variant_maps_to_its_class(self) -> None:
        for v in ("ok", "warning", "error", "info", "neutral"):
            self.assertIn(f'class="badge badge-{v}"', badge_html(v, "lbl"))

    def test_unknown_variant_degrades_to_neutral(self) -> None:
        self.assertIn('class="badge badge-neutral"', badge_html("magenta", "x"))

    def test_label_is_escaped(self) -> None:
        out = badge_html("danger", "<script>x</script>")
        self.assertNotIn("<script>", out)
        self.assertIn("&lt;script&gt;", out)

    def test_no_inline_background_hex(self) -> None:
        self.assertNotIn("style=", badge_html("ok", "x"))


class RenderShellTests(unittest.TestCase):
    def test_emits_sidebar_and_active_marker(self) -> None:
        out = render_shell("Focus 5", "<p>body</p>", active="focus5")
        self.assertIn('<aside class="sidebar"', out)
        self.assertIn("<p>body</p>", out)  # body passed through
        # The active nav item carries class="active" on its <li>.
        self.assertIn('<li class="active"><a href="/focus-5">Focus 5</a></li>', out)
        # A non-active item must NOT be marked active.
        self.assertIn('<li><a href="/auth-log">System Log</a></li>', out)

    def test_style_block_layers_tokens_chrome_and_button(self) -> None:
        out = render_shell("Home", "x", active="today", page_css=".pg{color:red}")
        self.assertIn("--accent", out)  # RB_TOKENS_CSS
        self.assertIn(".app", out)  # RB_CHROME_CSS
        self.assertIn(".rb-btn", out)  # RB_BUTTON_CSS
        self.assertIn(".pg{color:red}", out)  # page_css slotted in

    def test_wide_maps_to_bare_main_class(self) -> None:
        self.assertIn('<main class="main">', render_shell("t", "b", active="today", wide=True))

    def test_narrow_is_the_default(self) -> None:
        self.assertIn('<main class="main narrow">', render_shell("t", "b", active="today"))


class SystemLogLabelTests(unittest.TestCase):
    """One page, one name (GH-101).

    `/auth-log` was renamed to "System Log" everywhere EXCEPT the dashboard's own
    System-section link, which kept saying "Authorization Log". Two names for one
    page is not cosmetic: the operator cannot tell whether they are two surfaces,
    and the stale name still advertises the narrower scope the page is supposed to
    be outgrowing.
    """

    # The System section (Focus 5 / What's Next / System Log) lives only in the
    # RICH sidebar — the one the dashboard renders by passing nav_data. That is
    # the Home-page link, and it is where the stale name survived.
    def _home_sidebar(self) -> str:
        return render_sidebar("today", nav_data={})

    def test_nav_and_sidebar_link_agree_on_the_name(self) -> None:
        nav_label = next(label for key, _href, label in _NAV_LINKS if key == "authlog")
        self.assertEqual(nav_label, "System Log")
        self.assertIn("<span>System Log</span>", self._home_sidebar())

    def test_the_old_name_is_gone_from_the_home_sidebar(self) -> None:
        """THE PIN: the label AND its tooltip. The tooltip is the copy that
        outlived the last rename, because nothing reads a title= attribute."""
        self.assertNotIn("Authorization Log", self._home_sidebar())


if __name__ == "__main__":
    unittest.main()
