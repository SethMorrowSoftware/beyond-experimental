# Copyright (C) 2026 OXT-Beyond contributors.
#
# This file is part of OXT-Beyond.
#
# OXT-Beyond is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License v3 as published by the Free
# Software Foundation.
#
# OXT-Beyond is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License
# along with OXT-Beyond.  If not see <http://www.gnu.org/licenses/>.

"""beyond-experimental's Windows installer installs beside a released
OXT-Beyond, never over it: Installer/oxt-beyond/oxt-beyond.iss has an
AppId of its own (the uninstall key Inno Setup replaces by), its own
Program Files folder, Start menu folder and desktop shortcut, and leaves
the file association unticked; tools/ci/test-installer.ps1 looks for the
shortcuts where the installer puts them.

  python3 -m unittest discover -s tools/ci/tests
"""

import os
import re
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
ISS = os.path.join(ROOT, 'Installer', 'oxt-beyond', 'oxt-beyond.iss')
TEST_PS1 = os.path.join(ROOT, 'tools', 'ci', 'test-installer.ps1')

# OXT-Beyond's own AppId (OpenXTalk-Beyond's oxt-beyond.iss)
OXT_BEYOND_APP_ID = '6CB5C1F5-4B20-43EF-B5F6-1C0C2C07B803'
INSTALL_NAME = 'OXT-Beyond Experimental'


def read(path):
    with open(path, encoding='utf-8-sig') as f:
        return f.read()


def setting(text, name):
    m = re.search(r'(?m)^\s*%s\s*=\s*(.*?)\s*$' % re.escape(name), text)
    return m.group(1) if m else None


class ExperimentalInstallerTest(unittest.TestCase):

    def setUp(self):
        self.iss = read(ISS)

    def test_app_id_is_not_oxt_beyonds(self):
        app_id = setting(self.iss, 'AppId')
        self.assertIsNotNone(app_id)
        self.assertRegex(app_id, r'^\{\{[0-9A-F]{8}(-[0-9A-F]{4}){3}-[0-9A-F]{12}\}$')
        self.assertNotIn(OXT_BEYOND_APP_ID, app_id.upper())

    def test_folders_and_shortcuts_are_its_own(self):
        self.assertIn('#define InstallName "%s"' % INSTALL_NAME, self.iss)
        self.assertEqual(setting(self.iss, 'DefaultDirName'), r'{autopf}\{#InstallName}')
        self.assertEqual(setting(self.iss, 'DefaultGroupName'), '{#InstallName}')
        self.assertIn(r'Name: "{autodesktop}\{#InstallName}"', self.iss)
        self.assertNotIn(r'Name: "{autodesktop}\{#AppName}"', self.iss)

    def test_file_association_is_unticked(self):
        line = [l for l in self.iss.splitlines() if l.startswith('Name: "fileassoc"')]
        self.assertEqual(len(line), 1)
        self.assertIn('Flags: unchecked', line[0])

    def test_installer_test_agrees(self):
        ps1 = read(TEST_PS1)
        self.assertIn("$InstallName = '%s'" % INSTALL_NAME, ps1)
        self.assertIn('$groupDir = Join-Path $programsDir $InstallName', ps1)
        self.assertIn('$desktopLink = Join-Path $desktopDir "$InstallName.lnk"', ps1)
        self.assertIn("'fileassoc' } else { '!fileassoc' }", ps1)


if __name__ == '__main__':
    unittest.main()
