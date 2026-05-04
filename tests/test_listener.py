import unittest

from piethorn.collections.listener import (
    GLOBAL_LISTENERS,
    DEFAULT_EVENT_BUILDER,
    Event,
    EventBuilder,
    EventEnd,
    GetListenerError,
    Listenable,
    Listener,
    ListenerBuilder,
    ListenerHolder,
    MutableListenerSequence,
    listens,
)
from piethorn.collections.listener.listens import DEFAULT_LISTENS_FOR, ListensFor, system_listens


class ListenerBuilderTests(unittest.TestCase):
    def test_listener_builder_normalizes_names_and_supports_index_lookup(self):
        builder = ListenerBuilder()
        alpha = builder.add("alpha")
        numbered = builder.add(3)

        self.assertIs(builder.get("alpha"), alpha)
        self.assertIs(builder.at(0), alpha)
        self.assertIs(builder.get("event_0"), alpha)
        self.assertIs(builder.get("event_3"), numbered)
        self.assertTrue(builder.has("alpha"))
        self.assertFalse(builder.has("missing"))

        with self.assertRaisesRegex(GetListenerError, "Listener 'missing' not found"):
            builder.get("missing")

    def test_listener_builder_add_replace_and_remove(self):
        builder = ListenerBuilder()
        first = builder.add("same")
        duplicate = builder.add("same")
        replacement = builder.add("same", replace=True)

        self.assertIs(duplicate, first)
        self.assertIsNot(replacement, first)
        self.assertIs(builder.get("same"), replacement)
        self.assertIs(builder.remove("same"), replacement)
        self.assertEqual(builder.remove("same", "default"), "default")

    def test_listener_rejects_non_callable_callers(self):
        listener = Listener("event")

        with self.assertRaisesRegex(TypeError, "isn't callable"):
            listener.add(object())

    def test_listener_builder_get_at_and_pop_fallbacks(self):
        builder = ListenerBuilder()
        alpha = builder.add("alpha")
        beta = builder.add("beta")

        self.assertIs(builder.get_at("alpha"), alpha)
        self.assertIs(builder.get_at(1), beta)
        self.assertIs(builder.get_at("event_1"), beta)
        self.assertIs(builder.pop(0), alpha)
        self.assertEqual(builder.pop(10, "default"), "default")

        with self.assertRaisesRegex(GetListenerError, "Listener 'missing' not found"):
            builder.get_at("missing")


class EventBuilderTests(unittest.TestCase):
    def test_event_builder_names_events_from_listener_names(self):
        listener = Listener("created", EventBuilder())
        event = listener.event((1,), {"x": 2}, "result", lambda: None)

        self.assertEqual(event.name, "EventCreated")
        self.assertIs(event.listener, listener)
        self.assertIs(event.caller, listener)
        self.assertEqual(event.args, (1,))
        self.assertEqual(event.kwargs, {"x": 2})
        self.assertEqual(event.returned, "result")
        self.assertTrue(callable(event.called_method))

    def test_default_event_builder_copies_to_new_listeners(self):
        one = Listener("one")
        two = Listener("two")

        self.assertIsNot(one.event_builder, DEFAULT_EVENT_BUILDER)
        self.assertIsNot(two.event_builder, DEFAULT_EVENT_BUILDER)
        self.assertIsNot(one.event_builder, two.event_builder)
        self.assertEqual(one.event_builder.name, "EventOne")
        self.assertEqual(two.event_builder.name, "EventTwo")

    def test_static_builder_reuses_event_until_cleared(self):
        listener = Listener("static", EventBuilder(static=True))
        seen = []

        listener.add(lambda event: seen.append(event) or True)
        listener.add(lambda event: seen.append(event) or True)
        listener.use(("a",), {}, None, lambda: None)

        self.assertEqual(len(seen), 2)
        self.assertIs(seen[0], seen[1])
        self.assertFalse(seen[0].active)

    def test_non_static_builder_creates_event_per_caller(self):
        listener = Listener("dynamic", EventBuilder(static=False))
        seen = []

        listener.add(lambda event: seen.append(event) or True)
        listener.add(lambda event: seen.append(event) or True)
        listener.use((), {}, None, lambda: None)

        self.assertEqual(len(seen), 2)
        self.assertIsNot(seen[0], seen[1])

    def test_clear_active_event_raises(self):
        builder = EventBuilder(static=True)
        listener = Listener("active", builder)
        event = listener.event((), {}, None, lambda: None)
        event._in_use = True

        with self.assertRaisesRegex(RuntimeError, "Cannot clear an active event"):
            listener.event_builder.clear_event()

        event._in_use = False
        self.assertIs(listener.event_builder.clear_event(), event)

    def test_event_pass_values_ignores_updates_while_active(self):
        event = Event(EventBuilder(), Listener("manual"))
        event.pass_values(("first",), {"x": 1}, "returned", lambda: None)
        event._in_use = True
        event.pass_values(("second",), {"x": 2}, "ignored", None)

        self.assertEqual(event.args, ("first",))
        self.assertEqual(event.kwargs, {"x": 1})
        self.assertEqual(event.returned, "returned")

    def test_stop_current_force_raises_event_end_without_ending_chain(self):
        event = Event(EventBuilder(), Listener("manual"))

        with self.assertRaises(EventEnd) as raised:
            event.stop_current()

        self.assertIs(raised.exception.event, event)
        self.assertTrue(event.end_current)
        self.assertFalse(event.end_chain)

    def test_non_copying_event_builder_moves_between_listeners(self):
        builder = EventBuilder(static=True, copies_to_new=False)
        first = Listener("first", builder)
        second = Listener("second", builder)

        self.assertIs(first.event_builder, builder)
        self.assertIs(second.event_builder, builder)
        self.assertIs(builder.listener, second)
        self.assertEqual(builder.name, "EventSecond")


class ListenerUseTests(unittest.TestCase):
    def test_use_passes_event_context_to_each_caller(self):
        listener = Listener("context")
        calls = []

        def method(value, *, option=False):
            return value, option

        def caller(event):
            calls.append(
                (
                    event.name,
                    event.args,
                    event.kwargs,
                    event.returned,
                    event.called_method,
                    event.active,
                )
            )
            return True

        listener.add(caller)
        listener.use(("value",), {"option": True}, ("value", True), method)

        self.assertEqual(calls, [("EventContext", ("value",), {"option": True}, ("value", True), method, True)])

    def test_use_stops_chain_when_caller_returns_false(self):
        listener = Listener("stop")
        calls = []

        listener.add(lambda event: calls.append("first") or False)
        listener.add(lambda event: calls.append("second") or True)
        listener.use((), {}, None, lambda: None)

        self.assertEqual(calls, ["first"])

    def test_event_end_finishes_current_caller_then_stops_chain(self):
        listener = Listener("end")
        calls = []

        def first(event):
            calls.append("first")
            event.end()
            calls.append("after-end")
            return True

        listener.add(first)
        listener.add(lambda event: calls.append("second") or True)
        listener.use((), {}, None, lambda: None)

        self.assertEqual(calls, ["first", "after-end"])

    def test_forced_event_end_can_stop_the_chain(self):
        listener = Listener("force")
        calls = []

        def first(event):
            calls.append("first")
            event.end(force=True)
            calls.append("after-end")
            return True

        listener.add(first)
        listener.add(lambda event: calls.append("second") or True)
        listener.use((), {}, None, lambda: None)

        self.assertEqual(calls, ["first"])

    def test_listener_callable_reuses_incoming_event(self):
        source = Listener("source")
        target = Listener("target")
        seen = []

        target.add(lambda event: seen.append((event.name, event.caller.name)) or False)
        source.add(target)
        source.add(lambda event: seen.append("after-target") or True)
        source.use((), {}, None, lambda: None)

        self.assertEqual(seen, [("EventSource", "source")])

    def test_stop_current_skips_rest_of_listener_callable_chain(self):
        source = Listener("source")
        target = Listener("target")
        seen = []

        def first(event):
            seen.append("target-first")
            event.stop_current(force=False)
            return True

        target.add(first)
        target.add(lambda event: seen.append("target-second") or True)
        source.add(target)
        source.add(lambda event: seen.append("source-after-target") or True)
        source.use((), {}, None, lambda: None)

        self.assertEqual(seen, ["target-first", "source-after-target"])


class ListenableTests(unittest.TestCase):
    def test_listenable_adds_named_listeners_and_triggers_them(self):
        class Thing(Listenable):
            def __init__(self):
                super().__init__("changed")

            @listens("changed")
            def change(self, value, *, flag=False):
                return value.upper() if flag else value

        thing = Thing()
        calls = []
        thing.add_listener("changed", lambda event: calls.append(event) or True)

        self.assertEqual(thing.change("ok", flag=True), "OK")
        self.assertEqual(thing.listener_count, 1)
        self.assertEqual(calls[0].args, ("ok",))
        self.assertEqual(calls[0].kwargs, {"flag": True})
        self.assertEqual(calls[0].returned, "OK")
        self.assertEqual(calls[0].called_method("again", flag=True), "AGAIN")

    def test_listenable_remove_listener_stops_future_notifications(self):
        holder = ListenerHolder("changed")
        calls = []

        def caller(event):
            calls.append(event.name)
            return True

        holder.add_listener("changed", caller)
        holder.event_trigger("changed", (), {}, None, lambda: None)
        holder.remove_listener("changed", caller)
        holder.event_trigger("changed", (), {}, None, lambda: None)

        self.assertEqual(calls, ["EventChanged"])

    def test_listener_holder_create_get_iter_and_remove(self):
        holder = ListenerHolder()
        made = holder.create("made")
        same = holder.create("made")
        replacement = holder.create("made", replace=True)

        self.assertIs(same, made)
        self.assertIs(holder["made"], replacement)
        self.assertEqual(list(holder), [replacement])
        self.assertEqual(len(holder), 1)
        self.assertIs(holder.remove("made"), replacement)
        self.assertEqual(holder.remove(0, "missing"), "missing")

    def test_auto_create_add_listener_creates_missing_listener(self):
        holder = ListenerHolder(auto_create=True)
        calls = []

        holder.add_listener("created_late", lambda event: calls.append(event.name) or True)
        holder.event_trigger("created_late", (), {}, None, lambda: None)

        self.assertTrue(holder.has_listener("created_late"))
        self.assertEqual(calls, ["EventCreatedLate"])

    def test_system_listeners_emit_for_listenable_management_methods(self):
        holder = ListenerHolder("add_listener", "remove_listener", "managed")
        calls = []

        def managed(event):
            calls.append(("managed", event.args, event.returned))
            return True

        def add_listener_event(event):
            calls.append(("add_listener", event.args[0], event.args[1]))
            return True

        def remove_listener_event(event):
            calls.append(("remove_listener", event.args[0], event.args[1]))
            return True

        holder.add_listener("add_listener", add_listener_event)
        holder.add_listener("remove_listener", remove_listener_event)
        holder.add_listener("managed", managed)
        holder.event_trigger("managed", ("value",), {}, "returned", lambda value: value)
        holder.remove_listener("managed", managed)

        self.assertEqual(
            calls,
            [
                ("add_listener", "add_listener", add_listener_event),
                ("add_listener", "remove_listener", remove_listener_event),
                ("add_listener", "managed", managed),
                ("managed", ("value",), "returned"),
                ("remove_listener", "managed", managed),
            ],
        )


class ListensDecoratorTests(unittest.TestCase):
    def tearDown(self):
        for name in (
            "test_global_listener_event",
            "test_local_beats_global_event",
            "test_function_listener_event",
            "test_static_listener_event",
            "test_class_listener_event",
        ):
            GLOBAL_LISTENERS.remove(name, None)

    def test_listens_requires_at_least_one_listener(self):
        with self.assertRaisesRegex(TypeError, "at least one listener"):
            listens()

    def test_plain_function_uses_global_listeners(self):
        calls = []
        GLOBAL_LISTENERS.create("test_function_listener_event", replace=True)
        GLOBAL_LISTENERS.add_listener("test_function_listener_event", lambda event: calls.append(event) or True)

        @listens("test_function_listener_event")
        def combine(left, right):
            return left + right

        self.assertEqual(combine(2, 3), 5)
        self.assertEqual(calls[0].args, (2, 3))
        self.assertEqual(calls[0].returned, 5)

    def test_instance_method_falls_back_to_global_when_local_missing(self):
        calls = []
        GLOBAL_LISTENERS.create("test_global_listener_event", replace=True)
        GLOBAL_LISTENERS.add_listener("test_global_listener_event", lambda event: calls.append(event) or True)

        class Thing(Listenable):
            @listens("test_global_listener_event")
            def save(self, value):
                return value * 2

        self.assertEqual(Thing().save(4), 8)
        self.assertEqual(calls[0].args, (4,))
        self.assertEqual(calls[0].returned, 8)

    def test_local_listener_takes_precedence_over_global_listener(self):
        local_calls = []
        global_calls = []
        GLOBAL_LISTENERS.create("test_local_beats_global_event", replace=True)
        GLOBAL_LISTENERS.add_listener("test_local_beats_global_event", lambda event: global_calls.append(event) or True)

        class Thing(Listenable):
            def __init__(self):
                super().__init__("test_local_beats_global_event")

            @listens("test_local_beats_global_event")
            def save(self):
                return "saved"

        thing = Thing()
        thing.add_listener("test_local_beats_global_event", lambda event: local_calls.append(event) or True)

        self.assertEqual(thing.save(), "saved")
        self.assertEqual(len(local_calls), 1)
        self.assertEqual(global_calls, [])

    def test_property_accessors_can_listen(self):
        class Thing(Listenable):
            def __init__(self):
                super().__init__("get_value", "set_value", "del_value")
                self._value = "initial"

            @property
            @listens("get_value")
            def value(self):
                return self._value

            @value.setter
            @listens("set_value")
            def value(self, value):
                self._value = value

            @value.deleter
            @listens("del_value")
            def value(self):
                self._value = None

        thing = Thing()
        calls = []
        for name in ("get_value", "set_value", "del_value"):
            thing.add_listener(name, lambda event, name=name: calls.append((name, event.args, event.returned)) or True)

        self.assertEqual(thing.value, "initial")
        thing.value = "changed"
        del thing.value

        self.assertEqual(
            calls,
            [
                ("get_value", (), "initial"),
                ("set_value", ("changed",), None),
                ("del_value", (), None),
            ],
        )
        self.assertIsNone(thing._value)

    def test_static_and_class_methods_use_global_listeners(self):
        calls = []
        GLOBAL_LISTENERS.create("test_static_listener_event", replace=True)
        GLOBAL_LISTENERS.create("test_class_listener_event", replace=True)
        GLOBAL_LISTENERS.add_listener("test_static_listener_event", lambda event: calls.append(("static", event.args)) or True)
        GLOBAL_LISTENERS.add_listener("test_class_listener_event", lambda event: calls.append(("class", event.args)) or True)

        class Thing(Listenable):
            @staticmethod
            @listens("test_static_listener_event")
            def static(value):
                return value + 1

            @classmethod
            @listens("test_class_listener_event")
            def classy(cls, value):
                return cls.__name__, value

        self.assertEqual(Thing.static(1), 2)
        self.assertEqual(Thing.classy(2), ("Thing", 2))
        self.assertEqual(calls[0], ("static", (1,)))
        self.assertEqual(calls[1][0], "class")
        self.assertEqual(calls[1][1][0], Thing)
        self.assertEqual(calls[1][1][1], 2)

    def test_multiple_listens_decorators_merge_without_double_wrapping(self):
        class Thing(Listenable):
            def __init__(self):
                super().__init__("first", "second")

            @listens("first")
            @listens("second")
            def work(self):
                return "done"

        thing = Thing()
        calls = []
        thing.add_listener("first", lambda event: calls.append("first") or True)
        thing.add_listener("second", lambda event: calls.append("second") or True)

        self.assertEqual(thing.work(), "done")
        self.assertCountEqual(calls, ["first", "second"])

    def test_listens_rejects_recursion_by_default_when_disabled(self):
        class Thing(Listenable):
            def __init__(self):
                super().__init__("changed")

            @listens("changed", allow_recurse=False)
            def change(self, value):
                return value + 1

        thing = Thing()
        thing.add_listener("changed", lambda event: thing.change(event.returned) or True)

        with self.assertRaisesRegex(RecursionError, "Recursion not allowed on method 'change'"):
            thing.change(1)

    def test_listens_can_suppress_or_straight_call_when_recursion_denied(self):
        class Thing(Listenable):
            def __init__(self):
                super().__init__("none_event", "straight_event")
                self.calls = []

            @listens("none_event", allow_recurse=False, throw_on_recurse_denied=False)
            def none_on_recurse(self, value):
                self.calls.append(("none", value))
                return value + 1

            @listens(
                "straight_event",
                allow_recurse=False,
                throw_on_recurse_denied=False,
                straight_call_on_recurse_denied=True,
            )
            def straight_on_recurse(self, value):
                self.calls.append(("straight", value))
                return value + 1

        thing = Thing()
        seen = []
        thing.add_listener("none_event", lambda event: seen.append(thing.none_on_recurse(event.returned)) or True)
        thing.add_listener("straight_event", lambda event: seen.append(thing.straight_on_recurse(event.returned)) or True)

        self.assertEqual(thing.none_on_recurse(1), 2)
        self.assertEqual(thing.straight_on_recurse(1), 2)
        self.assertEqual(seen, [None, 3])
        self.assertEqual(thing.calls, [("none", 1), ("straight", 1), ("straight", 2)])

    def test_listens_allows_recursive_call_without_emitting_nested_event(self):
        class Thing(Listenable):
            def __init__(self):
                super().__init__("changed")
                self.event_count = 0

            @listens("changed")
            def change(self, value):
                return value + 1

        thing = Thing()

        def caller(event):
            thing.event_count += 1
            if event.returned == 2:
                self.assertEqual(thing.change(event.returned), 3)
            return True

        thing.add_listener("changed", caller)

        self.assertEqual(thing.change(1), 2)
        self.assertEqual(thing.event_count, 1)

    def test_system_listens_can_straight_call_when_recursion_denied(self):
        class Thing(Listenable):
            def __init__(self):
                super().__init__("system_event")

            @system_listens("system_event", straight_call_on_recurse_denied=True)
            def managed(self, value):
                return value + 1

        thing = Thing()
        calls = []
        thing.add_listener("system_event", lambda event: calls.append(thing.managed(event.returned)) or True)

        self.assertEqual(thing.managed(1), 2)
        self.assertEqual(calls, [3])


class InheritedListensTests(unittest.TestCase):
    def tearDown(self):
        for name in ("static_event", "class_event"):
            GLOBAL_LISTENERS.remove(name, None)

    def test_subclass_method_inherits_missing_listens_metadata(self):
        class Base(Listenable):
            @listens("changed")
            def change(self, value):
                return value

        class Child(Base):
            def __init__(self):
                super().__init__("changed")

            def change(self, value):
                return value.upper()

        child = Child()
        calls = []
        child.add_listener("changed", lambda event: calls.append((event.args, event.returned)) or True)

        self.assertEqual(child.change("value"), "VALUE")
        self.assertEqual(calls, [(("value",), "VALUE")])

    def test_subclass_property_inherits_missing_accessor_listens_metadata(self):
        class Base(Listenable):
            @property
            @listens("read")
            def value(self):
                return "base"

        class Child(Base):
            def __init__(self):
                super().__init__("read")

            @property
            def value(self):
                return "child"

        child = Child()
        calls = []
        child.add_listener("read", lambda event: calls.append(event.returned) or True)

        self.assertEqual(child.value, "child")
        self.assertEqual(calls, ["child"])

    def test_subclass_static_and_class_methods_inherit_missing_listens_metadata(self):
        GLOBAL_LISTENERS.create("static_event", replace=True)
        GLOBAL_LISTENERS.create("class_event", replace=True)

        class Base(Listenable):
            @staticmethod
            @listens("static_event")
            def static(value):
                return value

            @classmethod
            @listens("class_event")
            def classy(cls, value):
                return value

        class Child(Base):
            def __init__(self):
                super().__init__("static_event", "class_event")

            @staticmethod
            def static(value):
                return value + 1

            @classmethod
            def classy(cls, value):
                return value + 2

        calls = []
        GLOBAL_LISTENERS.add_listener("static_event", lambda event: calls.append(("static", event.args, event.returned)) or True)
        GLOBAL_LISTENERS.add_listener("class_event", lambda event: calls.append(("class", event.args, event.returned)) or True)

        self.assertEqual(Child.static(1), 2)
        self.assertEqual(Child.classy(1), 3)
        self.assertEqual(calls[0], ("static", (1,), 2))
        self.assertEqual(calls[1][0], "class")
        self.assertEqual(calls[1][1][0], Child)
        self.assertEqual(calls[1][1][1], 1)
        self.assertEqual(calls[1][2], 3)


class MutableListenerSequenceTests(unittest.TestCase):
    def test_mutable_listener_sequence_abstract_hooks_emit_events(self):
        class DemoSequence(MutableListenerSequence[int]):
            def __init__(self, values):
                self.values = list(values)
                super().__init__()

            def __len__(self):
                return len(self.values)

            def __getitem__(self, index):
                return self.values[index]

            def insert(self, index, value):
                self.values.insert(index, value)

            def __setitem__(self, key, value):
                self.values[key] = value

            def __delitem__(self, index):
                del self.values[index]

        sequence = DemoSequence([1, 2])
        calls = []
        for name in ("get", "add", "set", "remove"):
            sequence.add_listener(name, lambda event, name=name: calls.append((name, event.args, event.returned)) or True)

        self.assertEqual(sequence[0], 1)
        sequence.insert(1, 10)
        sequence[0] = 5
        del sequence[2]

        self.assertEqual(sequence.values, [5, 10])
        self.assertEqual(
            calls,
            [
                ("get", (0,), 1),
                ("add", (1, 10), None),
                ("set", (0, 5), None),
                ("remove", (2,), None),
            ],
        )


class PublicApiTests(unittest.TestCase):
    def test_public_event_classes_are_importable(self):
        self.assertTrue(issubclass(EventEnd, Exception))
        self.assertIsInstance(EventBuilder(), EventBuilder)
        self.assertIsInstance(Event(EventBuilder(), Listener("manual")), Event)

    def test_listens_for_merge_combines_names_and_explicit_options(self):
        base = ListensFor(("base",), allow_recurse=False, straight_call_on_recurse_denied=True)
        override = ListensFor(("override",), throw_on_recurse_denied=False)

        override.merge(base)

        self.assertEqual(override.names, ("override", "base"))
        self.assertFalse(override.allow_recurse)
        self.assertFalse(override.throw_on_recurse_denied)
        self.assertTrue(override.straight_call_on_recurse_denied)

    def test_default_listens_for_is_immutable(self):
        with self.assertRaisesRegex(RuntimeError, "Cannot modify a default ListensFor"):
            DEFAULT_LISTENS_FOR.names = ("changed",)


if __name__ == "__main__":
    unittest.main()
