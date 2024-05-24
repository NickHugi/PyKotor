from __future__ import annotations

from typing import Any, Generic, TypeVar

from qtpy.QtCore import QSettings, Qt

from utility.logger_util import RobustRootLogger


class QtTypeWrapper:
    def __init__(self, value: Any, type_str: str):
        self.value: Any = value
        self.type_str: str = type_str

    def reconstruct(self):
        return Qt.Key(self.value) if self.type_str == "Qt.Key" else self.value

T = TypeVar("T")
KT = TypeVar("KT")

class SettingsProperty(property, Generic[T]):
    def __init__(self, name: str, default: Any):
        self.name: str = name
        self.default: Any = default
        self.return_type: type[T] = type(self.default)
        self.serialized_default: KT = self.serialize_value(default)
        self.serialized_type: type[KT] = type(self.serialized_default)

        # Asserts are removed in release versions automatically with PYTHONOPTIMIZE (-O) flag.
        reconstructed_default = self.deserialize_value(self.serialized_default)
        assert default == reconstructed_default, f"{self.return_type} != {reconstructed_default.__class__}, repr type({default}) != type({reconstructed_default})"

        super().__init__(self.getter, self.setter, None, None)

    def getter(self, instance: Settings) -> T:
        try:
            serialized_value: KT = instance.settings.value(self.name, self.serialized_default, self.serialized_type)
            constructed_value: T = self.deserialize_value(serialized_value)
            if constructed_value.__class__ != self.default.__class__:
                RobustRootLogger.error(f"Corrupted setting '{self.name}': {constructed_value.__class__} != {self.default.__class__}, repr type({constructed_value}) != type({self.default})")
                return self._handle_corrupted_setting(instance)
        except Exception as e:
            RobustRootLogger.exception(f"Exception in settings getter while deserializing setting '{self.name}', got {serialized_value} ({serialized_value}) of type {serialized_value.__class__.__name__}. Original error: {e.__class__.__name__}: {e}")
            return self._handle_corrupted_setting(instance)
        else:
            return constructed_value

    def setter(self, instance: Settings, value: T):
        try:
            serialized_value: KT = self.serialize_value(value)
        except Exception as e:  # noqa: BLE001
            RobustRootLogger.exception(f"Exception in settings setter while serializing setting '{self.name}', got {serialized_value} ({serialized_value}) of type {serialized_value.__class__.__name__}. Original error: {e.__class__.__name__}: {e}")
        else:
            try:
                instance.settings.setValue(self.name, serialized_value)
            except Exception as e:  # noqa: BLE001
                RobustRootLogger.exception(f"Exception in settings setter while saving serialized setting '{self.name}', value {serialized_value}: {e}")

    def _handle_corrupted_setting(self, instance: Settings) -> T:
        RobustRootLogger.warning(f"Due to the above error, will reset setting '{self.name}'")
        self.reset_to_default(instance)
        return self.default

    def reset_to_default(self, instance: Settings):
        RobustRootLogger.info(f"Reset setting '{self.name}' to default of {self.default!s} (repr: {self.default!r})")
        instance.settings.setValue(self.name, self.serialized_default)

        # Double check it serialized correctly.
        serialized_value: KT = instance.settings.value(self.name, self.serialized_default, self.serialized_default.__class__)
        constructed_value: T = self.deserialize_value(serialized_value)
        if constructed_value.__class__ != self.default.__class__:
            raise RuntimeError(f"{constructed_value.__class__} != {self.default.__class__}, repr type({constructed_value}) != type({self.default})")

    def serialize_value(self, value: T) -> KT:  # noqa: PLR0911
        """Recursively serializes values, including Qt.Key and nested structures, for serialization.

        Encapsulates special Qt types in QtTypeWrapper.
        """
        if isinstance(value, Qt.Key):
            return QtTypeWrapper(int(value), "Qt.Key")
        if isinstance(value, Qt.MouseButton):
            return QtTypeWrapper(value, "Qt.MouseButton")
        if isinstance(value, set):
            return {self.serialize_value(item) for item in value}  # type: ignore[reportUnhashable]
        if isinstance(value, tuple):
            return tuple(self.serialize_value(item) for item in value)
        if isinstance(value, list):
            return [self.serialize_value(item) for item in value]
        if isinstance(value, dict):
            return {key: self.serialize_value(val) for key, val in value.items()}
        return value

    def deserialize_value(self, value: KT) -> T:
        """Recursively deserializes the value from the serialized form, handling QtTypeWrapper instances."""
        if isinstance(value, QtTypeWrapper):
            return value.reconstruct()
        if isinstance(value, set):
            return {self.deserialize_value(item) for item in value}  # type: ignore[reportUnhashable]
        if isinstance(value, tuple):
            return tuple(self.deserialize_value(item) for item in value)
        if isinstance(value, list):
            return [self.deserialize_value(item) for item in value]
        if isinstance(value, dict):
            return {key: self.deserialize_value(val) for key, val in value.items()}
        return value


class Settings:
    def __init__(self, scope: str):
        self.settings: QSettings = QSettings("HolocronToolsetV3", scope)

    @staticmethod
    def addSetting(name: str, default: T) -> SettingsProperty[T]:  # noqa: C901
        return SettingsProperty(name, default)

    def get_property(self, name: str) -> SettingsProperty[T]:
        prop = getattr(self.__class__, name, None)
        if not isinstance(prop, SettingsProperty):
            raise AttributeError(f"'{self.__class__.__name__}' object has no property '{name}'")  # noqa: TRY004
        return prop

    def get_default(self, name: str) -> Any:
        prop: SettingsProperty = self.get_property(name)
        return prop.default

    def reset_setting(self, name: str):
        prop: SettingsProperty = self.get_property(name)
        prop.reset_to_default(self)
