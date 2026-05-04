import json
import tempfile
import unittest
from pathlib import Path

from piethorn.filehandle import File as PathFile
from piethorn.filehandle import JsonFile, JsonFileOptions
from piethorn.filehandle.filehandling import File, JSONEncoder
from piethorn.filehandle.importer import (
    CallerRoot,
    ModuleInfo,
    change_source_dir,
    convert_dot_notation,
    load_target_module,
    to_path,
)


class FileTests(unittest.TestCase):
    def test_file_can_create_children_and_edit_contents(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = File(tmp, find_children=False)
            folder = root.create_child("data")
            child = root.create_child("data/example.txt", "hello")

            child.write("first", line=0, insert=True)
            child.write("replaced", line=1, insert=False)

            self.assertTrue(folder.isdir())
            self.assertTrue(child.isfile())
            self.assertEqual("".join(child.read()), "first\nreplaced\n")
            self.assertEqual(child.rig(lambda handle: handle.read()), "first\nreplaced\n")
            self.assertEqual([entry.file_path.split("/")[-1] for entry in root.children.dirs()], ["data"])
            self.assertEqual([entry.file_path.split("/")[-1] for entry in folder.children.files()], ["example.txt"])

    def test_file_enforces_read_only_path_property_and_rig_callable(self):
        with tempfile.TemporaryDirectory() as tmp:
            file = File(Path(tmp) / "sample.txt", find_children=False)
            file.build("content")

            with self.assertRaises(NotImplementedError):
                file.file_path = "elsewhere.txt"
            with self.assertRaisesRegex(TypeError, "callable"):
                file.rig("not-callable")

    def test_json_encoder_uses_stdlib_compatible_compact_dump(self):
        encoded = JSONEncoder(sort_keys=True).dumps({"b": [1], "a": {"c": 2}})

        self.assertEqual(json.loads(encoded), {"a": {"c": 2}, "b": [1]})

    def test_discovered_children_are_relative_to_parent_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root_path = Path(tmp)
            (root_path / "sample.txt").write_text("content")

            root = File(root_path)

            self.assertEqual(root.children.files()[0].file_path, str(root_path / "sample.txt"))


class PathFileTests(unittest.TestCase):
    def test_append_text_preserves_existing_content_with_atomic_writes(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sample.txt"
            path.write_text("old")

            written = PathFile(path).append_text("new")

            self.assertEqual(written, 3)
            self.assertEqual(path.read_text(), "oldnew")

    def test_append_bytes_preserves_existing_content_with_atomic_writes(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sample.bin"
            path.write_bytes(b"old")

            written = PathFile(path).append_bytes(b"new")

            self.assertEqual(written, 3)
            self.assertEqual(path.read_bytes(), b"oldnew")

    def test_exclusive_write_content_raises_when_target_exists(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sample.txt"
            path.write_text("old")

            with self.assertRaises(FileExistsError):
                PathFile(path).write_content("x", "new")

            self.assertEqual(path.read_text(), "old")

    def test_exclusive_write_content_creates_missing_target_with_atomic_writes(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sample.txt"

            written = PathFile(path).write_content("x", "new")

            self.assertEqual(written, 3)
            self.assertEqual(path.read_text(), "new")

    def test_read_update_write_content_preserves_unwritten_content(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sample.txt"
            path.write_text("abcdef")

            written = PathFile(path).write_content("r+", "XY")

            self.assertEqual(written, 2)
            self.assertEqual(path.read_text(), "XYcdef")

    def test_read_update_write_content_requires_existing_target(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sample.txt"

            with self.assertRaises(FileNotFoundError):
                PathFile(path).write_content("r+", "XY")


class JsonFileTests(unittest.TestCase):
    def test_backup_preserves_previous_json_when_atomic_write_is_enabled(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sample.json"
            path.write_text('{"old": true}\n')
            options = JsonFileOptions(backup=True)

            JsonFile(path, options=options).save({"new": True})

            self.assertEqual(json.loads(path.read_text()), {"new": True})
            self.assertEqual(json.loads(path.with_suffix(".json.bak").read_text()), {"old": True})

    def test_allow_trailing_bytes_loads_first_json_value_after_leading_whitespace(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sample.json"
            path.write_text('\n  {"ok": true} trailing')
            options = JsonFileOptions(allow_trailing_bytes=True)

            self.assertEqual(JsonFile(path, options=options).load(), {"ok": True})


class ImporterTests(unittest.TestCase):
    def test_caller_root_and_path_helpers_resolve_against_source_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package = root / "pkg"
            package.mkdir()
            (package / "__init__.py").write_text("VALUE = 7\n")
            (package / "child.py").write_text("NAME = 'child'\n")

            caller_root = CallerRoot(root, "pkg")

            self.assertEqual(caller_root.source_dir, package)
            self.assertEqual(to_path("child.py", sub_to_source=True, project_root=caller_root), package / "child.py")
            self.assertTrue(change_source_dir("pkg", path=root, project_root=caller_root))
            self.assertEqual(convert_dot_notation("child", project_root=caller_root), "child.py")

    def test_module_info_and_load_target_module_expose_package_tree(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package = root / "pkg"
            package.mkdir()
            (package / "__init__.py").write_text("VALUE = 7\n")
            (package / "child.py").write_text("NAME = 'child'\n")

            info = ModuleInfo(package)
            module = info.module
            loaded = load_target_module("standalone_child", package / "child.py")

            self.assertEqual(info.import_name, "pkg")
            self.assertTrue(info.is_built)
            self.assertEqual(module.VALUE, 7)
            self.assertEqual(module.child.NAME, "child")
            self.assertIn("child", dir(module))
            self.assertEqual(loaded.NAME, "child")


if __name__ == "__main__":
    unittest.main()
