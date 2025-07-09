"""
Plugin manager for loading and managing algorithm plugins.
"""

import logging
import json
from typing import Dict, List, Optional, Type, Any, Union
from pathlib import Path
import importlib
import sys
import hashlib

from .plugin_base import Plugin, PluginInterface, PluginMetadata
from algorithms.base_v2 import MetaheuristicAlgorithm
from problems.base import AbstractProblem as Problem


logger = logging.getLogger(__name__)


class PluginManager:
    """
    Central manager for algorithm plugins.
    """
    
    def __init__(self, plugin_dir: Union[str, Path] = "external_plugins"):
        """
        Initialize plugin manager.
        
        Args:
            plugin_dir: Directory containing plugins
        """
        self.plugin_dir = Path(plugin_dir)
        self.plugin_dir.mkdir(exist_ok=True)
        
        # Plugin storage
        self.plugins: Dict[str, PluginInterface] = {}
        self.failed_plugins: Dict[str, str] = {}
        
        # Create subdirectories
        self.installed_dir = self.plugin_dir / "installed"
        self.config_dir = self.plugin_dir / "config"
        self.cache_dir = self.plugin_dir / "cache"
        
        for dir_path in [self.installed_dir, self.config_dir, self.cache_dir]:
            dir_path.mkdir(exist_ok=True)
        
        # Load configuration
        self.config_file = self.config_dir / "plugins.json"
        self.config = self._load_config()
        
        # Initialize with auto-discovery if enabled
        if self.config.get('auto_discover', True):
            self.discover_plugins()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load plugin configuration."""
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                return json.load(f)
        
        # Default configuration
        default_config = {
            'auto_discover': True,
            'validate_on_load': True,
            'cache_enabled': True,
            'plugin_paths': [
                str(self.installed_dir),
                'plugins/builtin'
            ]
        }
        
        self._save_config(default_config)
        return default_config
    
    def _save_config(self, config: Dict[str, Any]) -> None:
        """Save plugin configuration."""
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)
    
    def discover_plugins(self) -> List[str]:
        """
        Discover and load all available plugins.
        
        Returns:
            List of loaded plugin names
        """
        loaded = []
        
        # Search in configured paths
        for path_str in self.config.get('plugin_paths', []):
            path = Path(path_str)
            if not path.exists():
                continue
            
            # Look for plugin files
            for plugin_file in path.glob('*.py'):
                if plugin_file.name.startswith('_'):
                    continue
                
                try:
                    plugin_name = self._load_plugin_from_file(plugin_file)
                    if plugin_name:
                        loaded.append(plugin_name)
                        logger.info(f"Loaded plugin: {plugin_name}")
                except Exception as e:
                    logger.error(f"Failed to load plugin from {plugin_file}: {e}")
            
            # Look for plugin packages
            for plugin_dir in path.iterdir():
                if plugin_dir.is_dir() and not plugin_dir.name.startswith('_'):
                    manifest_file = plugin_dir / 'plugin.json'
                    if manifest_file.exists():
                        try:
                            plugin_name = self._load_plugin_from_package(plugin_dir)
                            if plugin_name:
                                loaded.append(plugin_name)
                                logger.info(f"Loaded plugin package: {plugin_name}")
                        except Exception as e:
                            logger.error(f"Failed to load plugin from {plugin_dir}: {e}")
        
        return loaded
    
    def _load_plugin_from_file(self, file_path: Path) -> Optional[str]:
        """Load plugin from Python file."""
        # Calculate checksum
        checksum = self._calculate_checksum(file_path)
        
        # Check cache
        if self.config.get('cache_enabled', True):
            cached = self._check_cache(file_path.stem, checksum)
            if cached:
                return self._load_cached_plugin(cached)
        
        # Import module
        spec = importlib.util.spec_from_file_location(file_path.stem, file_path)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            sys.modules[file_path.stem] = module
            spec.loader.exec_module(module)
            
            # Look for plugin class
            plugin = self._find_plugin_in_module(module)
            if plugin:
                return self._register_plugin(plugin, checksum)
        
        return None
    
    def _load_plugin_from_package(self, package_dir: Path) -> Optional[str]:
        """Load plugin from package directory."""
        manifest_file = package_dir / 'plugin.json'
        
        with open(manifest_file, 'r') as f:
            manifest = json.load(f)
        
        # Import package
        package_name = package_dir.name
        sys.path.insert(0, str(package_dir.parent))
        
        try:
            module = importlib.import_module(package_name)
            
            # Get plugin class from manifest
            plugin_class_name = manifest.get('plugin_class', 'Plugin')
            plugin_class = getattr(module, plugin_class_name, None)
            
            if plugin_class and issubclass(plugin_class, Plugin):
                plugin = plugin_class()
                
                # Update metadata from manifest
                if hasattr(plugin, '_metadata'):
                    for key, value in manifest.items():
                        if hasattr(plugin._metadata, key):
                            setattr(plugin._metadata, key, value)
                
                return self._register_plugin(plugin)
                
        finally:
            sys.path.pop(0)
        
        return None
    
    def _find_plugin_in_module(self, module) -> Optional[Plugin]:
        """Find Plugin instance in module."""
        # Look for direct plugin instance
        for name in dir(module):
            obj = getattr(module, name)
            if isinstance(obj, Plugin):
                return obj
        
        # Look for plugin class
        for name in dir(module):
            obj = getattr(module, name)
            if (isinstance(obj, type) and 
                issubclass(obj, Plugin) and 
                obj != Plugin):
                try:
                    return obj()
                except:
                    pass
        
        return None
    
    def _register_plugin(self, plugin: Plugin, 
                        checksum: Optional[str] = None) -> Optional[str]:
        """Register a plugin."""
        try:
            # Validate environment
            if self.config.get('validate_on_load', True):
                if not plugin.validate_environment():
                    raise RuntimeError("Plugin environment validation failed")
            
            # Get metadata
            metadata = plugin.get_metadata()
            plugin_name = metadata.name
            
            # Update checksum
            if checksum:
                metadata.checksum = checksum
            
            # Create interface
            interface = PluginInterface(plugin)
            
            # Setup plugin
            plugin.setup()
            
            # Register
            self.plugins[plugin_name] = interface
            
            # Cache if enabled
            if self.config.get('cache_enabled', True) and checksum:
                self._cache_plugin(plugin_name, metadata, checksum)
            
            return plugin_name
            
        except Exception as e:
            logger.error(f"Failed to register plugin: {e}")
            if hasattr(plugin, 'get_metadata'):
                self.failed_plugins[plugin.get_metadata().name] = str(e)
            return None
    
    def load_plugin(self, name: str, 
                   source: Optional[Union[str, Path]] = None) -> bool:
        """
        Load a specific plugin.
        
        Args:
            name: Plugin name
            source: Optional source file or directory
            
        Returns:
            True if loaded successfully
        """
        if name in self.plugins:
            logger.info(f"Plugin {name} already loaded")
            return True
        
        if source:
            source_path = Path(source)
            if source_path.is_file():
                loaded_name = self._load_plugin_from_file(source_path)
            elif source_path.is_dir():
                loaded_name = self._load_plugin_from_package(source_path)
            else:
                logger.error(f"Invalid source: {source}")
                return False
            
            return loaded_name == name
        
        # Try to find in configured paths
        self.discover_plugins()
        return name in self.plugins
    
    def unload_plugin(self, name: str) -> bool:
        """
        Unload a plugin.
        
        Args:
            name: Plugin name
            
        Returns:
            True if unloaded successfully
        """
        if name not in self.plugins:
            return False
        
        interface = self.plugins[name]
        
        # Teardown
        try:
            interface.plugin.teardown()
        except Exception as e:
            logger.error(f"Error during plugin teardown: {e}")
        
        # Remove
        del self.plugins[name]
        
        # Remove from failed if present
        self.failed_plugins.pop(name, None)
        
        return True
    
    def get_plugin(self, name: str) -> Optional[PluginInterface]:
        """Get plugin interface by name."""
        return self.plugins.get(name)
    
    def list_plugins(self, include_failed: bool = False) -> List[Dict[str, Any]]:
        """
        List all plugins.
        
        Args:
            include_failed: Include failed plugins
            
        Returns:
            List of plugin information
        """
        plugins = []
        
        # Active plugins
        for name, interface in self.plugins.items():
            info = interface.get_info()
            info['status'] = 'active'
            plugins.append(info)
        
        # Failed plugins
        if include_failed:
            for name, error in self.failed_plugins.items():
                plugins.append({
                    'metadata': {'name': name},
                    'status': 'failed',
                    'error': error
                })
        
        return plugins
    
    def get_algorithms(self) -> Dict[str, Type[MetaheuristicAlgorithm]]:
        """
        Get all available algorithms from plugins.
        
        Returns:
            Dictionary mapping algorithm name to class
        """
        algorithms = {}
        
        for name, interface in self.plugins.items():
            try:
                algo_class = interface.get_algorithm_class()
                algo_name = interface.metadata.algorithm_class
                algorithms[algo_name] = algo_class
            except Exception as e:
                logger.error(f"Failed to get algorithm from plugin {name}: {e}")
        
        return algorithms
    
    def create_algorithm(self, plugin_name: str, 
                        problem: Problem, **kwargs) -> MetaheuristicAlgorithm:
        """
        Create algorithm instance from plugin.
        
        Args:
            plugin_name: Plugin name
            problem: Problem instance
            **kwargs: Algorithm parameters
            
        Returns:
            Algorithm instance
        """
        interface = self.get_plugin(plugin_name)
        if not interface:
            raise ValueError(f"Plugin not found: {plugin_name}")
        
        return interface.create_algorithm(problem, **kwargs)
    
    def get_compatible_plugins(self, problem: Problem) -> List[str]:
        """
        Get plugins compatible with a problem.
        
        Args:
            problem: Problem instance
            
        Returns:
            List of compatible plugin names
        """
        compatible = []
        
        for name, interface in self.plugins.items():
            if interface.plugin.is_compatible_with_problem(problem):
                compatible.append(name)
        
        return compatible
    
    def install_plugin(self, source: Union[str, Path], 
                      name: Optional[str] = None) -> bool:
        """
        Install a plugin to the managed directory.
        
        Args:
            source: Source file or directory
            name: Optional plugin name
            
        Returns:
            True if installed successfully
        """
        source_path = Path(source)
        
        if not source_path.exists():
            logger.error(f"Source not found: {source}")
            return False
        
        # Determine destination
        if source_path.is_file():
            dest = self.installed_dir / source_path.name
            import shutil
            shutil.copy2(source_path, dest)
        else:
            # Copy directory
            dest = self.installed_dir / (name or source_path.name)
            import shutil
            shutil.copytree(source_path, dest, dirs_exist_ok=True)
        
        # Load the installed plugin
        if name:
            return self.load_plugin(name, dest)
        else:
            self.discover_plugins()
            return True
    
    def uninstall_plugin(self, name: str) -> bool:
        """
        Uninstall a plugin.
        
        Args:
            name: Plugin name
            
        Returns:
            True if uninstalled successfully
        """
        # Unload first
        self.unload_plugin(name)
        
        # Find and remove files
        for path in self.installed_dir.iterdir():
            if path.stem == name or path.name == name:
                if path.is_file():
                    path.unlink()
                else:
                    import shutil
                    shutil.rmtree(path)
                return True
        
        return False
    
    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate file checksum."""
        hasher = hashlib.md5()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                hasher.update(chunk)
        return hasher.hexdigest()
    
    def _check_cache(self, name: str, checksum: str) -> Optional[Dict[str, Any]]:
        """Check plugin cache."""
        cache_file = self.cache_dir / f"{name}_{checksum}.json"
        if cache_file.exists():
            with open(cache_file, 'r') as f:
                return json.load(f)
        return None
    
    def _cache_plugin(self, name: str, metadata: PluginMetadata, 
                     checksum: str) -> None:
        """Cache plugin information."""
        cache_file = self.cache_dir / f"{name}_{checksum}.json"
        cache_data = {
            'metadata': metadata.to_dict(),
            'checksum': checksum
        }
        with open(cache_file, 'w') as f:
            json.dump(cache_data, f, indent=2)
    
    def _load_cached_plugin(self, cache_data: Dict[str, Any]) -> Optional[str]:
        """Load plugin from cache."""
        # This would need to reconstruct the plugin
        # For now, return None to force reload
        return None
    
    def reload_plugin(self, name: str) -> bool:
        """
        Reload a plugin.
        
        Args:
            name: Plugin name
            
        Returns:
            True if reloaded successfully
        """
        # Get current plugin info
        interface = self.get_plugin(name)
        if not interface:
            return False
        
        # Find source
        source = None
        for path in self.config.get('plugin_paths', []):
            path_obj = Path(path)
            for file_path in path_obj.glob('**/*.py'):
                if file_path.stem == name:
                    source = file_path
                    break
            if source:
                break
        
        if not source:
            logger.error(f"Could not find source for plugin {name}")
            return False
        
        # Unload and reload
        self.unload_plugin(name)
        return self.load_plugin(name, source)
    
    def export_plugin_info(self, output_file: Union[str, Path]) -> None:
        """Export plugin information to file."""
        output_path = Path(output_file)
        
        info = {
            'plugins': self.list_plugins(include_failed=True),
            'config': self.config,
            'statistics': {
                'total_plugins': len(self.plugins),
                'failed_plugins': len(self.failed_plugins),
                'algorithms_available': len(self.get_algorithms())
            }
        }
        
        with open(output_path, 'w') as f:
            json.dump(info, f, indent=2)
        
        logger.info(f"Plugin information exported to {output_path}")