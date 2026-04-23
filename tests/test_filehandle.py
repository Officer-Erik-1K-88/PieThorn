import json
import tempfile
import unittest
from pathlib import Path

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
