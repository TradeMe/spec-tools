"""
Type registry for specification modules.

This module provides a registry system for discovering and loading specification
type definitions from Python modules. It replaces the YAML-based loader with
a Python import-based approach.
"""

import importlib
import importlib.util
import sys
from pathlib import Path

from spec_check.dsl.models import GlobalConfig, SpecClass, SpecModule


class SpecTypeRegistry:
    """
    Central registry of specification types.

    The registry manages all module and class definitions, providing lookup
    methods for matching files to types and retrieving type information.
    """

    def __init__(self, config: GlobalConfig | None = None):
        """
        Initialize the registry.

        Args:
            config: Global configuration (uses default if not provided)
        """
        self.config = config or GlobalConfig.default()
        self._modules: dict[str, SpecModule] = {}
        self._classes: dict[str, SpecClass] = {}

    @property
    def modules(self) -> dict[str, SpecModule]:
        """Get all registered modules."""
        return self._modules

    @property
    def classes(self) -> dict[str, SpecClass]:
        """Get all registered classes."""
        return self._classes

    def register_module(self, module: SpecModule) -> None:
        """
        Register a module type.

        The module is validated by Pydantic at registration time, ensuring
        the type definition is well-formed before it's used for validation.

        Args:
            module: Module definition to register

        Raises:
            ValueError: If module name is already registered
        """
        if module.name in self._modules:
            raise ValueError(f"Module '{module.name}' is already registered")

        self._modules[module.name] = module

        # Also register any classes defined in this module
        for class_name, class_def in module.classes.items():
            self.register_class(class_name, class_def)

    def register_class(self, name: str, class_def: SpecClass) -> None:
        """
        Register a reusable class definition.

        Args:
            name: Class name
            class_def: Class definition

        Raises:
            ValueError: If class name is already registered
        """
        if name in self._classes:
            raise ValueError(f"Class '{name}' is already registered")

        self._classes[name] = class_def

    def get_module(self, name: str) -> SpecModule | None:
        """
        Get a module by name.

        Args:
            name: Module name

        Returns:
            Module definition or None if not found
        """
        return self._modules.get(name)

    def get_class(self, name: str) -> SpecClass | None:
        """
        Get a class by name.

        Args:
            name: Class name

        Returns:
            Class definition or None if not found
        """
        return self._classes.get(name)

    def get_module_for_file(self, file_path: Path) -> SpecModule | None:
        """
        Find the module type that applies to a file.

        Checks file_pattern and location_pattern for each registered module.

        Args:
            file_path: Path to the file

        Returns:
            Matching module or None if no match found
        """
        for module in self._modules.values():
            if module.matches_file(file_path):
                return module
        return None

    @classmethod
    def load_from_package(cls, package_path: Path) -> "SpecTypeRegistry":
        """
        Load all type definitions from a Python package.

        The package should contain Python modules that define SpecModule
        instances. The registry discovers these by importing all Python
        files in the package and inspecting their global namespace.

        Args:
            package_path: Path to the package directory

        Returns:
            Registry with all discovered types

        Raises:
            FileNotFoundError: If package path doesn't exist
            ImportError: If package cannot be imported
        """
        if not package_path.exists():
            raise FileNotFoundError(f"Package path not found: {package_path}")

        registry = cls()

        # Check if this is a Python package (has __init__.py)
        init_file = package_path / "__init__.py"
        if not init_file.exists():
            raise ImportError(f"Not a Python package (missing __init__.py): {package_path}")

        # Import the package
        package_name = package_path.name
        spec = importlib.util.spec_from_file_location(package_name, init_file)
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot load package: {package_path}")

        module = importlib.util.module_from_spec(spec)
        sys.modules[package_name] = module
        spec.loader.exec_module(module)

        # Discover SpecModule instances in the package
        registry._discover_types_in_module(module)

        # Also discover types in submodules
        for py_file in package_path.glob("*.py"):
            if py_file.name.startswith("_"):
                continue  # Skip __init__.py and private modules

            submodule_name = f"{package_name}.{py_file.stem}"
            spec = importlib.util.spec_from_file_location(submodule_name, py_file)
            if spec is None or spec.loader is None:
                continue

            submodule = importlib.util.module_from_spec(spec)
            sys.modules[submodule_name] = submodule
            spec.loader.exec_module(submodule)

            registry._discover_types_in_module(submodule)

        return registry

    def _discover_types_in_module(self, module) -> None:
        """
        Discover SpecModule instances in a Python module.

        Args:
            module: Python module to inspect
        """
        for name in dir(module):
            if name.startswith("_"):
                continue

            obj = getattr(module, name)

            # Check if it's a SpecModule instance
            if isinstance(obj, SpecModule):
                try:
                    self.register_module(obj)
                except ValueError:
                    # Already registered, skip
                    pass

    @classmethod
    def load_builtin_types(cls) -> "SpecTypeRegistry":
        """
        Load built-in type definitions.

        Returns:
            Registry with built-in types (Requirement, Contract, ADR)
        """
        from spec_check.dsl.builtin_types import BUILTIN_MODULES

        registry = cls()
        for module in BUILTIN_MODULES.values():
            registry.register_module(module)

        return registry

    @classmethod
    def load_from_path_or_builtin(cls, type_path: Path | None = None) -> "SpecTypeRegistry":
        """
        Load type definitions from a path or use built-in types.

        Args:
            type_path: Path to Python package with type definitions,
                       or None to use built-in types

        Returns:
            Registry with loaded types
        """
        if type_path is None:
            return cls.load_builtin_types()

        if not type_path.exists():
            raise FileNotFoundError(f"Type definition path not found: {type_path}")

        return cls.load_from_package(type_path)
