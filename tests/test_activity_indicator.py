from pathlib import Path
import unittest


class OpenCodeActivityIndicatorTests(unittest.TestCase):
    def test_terminal_indicator_replaces_command_symbol(self):
        root = Path(__file__).resolve().parents[1]
        script = (root / "panel.js").read_text(encoding="utf-8")
        styles = (root / "panel.css").read_text(encoding="utf-8")

        self.assertNotIn('oc-chat-activity-icon" aria-hidden="true">⌘', script)
        self.assertIn('.oc-chat-activity-icon::before{content:"█"', styles)
        self.assertIn('@keyframes oc-cursor-blink', styles)
        self.assertIn('@keyframes oc-terminal-spinner', styles)
        self.assertIn('25%{content:"-"}', styles)
        self.assertIn('75%{content:"|"}', styles)

    def test_indicator_stays_by_composer_and_only_shows_while_running(self):
        root = Path(__file__).resolve().parents[1]
        script = (root / "panel.js").read_text(encoding="utf-8")
        styles = (root / "panel.css").read_text(encoding="utf-8")

        self.assertIn('document.getElementById("chat-utility-dock")', script)
        self.assertNotIn('document.getElementById("command-addon-badge-slot")', script)
        self.assertIn('PETEY_ADDON_INTERFACE?.["petey-opencode"]?.badges', script)
        self.assertIn('activeRunCount === 0', script)
        self.assertIn('width:38px;min-width:38px;height:38px', styles)
        self.assertNotIn('headerMenu.before(button)', script)

    def test_current_work_registers_as_toggleable_command_panel(self):
        root = Path(__file__).resolve().parents[1]
        script = (root / "panel.js").read_text(encoding="utf-8")
        styles = (root / "panel.css").read_text(encoding="utf-8")

        self.assertIn('window.peteyInterface?.registerPanel({', script)
        self.assertIn('addonId: "petey-opencode"', script)
        self.assertIn('id: "petey-opencode-current-work"', script)
        self.assertIn('renderCurrentWork(runs);', script)
        self.assertIn('.oc-current-output{', styles)


if __name__ == "__main__":
    unittest.main()
