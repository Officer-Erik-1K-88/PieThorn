import json
import os
import tempfile
import unittest
from pathlib import Path

from piethorn.filehandle import BasePath, FileOptions, Folder
from piethorn.filehandle import File as PathFile
from piethorn.filehandle import JsonDecodeError, JsonFile, JsonFileOptions
from piethorn.filehandle.content import ContentWrapper, fd_closed, fd_open, used_file_descriptor
from piethorn.filehandle.filehandling import File, JSONEncoder, JSONFile
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

    def test_legacy_json_encoder_formats_complex_values_and_rejects_cycles(self):
        encoded = json.dumps({"outer": [{"inner": [1, 2]}, 3]}, cls=JSONEncoder, indent=2)

        self.assertEqual(json.loads(encoded), {"outer": [{"inner": [1, 2]}, 3]})

        value = []
        value.append(value)
        with self.assertRaises(ValueError):
            json.dumps(value, cls=JSONEncoder, indent=2)

    def test_discovered_children_are_relative_to_parent_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root_path = Path(tmp)
            (root_path / "sample.txt").write_text("content")

            root = File(root_path)

            self.assertEqual(root.children.files()[0].file_path, str(root_path / "sample.txt"))

    def test_legacy_json_file_persists_mapping_and_nested_views(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sample.json"
            json_file = JSONFile(str(path))

            json_file["root"] = {"leaf": 1}
            nested = json_file["root"]
            nested["leaf"] = 2
            json_file.setdefault("created", {"value": 3})

            self.assertEqual(JSONFile(str(path)).get("root").fast_get("leaf"), 2)
            self.assertEqual(json.loads(path.read_text()), {"root": {"leaf": 2}, "created": {"value": 3}})

            self.assertEqual(json_file.pop("created"), {"value": 3})
            self.assertEqual(list(json_file.keys()), ["root"])


class BasePathAndFolderTests(unittest.TestCase):
    def test_base_path_create_file_and_folder_and_remove_tree(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            file_path = BasePath(root / "nested" / "sample.txt")
            folder_path = BasePath(root / "tree")

            file_path.create(parents=True)
            folder_path.create(force_folder=True)
            (root / "tree" / "child.txt").write_text("child")

            self.assertTrue((root / "nested" / "sample.txt").is_file())
            self.assertTrue((root / "tree").is_dir())

            folder_path.remove()

            self.assertFalse((root / "tree").exists())

    def test_base_path_remove_missing_honors_missing_ok(self):
        with tempfile.TemporaryDirectory() as tmp:
            missing = BasePath(Path(tmp) / "missing.txt")

            missing.remove(missing_ok=True)
            with self.assertRaises(FileNotFoundError):
                missing.remove()

    def test_base_path_get_proper_returns_file_or_folder_wrappers(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            file_path = root / "sample.txt"
            folder_path = root / "folder"
            file_path.write_text("content")
            folder_path.mkdir()

            self.assertIsInstance(BasePath(file_path).get_proper(), PathFile)
            self.assertIsInstance(BasePath(folder_path).get_proper(), Folder)
            self.assertIsInstance(BasePath(root / "virtual").get_proper(forced="file"), PathFile)
            self.assertIsInstance(BasePath(root / "virtual").get_proper(forced="folder"), Folder)

    def test_folder_lists_filters_walks_sizes_and_deletes_children(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            folder = Folder(root)
            (root / "a.txt").write_text("abc")
            sub = root / "sub"
            sub.mkdir()
            (sub / "b.txt").write_text("de")

            names = sorted(entry.name for entry in folder.list())
            file_names = [entry.name for entry in folder.list(folders=False)]
            folder_names = [entry.name for entry in folder.list(files=False)]
            walked = list(folder.walk())

            self.assertEqual(names, ["a.txt", "sub"])
            self.assertEqual(file_names, ["a.txt"])
            self.assertEqual(folder_names, ["sub"])
            self.assertEqual(folder.size, 5)
            self.assertEqual(walked[0][0].path, root)
            self.assertEqual([f.name for f in walked[0][2]], ["a.txt"])

            folder.delete("sub")

            self.assertFalse(sub.exists())

    def test_folder_factory_methods_create_and_validate_children(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Folder(tmp)

            child = folder.file("sample.txt", create=True)
            nested = folder.subfolder("nested", create=True)

            self.assertTrue(child.path.is_file())
            self.assertTrue(nested.path.is_dir())
            with self.assertRaises(FileNotFoundError):
                folder.file("missing.txt", must_exist=True)
            with self.assertRaises(FileNotFoundError):
                folder.subfolder("missing", must_exist=True)


class PathFileTests(unittest.TestCase):
    def test_public_file_helpers_read_write_touch_and_size(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "nested" / "sample.txt"
            file = PathFile(path)

            file.touch()
            self.assertEqual(file.size, 0)

            file.write("hello")

            self.assertEqual(file.read(), "hello")
            self.assertEqual(file.size, 5)

            file.write_bytes(b"\x00\x01")

            self.assertEqual(file.read(binary=True), b"\x00\x01")

    def test_write_content_accepts_iterables_and_reports_bytes_written(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sample.txt"

            written = PathFile(path).write_content("w", ["a", "é", "c"])

            self.assertEqual(written, len("aéc".encode("utf-8")))
            self.assertEqual(path.read_text(), "aéc")

    def test_write_content_rejects_read_only_modes_and_wrong_data_types(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sample.txt"
            file = PathFile(path)

            with self.assertRaises(ValueError):
                file.write_content("r", "content")
            with self.assertRaises(TypeError):
                file.write_text(b"bytes")
            with self.assertRaises(TypeError):
                file.write_bytes("text")

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

    def test_append_update_and_exclusive_modes_work_without_atomic_writes(self):
        with tempfile.TemporaryDirectory() as tmp:
            options = FileOptions(atomic_write=False)
            path = Path(tmp) / "sample.txt"
            file = PathFile(path, options=options)

            self.assertEqual(file.write_content("x", "abc"), 3)
            self.assertEqual(file.append_text("d"), 1)
            self.assertEqual(file.write_content("r+", "XY"), 2)

            self.assertEqual(path.read_text(), "XYcd")

    def test_backup_preserves_previous_content_before_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sample.txt"
            path.write_text("old")
            file = PathFile(path, options=FileOptions(backup=True))

            file.write_text("new")

            self.assertEqual(path.read_text(), "new")
            self.assertEqual(path.with_suffix(".txt.bak").read_text(), "old")

    def test_copy_to_and_move_to_handle_destinations_and_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source.txt"
            source.write_text("content")
            dest_dir = root / "dest"
            dest_dir.mkdir()

            copied = PathFile(source).copy_to(dest_dir)

            self.assertEqual(copied.path, dest_dir / "source.txt")
            self.assertEqual(copied.read(), "content")
            with self.assertRaises(FileExistsError):
                PathFile(source).copy_to(copied.path)

            moved = PathFile(source).move_to(root / "moved.txt")

            self.assertFalse(source.exists())
            self.assertEqual(moved.path, root / "moved.txt")
            self.assertEqual(moved.read(), "content")

    def test_iter_content_chunks_binary_and_unicode_text_by_byte_size(self):
        with tempfile.TemporaryDirectory() as tmp:
            text_path = Path(tmp) / "text.txt"
            text_path.write_text("éé\nabc", encoding="utf-8")
            binary_path = Path(tmp) / "data.bin"
            binary_path.write_bytes(b"abcdef")

            text_chunks = list(PathFile(text_path).iter_content(chunk_size=4))
            binary_chunks = list(PathFile(binary_path).iter_content(binary=True, chunk_size=2))

            self.assertEqual([(chunk.chunk, chunk.size, chunk.line_end) for chunk in text_chunks], [
                ("éé", 4, False),
                ("\n", 1, True),
                ("abc", 3, True),
            ])
            self.assertEqual([chunk.chunk for chunk in binary_chunks], [b"ab", b"cd", b"ef"])
            self.assertTrue(all(not chunk.line_end for chunk in binary_chunks))

    def test_open_returns_content_wrapper_and_tracks_descriptor_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sample.txt"
            path.write_text("content")

            with PathFile(path).open("r") as handle:
                fd = handle.fileno()
                self.assertIsInstance(handle, ContentWrapper)
                self.assertTrue(used_file_descriptor(fd))
                self.assertTrue(fd_open(fd))
                self.assertEqual(handle.read(), "content")

            self.assertTrue(fd_closed(fd, path=path))


class JsonFileTests(unittest.TestCase):
    def test_load_missing_file_returns_default_or_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sample.json"
            json_file = JsonFile(path)

            self.assertEqual(json_file.load(default={"missing": True}), {"missing": True})
            with self.assertRaises(FileNotFoundError):
                json_file.load()

    def test_invalid_json_raises_package_decode_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sample.json"
            path.write_text("{invalid")

            with self.assertRaises(JsonDecodeError):
                JsonFile(path).load()

    def test_save_creates_parents_and_respects_formatting_options(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "nested" / "sample.json"
            options = JsonFileOptions(indent=None, sort_keys=True, ensure_ascii=True, newline="")

            JsonFile(path, options=options).save({"é": 1, "a": 2})

            self.assertEqual(path.read_text(), '{"a": 2, "\\u00e9": 1}')

    def test_backup_preserves_previous_json_when_atomic_write_is_enabled(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sample.json"
            path.write_text('{"old": true}\n')
            options = JsonFileOptions(backup=True)

            JsonFile(path, options=options).save({"new": True})

            self.assertEqual(json.loads(path.read_text()), {"new": True})
            self.assertEqual(json.loads(path.with_suffix(".json.bak").read_text()), {"old": True})

    def test_backup_preserves_previous_json_when_atomic_write_is_disabled(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sample.json"
            path.write_text('{"old": true}\n')
            options = JsonFileOptions(backup=True, atomic_write=False)

            JsonFile(path, options=options).save({"new": True})

            self.assertEqual(json.loads(path.read_text()), {"new": True})
            self.assertEqual(json.loads(path.with_suffix(".json.bak").read_text()), {"old": True})

    def test_allow_trailing_bytes_loads_first_json_value_after_leading_whitespace(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sample.json"
            path.write_text('\n  {"ok": true} trailing')
            options = JsonFileOptions(allow_trailing_bytes=True)

            self.assertEqual(JsonFile(path, options=options).load(), {"ok": True})

    def test_get_set_update_and_edit_require_object_roots_where_documented(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sample.json"
            json_file = JsonFile(path)

            json_file.set("a", 1)
            self.assertEqual(json_file.get("a"), 1)
            self.assertEqual(json_file.get("missing", "fallback"), "fallback")

            updated = json_file.update(lambda data: {**data, "b": 2}, default={})
            self.assertEqual(updated, {"a": 1, "b": 2})

            with json_file.edit(default={}) as data:
                data["c"] = 3

            self.assertEqual(json_file.load(), {"a": 1, "b": 2, "c": 3})

            path.write_text("[1, 2, 3]")
            with self.assertRaises(TypeError):
                json_file.get("a")
            with self.assertRaises(TypeError):
                json_file.set("a", 1)

    def test_edit_does_not_save_when_context_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sample.json"
            JsonFile(path).save({"saved": True})

            with self.assertRaises(RuntimeError):
                with JsonFile(path).edit(default={}) as data:
                    data["saved"] = False
                    raise RuntimeError("abort")

            self.assertEqual(JsonFile(path).load(), {"saved": True})

    def test_lock_timeout_raises_when_lockfile_already_exists(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sample.json"
            lock_path = path.with_suffix(".json.lock")
            lock_path.write_text("locked")
            options = JsonFileOptions(lock_timeout=0, lock_poll_interval=0)

            with self.assertRaises(Exception) as ctx:
                JsonFile(path, options=options).save({"blocked": True})

            self.assertEqual(type(ctx.exception).__name__, "JsonLockError")


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

    def test_to_path_absolute_strict_source_validation_and_resolution(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "src"
            outside = root / "outside.py"
            source.mkdir()
            outside.write_text("")
            caller_root = CallerRoot(root, "src")

            self.assertEqual(to_path(source / "child.py", sub_to_source=True, project_root=caller_root), source / "child.py")
            with self.assertRaises(RuntimeError):
                to_path(outside, sub_to_source=True, strict=True, project_root=caller_root)
            self.assertEqual(to_path("missing.py", sub_to_source=True, resolve=False, project_root=caller_root), source / "missing.py")

    def test_change_source_dir_reports_false_for_missing_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            caller_root = CallerRoot(root)

            self.assertFalse(change_source_dir("missing", project_root=caller_root))
            self.assertEqual(caller_root.path, root)
            self.assertIsNone(caller_root._source_dir)

    def test_convert_dot_notation_accepts_packages_and_raises_for_missing_modules(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package = root / "pkg"
            nested = package / "nested"
            nested.mkdir(parents=True)
            (nested / "__init__.py").write_text("")
            caller_root = CallerRoot(root, "pkg")

            self.assertEqual(convert_dot_notation("nested", project_root=caller_root), "nested")
            with self.assertRaises(FileNotFoundError):
                convert_dot_notation("missing.module", project_root=caller_root)

    def test_load_target_module_rejects_missing_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(FileNotFoundError):
                load_target_module("missing", Path(tmp) / "missing.py")

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

    def test_module_info_sanitizes_names_and_builds_submodules_once(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            module_path = root / "my module.py"
            module_path.write_text("VALUE = 9\n")
            info = ModuleInfo(module_path, name=" custom name ")

            info.build_module()
            first_module = info.module
            info.build_module()

            self.assertEqual(info.name, "custom_name")
            self.assertEqual(info.import_name, "custom_name")
            self.assertIs(first_module, info.module)
            self.assertEqual(first_module.VALUE, 9)


if __name__ == "__main__":
    unittest.main()
