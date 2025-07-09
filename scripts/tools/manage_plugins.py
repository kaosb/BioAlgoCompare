#!/usr/bin/env python3
"""
CLI tool for managing algorithm plugins.
"""

import click
import json
from pathlib import Path
from typing import Optional
import sys

from plugins import PluginManager
from plugins.plugin_loader import create_plugin_template, validate_plugin, PluginLoader
from plugins.plugin_registry import PluginRegistry


@click.group()
@click.option('--plugin-dir', default='external_plugins', 
              help='Plugin directory path')
@click.pass_context
def cli(ctx, plugin_dir):
    """BioAlgoCompare Plugin Manager."""
    ctx.ensure_object(dict)
    ctx.obj['manager'] = PluginManager(plugin_dir=plugin_dir)


@cli.command()
@click.pass_context
def list(ctx):
    """List all available plugins."""
    manager = ctx.obj['manager']
    plugins = manager.list_plugins(include_failed=True)
    
    if not plugins:
        click.echo("No plugins found.")
        return
    
    # Group by status
    active = [p for p in plugins if p.get('status') == 'active']
    failed = [p for p in plugins if p.get('status') == 'failed']
    
    if active:
        click.echo("\n=== Active Plugins ===")
        for plugin in active:
            metadata = plugin['metadata']
            click.echo(f"\n{metadata['name']} v{metadata['version']}")
            click.echo(f"  Author: {metadata['author']}")
            click.echo(f"  Description: {metadata['description']}")
            click.echo(f"  Algorithm: {metadata['algorithm_class']}")
            if metadata.get('problem_types'):
                click.echo(f"  Problem Types: {', '.join(metadata['problem_types'])}")
    
    if failed:
        click.echo("\n=== Failed Plugins ===")
        for plugin in failed:
            click.echo(f"\n{plugin['metadata']['name']}")
            click.echo(f"  Error: {plugin['error']}")


@cli.command()
@click.argument('source', type=click.Path(exists=True))
@click.option('--name', help='Plugin name (auto-detected if not provided)')
@click.pass_context
def install(ctx, source, name):
    """Install a plugin from file or directory."""
    manager = ctx.obj['manager']
    source_path = Path(source)
    
    click.echo(f"Installing plugin from: {source_path}")
    
    success = manager.install_plugin(source_path, name)
    
    if success:
        click.echo(click.style("✓ Plugin installed successfully", fg='green'))
        
        # Show installed plugin info
        if name:
            plugin_info = manager.get_plugin(name)
            if plugin_info:
                info = plugin_info.get_info()
                click.echo(f"\nInstalled: {info['metadata']['name']} v{info['metadata']['version']}")
    else:
        click.echo(click.style("✗ Plugin installation failed", fg='red'))
        sys.exit(1)


@cli.command()
@click.argument('name')
@click.pass_context
def uninstall(ctx, name):
    """Uninstall a plugin."""
    manager = ctx.obj['manager']
    
    click.echo(f"Uninstalling plugin: {name}")
    
    success = manager.uninstall_plugin(name)
    
    if success:
        click.echo(click.style("✓ Plugin uninstalled successfully", fg='green'))
    else:
        click.echo(click.style("✗ Plugin not found or uninstall failed", fg='red'))
        sys.exit(1)


@cli.command()
@click.argument('name')
@click.pass_context
def info(ctx, name):
    """Show detailed information about a plugin."""
    manager = ctx.obj['manager']
    
    plugin_interface = manager.get_plugin(name)
    if not plugin_interface:
        click.echo(f"Plugin not found: {name}")
        sys.exit(1)
    
    info = plugin_interface.get_info()
    metadata = info['metadata']
    
    click.echo(f"\n=== {metadata['name']} ===")
    click.echo(f"Version: {metadata['version']}")
    click.echo(f"Author: {metadata['author']}")
    click.echo(f"Description: {metadata['description']}")
    click.echo(f"Algorithm Class: {metadata['algorithm_class']}")
    click.echo(f"Created: {metadata.get('created_at', 'Unknown')}")
    
    if metadata.get('problem_types'):
        click.echo(f"\nProblem Types: {', '.join(metadata['problem_types'])}")
    
    if metadata.get('dependencies'):
        click.echo(f"\nDependencies: {', '.join(metadata['dependencies'])}")
    
    click.echo(f"\nEnvironment Valid: {info.get('environment_valid', False)}")
    
    if info.get('custom_operators'):
        click.echo(f"\nCustom Operators: {', '.join(info['custom_operators'])}")
    
    # Show parameter schema
    schema = info.get('parameter_schema', {})
    if schema.get('properties'):
        click.echo("\nParameters:")
        for param, details in schema['properties'].items():
            param_type = details.get('type', 'any')
            default = details.get('default', 'none')
            required = param in schema.get('required', [])
            req_str = " (required)" if required else ""
            click.echo(f"  - {param}: {param_type} = {default}{req_str}")


@cli.command()
@click.argument('name')
@click.option('--source', help='Plugin source file/directory')
@click.pass_context
def reload(ctx, name, source):
    """Reload a plugin."""
    manager = ctx.obj['manager']
    
    click.echo(f"Reloading plugin: {name}")
    
    if source:
        # Unload and load from specific source
        manager.unload_plugin(name)
        success = manager.load_plugin(name, source)
    else:
        # Use built-in reload
        success = manager.reload_plugin(name)
    
    if success:
        click.echo(click.style("✓ Plugin reloaded successfully", fg='green'))
    else:
        click.echo(click.style("✗ Plugin reload failed", fg='red'))
        sys.exit(1)


@cli.command()
@click.argument('source', type=click.Path(exists=True))
@click.pass_context
def validate(ctx, source):
    """Validate a plugin before installation."""
    source_path = Path(source)
    
    click.echo(f"Validating plugin: {source_path}")
    
    # Load plugin
    if source_path.is_file():
        plugin = PluginLoader.load_from_file(source_path)
    elif source_path.is_dir():
        plugin = PluginLoader.load_from_package(source_path)
    else:
        click.echo("Invalid source type")
        sys.exit(1)
    
    if not plugin:
        click.echo(click.style("✗ Failed to load plugin", fg='red'))
        sys.exit(1)
    
    # Validate
    is_valid, issues = validate_plugin(plugin)
    
    if is_valid:
        click.echo(click.style("✓ Plugin is valid", fg='green'))
        
        # Show plugin info
        metadata = plugin.get_metadata()
        click.echo(f"\nPlugin: {metadata.name} v{metadata.version}")
        click.echo(f"Algorithm: {metadata.algorithm_class}")
    else:
        click.echo(click.style("✗ Plugin validation failed", fg='red'))
        click.echo("\nIssues found:")
        for issue in issues:
            click.echo(f"  - {issue}")
        sys.exit(1)


@cli.command()
@click.option('--output-dir', '-o', default='new_plugin', 
              help='Output directory for plugin')
@click.option('--plugin-name', '-p', required=True, 
              help='Plugin name')
@click.option('--algorithm-name', '-a', required=True,
              help='Algorithm class name')
def create(output_dir, plugin_name, algorithm_name):
    """Create a new plugin template."""
    output_path = Path(output_dir)
    
    click.echo(f"Creating plugin template: {plugin_name}")
    click.echo(f"Output directory: {output_path}")
    
    try:
        create_plugin_template(output_path, plugin_name, algorithm_name)
        
        click.echo(click.style("✓ Plugin template created successfully", fg='green'))
        click.echo("\nFiles created:")
        for file in output_path.iterdir():
            click.echo(f"  - {file.name}")
        
        click.echo(f"\nNext steps:")
        click.echo(f"1. Edit {output_path / f'{plugin_name.lower()}_plugin.py'}")
        click.echo(f"2. Implement your algorithm logic")
        click.echo(f"3. Test with: bioalgo-plugins validate {output_path}")
        click.echo(f"4. Install with: bioalgo-plugins install {output_path}")
        
    except Exception as e:
        click.echo(click.style(f"✗ Failed to create template: {e}", fg='red'))
        sys.exit(1)


@cli.command()
@click.argument('output', type=click.Path())
@click.pass_context
def export(ctx, output):
    """Export plugin information to file."""
    manager = ctx.obj['manager']
    output_path = Path(output)
    
    click.echo(f"Exporting plugin information to: {output_path}")
    
    try:
        manager.export_plugin_info(output_path)
        click.echo(click.style("✓ Export completed successfully", fg='green'))
        
        # Show summary
        with open(output_path) as f:
            data = json.load(f)
        
        stats = data.get('statistics', {})
        click.echo(f"\nExported:")
        click.echo(f"  - Total plugins: {stats.get('total_plugins', 0)}")
        click.echo(f"  - Failed plugins: {stats.get('failed_plugins', 0)}")
        click.echo(f"  - Available algorithms: {stats.get('algorithms_available', 0)}")
        
    except Exception as e:
        click.echo(click.style(f"✗ Export failed: {e}", fg='red'))
        sys.exit(1)


@cli.command()
@click.pass_context
def registry(ctx):
    """Show plugin registry information."""
    click.echo("\n=== Plugin Registry ===")
    
    # List registered plugins
    plugins = PluginRegistry.list_plugins()
    if plugins:
        click.echo("\nRegistered Plugins:")
        for name in plugins:
            plugin_info = PluginRegistry.get_plugin_info(name)
            if plugin_info:
                metadata = plugin_info['metadata']
                click.echo(f"  - {name}: {metadata['description']}")
    else:
        click.echo("\nNo plugins in registry")
    
    # List algorithms
    algorithms = PluginRegistry.list_algorithms()
    if algorithms:
        click.echo("\nRegistered Algorithms:")
        for name in algorithms:
            algo_class = PluginRegistry.get_algorithm(name)
            if algo_class:
                module = algo_class.__module__
                click.echo(f"  - {name} ({module})")
    else:
        click.echo("\nNo algorithms in registry")


@cli.command()
@click.pass_context
def clear_cache(ctx):
    """Clear plugin cache."""
    manager = ctx.obj['manager']
    
    cache_dir = manager.cache_dir
    if cache_dir.exists():
        import shutil
        shutil.rmtree(cache_dir)
        cache_dir.mkdir()
        click.echo(click.style("✓ Cache cleared successfully", fg='green'))
    else:
        click.echo("No cache to clear")


def main():
    """Main entry point."""
    cli(obj={})


if __name__ == '__main__':
    main()