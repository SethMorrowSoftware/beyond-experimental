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

"""android-engine.yml's two emulator jobs take the IDE whose Android
builder they run from the latest release tagged v<version>. Before
beyond-experimental's first release it has none, so both take OXT-Beyond's
latest release instead (UPSTREAM), and only then; the engine under test is
still the one the run built.

  python3 -m unittest discover -s tools/ci/tests
"""

import os
import re
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
WORKFLOW = os.path.join(ROOT, '.github', 'workflows', 'android-engine.yml')


class AndroidEngineIdeFallbackTest(unittest.TestCase):

    def steps(self):
        with open(WORKFLOW, encoding='utf-8') as f:
            text = f.read()
        # each "Download the IDE" step, up to the next step
        return re.findall(r'- name: Download the IDE\n(.*?)(?=\n      - name: )', text, re.S)

    def test_both_emulator_jobs_fall_back(self):
        steps = self.steps()
        self.assertEqual(len(steps), 2)
        for step in steps:
            self.assertIn('UPSTREAM: SethMorrowSoftware/OpenXTalk-Beyond', step)
            self.assertIn('if [ -z "$tag" ] && [ "$REPO" != "$UPSTREAM" ]; then', step)
            # the fallback comes before the refusal, and the download uses
            # whichever repository the tag was found in
            self.assertLess(step.index('REPO=$UPSTREAM'), step.index('no release tagged'))
            self.assertIn('gh release download "$tag" --repo "$REPO"', step)


if __name__ == '__main__':
    unittest.main()
