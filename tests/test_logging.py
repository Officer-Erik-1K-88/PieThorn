import io
import unittest

from piethorn.logging.counter import Counter, CounterBehavior, Percent
from piethorn.logging.logger import Logger


class LoggerTests(unittest.TestCase):
    def test_logger_writes_messages_and_tracks_counts(self):
        logger = Logger(debug_level=1)
        stream = io.StringIO()
        logger.set_default_file("default", stream)
        logger.set_default_file("log", stream)
        logger.set_default_file("INFO", stream)

        self.assertTrue(logger.base_log("alpha", "beta", file=stream, end=""))
        self.assertEqual(stream.getvalue(), "alpha beta")

        stream.seek(0)
        stream.truncate(0)

        self.assertTrue(logger.info("hello", file=stream))
        self.assertEqual(stream.getvalue(), "[INFO] hello\n")
        self.assertEqual(logger.log_count.current, 1)
        self.assertEqual(logger.infos.current, 1)

    def test_logger_validates_required_base_log_arguments(self):
        logger = Logger()
        with self.assertRaisesRegex(RuntimeError, "at least one"):
            logger.base_log()


class CounterTests(unittest.TestCase):
    def test_counter_add_tick_compare_and_reset(self):
        counter = Counter("jobs", visible=1, hidden=2, only_visible=False, step=0.5)

        counter.add(2)
        counter.float_add(1.25, hidden=True)
        counter.tick(2, worth=2)
        counter.non_linear_tick(2, worth=1)

        self.assertEqual(counter.visible, 5)
        self.assertEqual(counter.hidden, 3)
        self.assertAlmostEqual(counter.decimal, 1.0)
        self.assertEqual(counter.current, 9.0)
        self.assertTrue(counter > 0)
        self.assertEqual(counter.compare(10), -1)

        counter.reset()
        self.assertEqual(counter.current, 0)

    def test_counter_behavior_child_inheritance(self):
        parent = CounterBehavior(reset_on_reset=False, remove_on_reset=True, affect_child=True)
        child = parent.child_behavior()

        self.assertTrue(child.affected_by_parent)
        self.assertFalse(child.reset_on_reset)
        self.assertTrue(child.remove_on_reset)
        self.assertTrue(parent.reset_allowed())


class PercentTests(unittest.TestCase):
    def test_percent_supports_child_progress_and_reset(self):
        parent = Percent("task", current=10, cap=20, step=5)
        child = parent("child", cap=5, worth=4)

        child.current = 5
        child.check()

        self.assertTrue(child.is_complete())
        self.assertTrue(parent.is_parent())
        self.assertTrue(child.is_child())
        self.assertEqual(child.long_name, "task ; child")
        self.assertEqual(parent.current, 22)
        self.assertEqual(parent.children[0], child)

        parent.reset()
        self.assertEqual(parent.current, 0)
        self.assertEqual(len(parent.children), 0)

    def test_percent_percent_property_clamps_and_validates(self):
        percent = Percent("download", current=5, cap=10, step=2)
        percent.percent = 0.5

        self.assertEqual(percent.current, 5)
        self.assertEqual(percent.larger_percent(), 50)
        self.assertFalse(bool(percent))

        with self.assertRaisesRegex(ValueError, "greater than one"):
            percent.percent = 1.1


if __name__ == "__main__":
    unittest.main()
