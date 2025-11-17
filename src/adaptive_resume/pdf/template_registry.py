"""Template registry for managing available resume templates.

This module provides a centralized registry for all resume templates,
allowing templates to be registered, retrieved, and listed.
"""

from __future__ import annotations

from typing import Dict, List, Type, Optional
import logging

from .base_template import BaseResumeTemplate, TemplateSpec

logger = logging.getLogger(__name__)


class TemplateRegistryError(Exception):
    """Exception raised for template registry errors."""
    pass


class TemplateRegistry:
    """Registry for available resume templates.

    This class maintains a registry of all available resume templates
    and provides methods to register, retrieve, and list templates.

    All template classes are registered using the @TemplateRegistry.register
    decorator or the register() class method.

    Example:
        @TemplateRegistry.register("classic")
        class ClassicTemplate(BaseResumeTemplate):
            ...

        Or manually:
        TemplateRegistry.register("classic", ClassicTemplate)

        # Retrieve template
        template_class = TemplateRegistry.get_template("classic")
        template = template_class(spec)
    """

    _templates: Dict[str, Type[BaseResumeTemplate]] = {}
    _specs: Dict[str, TemplateSpec] = {}

    @classmethod
    def register(
        cls,
        name: str,
        template_class: Optional[Type[BaseResumeTemplate]] = None,
        spec: Optional[TemplateSpec] = None
    ):
        """Register a template class.

        Can be used as a decorator or called directly.

        Args:
            name: Template name (e.g., "classic", "modern")
            template_class: Template class to register (optional if used as decorator)
            spec: Default TemplateSpec for this template (optional)

        Returns:
            Template class (for decorator usage) or None

        Raises:
            TemplateRegistryError: If template name already registered
            ValueError: If template_class is not a BaseResumeTemplate subclass

        Example:
            # As decorator
            @TemplateRegistry.register("classic")
            class ClassicTemplate(BaseResumeTemplate):
                pass

            # Direct call
            TemplateRegistry.register("classic", ClassicTemplate)
        """
        def decorator(template_cls: Type[BaseResumeTemplate]):
            # Validate template class
            if not issubclass(template_cls, BaseResumeTemplate):
                raise ValueError(
                    f"Template class must inherit from BaseResumeTemplate, "
                    f"got {template_cls.__name__}"
                )

            # Check if already registered
            if name in cls._templates:
                logger.warning(f"Template '{name}' is already registered, overwriting")

            # Register template
            cls._templates[name] = template_cls
            if spec:
                cls._specs[name] = spec

            logger.info(f"Registered template: {name} ({template_cls.__name__})")
            return template_cls

        # If used as decorator (@register("name"))
        if template_class is None:
            return decorator

        # If used directly (register("name", ClassicTemplate))
        return decorator(template_class)

    @classmethod
    def get_template(cls, name: str) -> Type[BaseResumeTemplate]:
        """Get template class by name.

        Args:
            name: Template name

        Returns:
            Template class

        Raises:
            TemplateRegistryError: If template not found
        """
        if name not in cls._templates:
            available = ", ".join(cls.list_templates())
            raise TemplateRegistryError(
                f"Template '{name}' not found. "
                f"Available templates: {available}"
            )

        return cls._templates[name]

    @classmethod
    def get_spec(cls, name: str) -> Optional[TemplateSpec]:
        """Get default TemplateSpec for a template.

        Args:
            name: Template name

        Returns:
            TemplateSpec if registered, None otherwise
        """
        return cls._specs.get(name)

    @classmethod
    def list_templates(cls) -> List[str]:
        """List all registered template names.

        Returns:
            List of template names
        """
        return sorted(cls._templates.keys())

    @classmethod
    def is_registered(cls, name: str) -> bool:
        """Check if a template is registered.

        Args:
            name: Template name

        Returns:
            True if template is registered, False otherwise
        """
        return name in cls._templates

    @classmethod
    def clear(cls) -> None:
        """Clear all registered templates.

        This is primarily used for testing to reset the registry state.
        """
        cls._templates.clear()
        cls._specs.clear()
        logger.info("Cleared template registry")

    @classmethod
    def unregister(cls, name: str) -> None:
        """Unregister a template.

        Args:
            name: Template name

        Raises:
            TemplateRegistryError: If template not found
        """
        if name not in cls._templates:
            raise TemplateRegistryError(f"Template '{name}' not found")

        del cls._templates[name]
        if name in cls._specs:
            del cls._specs[name]

        logger.info(f"Unregistered template: {name}")

    @classmethod
    def clear(cls) -> None:
        """Clear all registered templates.

        Warning: This is primarily for testing. Use with caution.
        """
        cls._templates.clear()
        cls._specs.clear()
        logger.warning("Cleared all registered templates")

    @classmethod
    def get_template_info(cls) -> Dict[str, Dict[str, any]]:
        """Get information about all registered templates.

        Returns:
            Dictionary mapping template names to info dictionaries
        """
        info = {}
        for name, template_class in cls._templates.items():
            info[name] = {
                'class_name': template_class.__name__,
                'module': template_class.__module__,
                'has_default_spec': name in cls._specs
            }
        return info


__all__ = ['TemplateRegistry', 'TemplateRegistryError']
