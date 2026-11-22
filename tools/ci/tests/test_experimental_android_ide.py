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
import shutil
import stat
import subprocess
import tempfile
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


    def run_step(self, step, own_tags, upstream_tags):
        """Runs the step's script as Actions does (bash -e -o pipefail) with
        a stand-in gh; returns (exit status, output, GITHUB_ENV)"""
        # the run block ends at the first empty line (comments of the next
        # step follow it)
        block = step.split('run: |\n', 1)[1].split('\n\n', 1)[0]
        script = '\n'.join(l[10:] for l in block.splitlines())
        work = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, work)
        os.mkdir(os.path.join(work, 'bin'))
        gh = os.path.join(work, 'bin', 'gh')
        with open(gh, 'w') as f:
            f.write('#!/bin/bash\n'
                    'if [ "$1 $2" = "release list" ]; then\n'
                    '  if [ "$4" = "SethMorrowSoftware/OpenXTalk-Beyond" ]; then printf "%%s" "%s"; '
                    'else printf "%%s" "%s"; fi; exit 0; fi\n'
                    'if [ "$1 $2" = "release download" ]; then echo "download $3 from $5"; '
                    'touch "$9/OXT-Beyond-$3-linux-x86_64.tar.xz"; exit 0; fi\n'
                    'exit 1\n' % (upstream_tags, own_tags))
        os.chmod(gh, os.stat(gh).st_mode | stat.S_IEXEC)
        env = dict(os.environ, PATH=os.path.join(work, 'bin') + os.pathsep + os.environ['PATH'],
                   REPO='SethMorrowSoftware/beyond-experimental',
                   UPSTREAM='SethMorrowSoftware/OpenXTalk-Beyond', PLATFORM='linux-x86_64',
                   RUNNER_TEMP=work, GITHUB_STEP_SUMMARY=os.path.join(work, 'summary'),
                   GITHUB_ENV=os.path.join(work, 'env'))
        p = subprocess.run(['bash', '--noprofile', '--norc', '-e', '-o', 'pipefail', '-c', script],
                           env=env, capture_output=True, text=True)
        written = ''
        if os.path.exists(env['GITHUB_ENV']):
            with open(env['GITHUB_ENV']) as f:
                written = f.read()
        return p.returncode, p.stdout + p.stderr, written

    @unittest.skipUnless(shutil.which('bash'), 'needs bash')
    def test_the_steps_run(self):
        for step in self.steps():
            # no release here: OXT-Beyond's latest (before, pipefail ended
            # the step at the first lookup, with no message)
            code, out, written = self.run_step(step, '', 'runtimes-x\nv0.2.8-dp.2.1\n')
            self.assertEqual(code, 0, out)
            self.assertIn('download v0.2.8-dp.2.1 from SethMorrowSoftware/OpenXTalk-Beyond', out)
            self.assertIn('OXT-Beyond-v0.2.8-dp.2.1-linux-x86_64.tar.xz', written)
            # a release here: its own, as before
            code, out, written = self.run_step(step, 'v0.2.8-experimental.1\n', 'v0.2.8-dp.2.1\n')
            self.assertEqual(code, 0, out)
            self.assertIn('download v0.2.8-experimental.1 from SethMorrowSoftware/beyond-experimental', out)
            # none anywhere: the step's own refusal
            code, out, _ = self.run_step(step, '', '')
            self.assertNotEqual(code, 0)
            self.assertIn('no release tagged v<version> to take the IDE from', out)


if __name__ == '__main__':
    unittest.main()
