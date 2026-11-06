import contextlib
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from pasta_clara import OrganizationError, apply_plan, make_plan
from pasta_clara.__main__ import main
from pasta_clara import core


class OrganizerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.source = self.root / 'entrada'
        self.source.mkdir()
        self.destination = self.root / 'saida'

    def write(self, name='nota.txt', data=b'bytes sinteticos\x00\xff'):
        path = self.source / name
        path.write_bytes(data)
        return path

    def test_dry_run_has_no_effects(self):
        original = self.write()
        before = original.read_bytes()
        plan = make_plan(self.source, self.destination)
        self.assertEqual(len(plan.items), 1)
        self.assertFalse(self.destination.exists())
        self.assertEqual(original.read_bytes(), before)
        self.assertEqual(list(self.source.iterdir()), [original])

    def test_copy_preserves_every_byte_and_source(self):
        payload = bytes(range(256)) * 8193
        original = self.write(data=payload)
        plan = make_plan(self.source, self.destination)
        self.assertEqual(apply_plan(plan), 1)
        self.assertEqual(plan.items[0].destination.read_bytes(), payload)
        self.assertEqual(original.read_bytes(), payload)

    def test_collisions_and_repeat_are_predictable(self):
        self.write()
        folder = self.destination / 'documentos'
        folder.mkdir(parents=True)
        (folder / 'nota.txt').write_bytes(b'existente')
        (folder / 'nota__2.txt').mkdir()
        first = make_plan(self.source, self.destination)
        self.assertEqual(first.items[0].destination.name, 'nota__3.txt')
        apply_plan(first)
        second = make_plan(self.source, self.destination)
        self.assertEqual(second.items[0].destination.name, 'nota__4.txt')
        apply_plan(second)
        self.assertEqual((folder / 'nota.txt').read_bytes(), b'existente')

    def test_hidden_directories_and_symlinks_ignored(self):
        self.write('.oculto.txt')
        self.write('visivel.txt')
        (self.source / 'pasta').mkdir()
        (self.source / 'atalho.txt').symlink_to(self.source / 'visivel.txt')
        (self.source / 'quebrado').symlink_to(self.source / 'ausente')
        plan = make_plan(self.source, self.destination)
        self.assertEqual([item.source.name for item in plan.items], ['visivel.txt'])
        self.assertEqual(plan.ignored, 4)

    def test_invalid_source(self):
        for source in [self.root / 'ausente', self.write()]:
            with self.subTest(source=source), self.assertRaises(OrganizationError):
                make_plan(source, self.destination)
        self.assertFalse(self.destination.exists())

    def test_overlap_rejected(self):
        for destination in [self.source, self.source / 'subpasta', self.root]:
            with self.subTest(destination=destination), self.assertRaises(OrganizationError):
                make_plan(self.source, destination)

    def test_symlink_roots_and_destination_ancestors_rejected(self):
        self.write()
        link = self.root / 'link'
        link.symlink_to(self.source, target_is_directory=True)
        for src, dst in [(link, self.destination), (self.source, link / 'sub')]:
            with self.subTest(src=src, dst=dst), self.assertRaises(OrganizationError):
                make_plan(src, dst)
        self.destination.mkdir()
        (self.destination / 'documentos').symlink_to(self.source, target_is_directory=True)
        with self.assertRaises(OrganizationError):
            make_plan(self.source, self.destination)

    def test_broken_symlink_destination_name_not_overwritten(self):
        self.write()
        folder = self.destination / 'documentos'
        folder.mkdir(parents=True)
        (folder / 'nota.txt').symlink_to(self.root / 'inexistente')
        plan = make_plan(self.source, self.destination)
        self.assertEqual(plan.items[0].destination.name, 'nota__2.txt')
        apply_plan(plan)
        self.assertTrue((folder / 'nota.txt').is_symlink())

    def test_source_changed_after_plan_has_no_effects(self):
        original = self.write()
        plan = make_plan(self.source, self.destination)
        original.write_bytes(b'alterado')
        with self.assertRaises(OrganizationError):
            apply_plan(plan)
        self.assertFalse(self.destination.exists())

    def test_destination_created_after_plan_never_overwritten(self):
        self.write()
        plan = make_plan(self.source, self.destination)
        target = plan.items[0].destination
        target.parent.mkdir(parents=True)
        target.write_bytes(b'existente')
        with self.assertRaises(OrganizationError):
            apply_plan(plan)
        self.assertEqual(target.read_bytes(), b'existente')

    def test_copy_error_removes_partial_and_preserves_completed(self):
        first = self.write('a.txt', b'primeiro')
        second = self.write('b.txt', b'segundo')
        plan = make_plan(self.source, self.destination)
        real_copy = core._copy_bytes
        def fail_second(reader, writer, size):
            if str(writer.name).endswith('b.txt'):
                writer.write(b'parcial')
                raise OSError('falha sintética')
            real_copy(reader, writer, size)
        with patch.object(core, '_copy_bytes', side_effect=fail_second):
            with self.assertRaisesRegex(OrganizationError, 'após 1'):
                apply_plan(plan)
        self.assertEqual(first.read_bytes(), b'primeiro')
        self.assertEqual(second.read_bytes(), b'segundo')
        self.assertEqual(plan.items[0].destination.read_bytes(), b'primeiro')
        self.assertFalse(plan.items[1].destination.exists())

    def test_mutation_during_copy_removes_partial(self):
        source = self.write(data=b'original')
        plan = make_plan(self.source, self.destination)
        real_copy = core._copy_bytes
        def mutate(reader, writer, size):
            real_copy(reader, writer, size)
            source.write_bytes(b'alterado depois')
        with patch.object(core, '_copy_bytes', side_effect=mutate):
            with self.assertRaises(OrganizationError):
                apply_plan(plan)
        self.assertFalse(plan.items[0].destination.exists())
        self.assertEqual(source.read_bytes(), b'alterado depois')

    def test_destination_swapped_for_symlink_after_plan_is_rejected(self):
        self.write()
        plan = make_plan(self.source, self.destination)
        self.destination.symlink_to(self.source, target_is_directory=True)
        with self.assertRaises(OrganizationError):
            apply_plan(plan)
        self.assertEqual([p.name for p in self.source.iterdir()], ['nota.txt'])

    def test_source_replaced_by_symlink_after_plan_is_rejected(self):
        original = self.write()
        plan = make_plan(self.source, self.destination)
        other = self.root / 'outro.txt'
        other.write_bytes(b'outro')
        original.unlink()
        original.symlink_to(other)
        with self.assertRaises(OrganizationError):
            apply_plan(plan)
        self.assertFalse(self.destination.exists())
        self.assertEqual(other.read_bytes(), b'outro')

    def test_replaying_same_plan_is_rejected(self):
        self.write()
        plan = make_plan(self.source, self.destination)
        apply_plan(plan)
        with self.assertRaises(OrganizationError):
            apply_plan(plan)
        self.assertEqual(len(list((self.destination / 'documentos').iterdir())), 1)

    def test_limits_fail_before_writes(self):
        self.write('a.txt', b'1234')
        self.write('b.txt', b'5678')
        for constant, limit in [('MAX_FILES', 1), ('MAX_ENTRIES', 1),
                                ('MAX_FILE_BYTES', 3), ('MAX_TOTAL_BYTES', 7)]:
            with self.subTest(constant=constant), patch.object(core, constant, limit):
                with self.assertRaises(OrganizationError):
                    make_plan(self.source, self.destination)
                self.assertFalse(self.destination.exists())

    def test_grouping_case_and_unknown_extension(self):
        for name in ['foto.JPG', 'README', 'dados.xyz', 'script.py', 'arquivo.tar.gz']:
            self.write(name)
        plan = make_plan(self.source, self.destination)
        groups = {item.source.name: item.destination.parent.name for item in plan.items}
        self.assertEqual(groups, {'foto.JPG': 'imagens', 'README': 'sem_extensao',
                                 'dados.xyz': 'outros', 'script.py': 'codigo',
                                 'arquivo.tar.gz': 'compactados'})

    def test_empty_folder_does_not_create_destination(self):
        plan = make_plan(self.source, self.destination)
        self.assertEqual(apply_plan(plan), 0)
        self.assertFalse(self.destination.exists())

    def test_cli_defaults_to_simulation_and_apply_is_explicit(self):
        self.write()
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            self.assertEqual(main([str(self.source), str(self.destination)]), 0)
        self.assertIn('SIMULAÇÃO', output.getvalue())
        self.assertFalse(self.destination.exists())
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(main([str(self.source), str(self.destination), '--aplicar']), 0)
        self.assertTrue((self.destination / 'documentos' / 'nota.txt').is_file())

    def test_cli_rejects_abbreviated_apply_without_writing(self):
        original = self.write()
        before = original.read_bytes()
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as error:
                main([str(self.source), str(self.destination), '--a'])
        self.assertEqual(error.exception.code, 2)
        self.assertFalse(self.destination.exists())
        self.assertEqual(original.read_bytes(), before)

    def test_cli_reports_validation_error(self):
        with contextlib.redirect_stderr(io.StringIO()) as errors:
            self.assertEqual(main([str(self.root / 'ausente'), str(self.destination)]), 1)
        self.assertIn('Erro:', errors.getvalue())


if __name__ == '__main__':
    unittest.main()
