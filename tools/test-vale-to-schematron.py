#!/usr/bin/env python3
# Copyright (c) 2026 Red Hat, Inc.
# This program and the accompanying materials are made
# available under the terms of the Eclipse Public License 2.0
# which is available at https://www.eclipse.org/legal/epl-2.0/
#
# SPDX-License-Identifier: EPL-2.0
"""Unit tests for Vale-to-Schematron conversion details."""

import importlib.util
import os
import unittest
from unittest import mock


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GENERATOR_PATH = os.path.join(REPO_ROOT, "tools", "vale-to-schematron.py")
SCH_NS = "http://purl.oclc.org/dsdl/schematron"


def load_generator():
    """Load the generator module whose filename contains a hyphen."""
    spec = importlib.util.spec_from_file_location("vale_to_schematron", GENERATOR_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


generator = load_generator()


class SchematronGeneratorTests(unittest.TestCase):
    """Check conversion behavior that is not covered by XML smoke tests."""

    def test_substitution_message_uses_matched_text(self):
        """Substitution diagnostics must not print the source regex."""
        data = {
            "extends": "substitution",
            "level": "error",
            "ignorecase": True,
            "message": "Use '%s' rather than '%s'.",
            "swap": {"bad-term": "good term"},
        }

        with mock.patch.object(generator, "write_schematron_file") as writer:
            generator.handle_substitution("TestSubstitution", data)

        schema = writer.call_args.args[1]
        report = schema.find(".//{%s}report" % SCH_NS)
        value_of = report.find("{%s}value-of" % SCH_NS)

        self.assertEqual(report.text, "Use 'good term' rather than '")
        self.assertIsNotNone(value_of)
        self.assertIn("replace(.", value_of.get("select"))
        self.assertIn("bad-term", value_of.get("select"))
        self.assertIn(r"^[^\r\n]*?(?:^|[^\w\r\n])(bad-term)(?:[^\w\r\n]|$)[^\r\n]*$",
                      value_of.get("select"))
        self.assertEqual(value_of.tail, "'.")

    def test_sentence_scope_uses_text_nodes(self):
        """Inline code must be excluded even when nested inside a paragraph."""
        context = generator.build_scope_context("sentence", text_nodes=True)

        self.assertTrue(context.startswith("//text()["))
        for element in generator.CODE_EXCLUSIONS:
            self.assertIn("ancestor-or-self::%s" % element, context)


if __name__ == "__main__":
    unittest.main()
