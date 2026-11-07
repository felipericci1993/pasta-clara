"""Regressões de caminhos com '..'; todos os dados são temporários e fictícios."""
import contextlib
import io
from pathlib import Path
import tempfile
import unittest

from pasta_clara import OrganizationError, apply_plan, make_plan
from pasta_clara.__main__ import main


class PathValidationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.source = self.root / 'entrada'
        self.source.mkdir()
        self.original = self.source / 'nota.txt'
        self.payload = b'conteudo sintetico preservado'
        self.original.write_bytes(self.payload)
        self.destination = self.root / 'saida'

    def assert_unchanged(self):
        self.assertEqual(self.original.read_bytes(), self.payload)
        self.assertEqual(list(self.source.iterdir()), [self.original])
        self.assertFalse(self.destination.exists())

    def make_link(self):
        target = self.root / 'outra' / 'subpasta'
        target.mkdir(parents=True)
        link = self.root / 'atalho'
        link.symlink_to(target, target_is_directory=True)
        return link

    def test_source_symlink_before_parent_rejected(self):
        source = self.make_link() / '..' / 'entrada'
        # The OS would look in outra/entrada, not root/entrada.
        self.assertEqual(source.resolve(), self.root / 'outra' / 'entrada')
        with self.assertRaisesRegex(OrganizationError, 'Link simbólico'):
            make_plan(source, self.destination)
        self.assert_unchanged()

    def test_destination_symlink_before_parent_rejected(self):
        destination = self.make_link() / '..' / 'saida'
        with self.assertRaisesRegex(OrganizationError, 'Link simbólico'):
            make_plan(self.source, destination)
        self.assertFalse((self.root / 'outra' / 'saida').exists())
        self.assert_unchanged()

    def test_relative_symlink_before_parent_rejected(self):
        self.make_link()
        with contextlib.chdir(self.root):
            for source, destination in [
                    ('atalho/../entrada', 'saida'),
                    ('entrada', 'atalho/../saida')]:
                with self.subTest(source=source, destination=destination):
                    with self.assertRaisesRegex(OrganizationError, 'Link simbólico'):
                        make_plan(source, destination)
        self.assert_unchanged()

    def test_broken_symlink_before_parent_rejected(self):
        link = self.root / 'quebrado'
        link.symlink_to(self.root / 'ausente', target_is_directory=True)
        for source, destination in [
                (link / '..' / 'entrada', self.destination),
                (self.source, link / '..' / 'saida')]:
            with self.subTest(source=source, destination=destination):
                with self.assertRaisesRegex(OrganizationError, 'Link simbólico'):
                    make_plan(source, destination)
        self.assert_unchanged()

    def test_file_before_parent_rejected(self):
        file = self.root / 'arquivo.txt'
        file.write_bytes(b'nao e pasta')
        for source, destination in [
                (file / '..' / 'entrada', self.destination),
                (self.source, file / '..' / 'saida')]:
            with self.subTest(source=source, destination=destination):
                with self.assertRaises(OrganizationError):
                    make_plan(source, destination)
        self.assertEqual(file.read_bytes(), b'nao e pasta')
        self.assert_unchanged()

    def test_missing_directory_before_parent_rejected(self):
        missing = self.root / 'ausente'
        for source, destination in [
                (missing / '..' / 'entrada', self.destination),
                (self.source, missing / '..' / 'saida')]:
            with self.subTest(source=source, destination=destination):
                with self.assertRaises(OrganizationError):
                    make_plan(source, destination)
        self.assertFalse(missing.exists())
        self.assert_unchanged()

    def test_real_parent_components_are_normalized(self):
        folder = self.root / 'pasta-real'
        folder.mkdir()
        with contextlib.chdir(self.root):
            plan = make_plan('pasta-real/../entrada', 'pasta-real/../saida')
        self.assertEqual(plan.source, self.source)
        self.assertEqual(plan.destination, self.destination)
        self.assert_unchanged()
        self.assertEqual(apply_plan(plan), 1)
        self.assertEqual(plan.items[0].destination.read_bytes(), self.payload)
        self.assertEqual(self.original.read_bytes(), self.payload)

    def test_parent_components_do_not_hide_overlap(self):
        folder = self.root / 'pasta-real'
        folder.mkdir()
        for destination in [folder / '..' / 'entrada',
                            folder / '..' / 'entrada' / 'subpasta',
                            folder / '..']:
            with self.subTest(destination=destination):
                with self.assertRaises(OrganizationError):
                    make_plan(self.source, destination)
        self.assert_unchanged()

    def test_cli_apply_rejects_hidden_symlink_without_writes(self):
        destination = self.make_link() / '..' / 'saida'
        errors = io.StringIO()
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(errors):
            code = main([str(self.source), str(destination), '--aplicar'])
        self.assertEqual(code, 1)
        self.assertIn('Link simbólico', errors.getvalue())
        self.assertFalse((self.root / 'outra' / 'saida').exists())
        self.assert_unchanged()


if __name__ == '__main__':
    unittest.main()
