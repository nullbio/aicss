"""
Command Line Interface for AI CSS Framework.
"""

import sys
import os
import time
import click
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Completely disable tqdm and progress bars before any imports
os.environ["TQDM_DISABLE"] = "1"
os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["TRANSFORMERS_NO_ADVISORY_WARNINGS"] = "1"
os.environ["TRANSFORMERS_VERBOSITY"] = "error"

# Aggressively patch tqdm to completely disable it
try:
    # First try to redirect stdout for any tqdm output
    import sys
    real_stdout = sys.stdout
    
    class DummyTqdmFile:
        """File-like object that discards tqdm outputs."""
        def __init__(self, file):
            self.file = file
            
        def write(self, x):
            # Filter out tqdm outputs
            if not x.startswith('\r') and not '|' in x:
                self.file.write(x)
                
        def flush(self):
            self.file.flush()
    
    sys.stdout = DummyTqdmFile(sys.stdout)
    
    # Now completely replace tqdm with a no-op version
    import importlib.util
    if importlib.util.find_spec("tqdm") is not None:
        import tqdm as tqdm_module
        
        # Define a completely disabled version of tqdm
        def _null_tqdm(*args, **kwargs):
            if len(args) > 0:
                return args[0]  # Return the iterable unchanged
            return None
        
        # Replace every possible tqdm function and class
        for module_name in ['tqdm', 'tqdm.auto', 'tqdm.notebook', 'tqdm.std', 'tqdm.gui']:
            try:
                module = importlib.import_module(module_name)
                module.tqdm = _null_tqdm
                if hasattr(module, 'trange'):
                    module.trange = lambda *args, **kwargs: range(*args)
            except (ImportError, AttributeError):
                pass
                
        # Replace the original tqdm implementation
        tqdm_module.tqdm = _null_tqdm
        
        # Also disable auto, notebook and cli versions
        if hasattr(tqdm_module, 'auto'):
            tqdm_module.auto.tqdm = _null_tqdm
        if hasattr(tqdm_module, 'notebook'):
            tqdm_module.notebook.tqdm = _null_tqdm
        if hasattr(tqdm_module, 'std'):
            tqdm_module.std.tqdm = _null_tqdm
        
        # For good measure, modify __class__ of tqdm for inheritance issues
        tqdm_module.tqdm.__class__ = type('null_tqdm', (), {'__call__': lambda *args, **kwargs: _null_tqdm})
except Exception:
    pass  # Silently fail if something goes wrong with the monkey patching

from .ml.engine import nl_to_css_fast, initialize_engine, download_models, models_are_downloaded
from .ml.html_processor import (
    extract_and_process,
    process_html_file,
    process_directory,
    minify_html_file
)


@click.group()
@click.version_option()
def main():
    """AI CSS Framework CLI - Convert natural language to CSS with AI."""
    pass


@main.command()
@click.argument('description')
@click.option('--selector', '-s', default='element', help='CSS selector to use')
def generate(description, selector):
    """Generate CSS from natural language description."""
    # Initialize the ML engine
    initialize_engine()
    
    # Generate CSS
    css_text = nl_to_css_fast(description, selector)
    click.echo(css_text)


@main.command()
@click.argument('input_path', type=click.Path(exists=True))
@click.argument('output_path', type=click.Path())
@click.option('--verbose', '-v', is_flag=True, help='Show detailed output')
@click.option('--disable-progress/--enable-progress', default=True, 
              help='Disable progress bars (default: disabled)')
@click.option('--max-passes', default=3, help='Maximum number of processing passes for AI tags (default: 3)')
def process(input_path, output_path, verbose, disable_progress, max_passes):
    """
    Process HTML/CSS files with AI styling.
    
    For HTML files: Extracts aicss attributes, processes <ai*> tags, and replaces with real CSS.
    For CSS files: Copies to the output path.
    For directories: Processes all HTML/CSS files recursively.
    
    Features:
    - Supports <aistyle> tags in the head section
    - Processes <ai*> tags (aibutton, aidiv, aip, etc.)
    - Converts aicss attributes to real CSS classes
    """
    # Make sure progress bars are disabled
    import os
    if disable_progress:
        os.environ["TQDM_DISABLE"] = "1"
        
    # Initialize the ML engine with no progress bars
    try:
        initialize_engine()
        
        # Enable multiple passes of processing to handle nested AI tags
        from .ml.html_processor import extract_and_process
        current_input = input_path
        temp_output = None
        final_output = output_path
        
        # First pass to handle standard processing
        success = extract_and_process(current_input, final_output)
        
        if verbose:
            click.echo(f"Completed initial processing pass")
            
        # Look for remaining AI tags
        import re
        
        if os.path.isfile(final_output):
            with open(final_output, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Check for any remaining AI tags
            ai_tag_pattern = r'<ai[^>]*>'
            remaining_tags = re.findall(ai_tag_pattern, content)
            
            if remaining_tags and verbose:
                click.echo(f"Found {len(remaining_tags)} remaining AI tags. Processing again...")
                
            # Process additional passes if needed
            if remaining_tags and max_passes > 1:
                for i in range(2, max_passes + 1):
                    success = extract_and_process(final_output, final_output)
                    if verbose:
                        click.echo(f"Completed processing pass {i}")
                    
                    # Check if we still have AI tags
                    with open(final_output, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    remaining_tags = re.findall(ai_tag_pattern, content)
                    if not remaining_tags:
                        if verbose:
                            click.echo(f"All AI tags processed. Done.")
                        break
        
        if success:
            click.echo(f"Successfully processed {input_path}")
            click.echo(f"Output saved to {output_path}")
        else:
            click.echo(f"Error processing {input_path}", err=True)
            
    except Exception as e:
        if verbose:
            import traceback
            click.echo(f"Error: {str(e)}", err=True)
            click.echo(traceback.format_exc(), err=True)
        else:
            click.echo(f"Error processing {input_path}. Run with --verbose for details.", err=True)


@main.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.argument('output_file', type=click.Path())
def minify(input_file, output_file):
    """Minify an HTML file."""
    success = minify_html_file(input_file, output_file)
    if success:
        click.echo(f"Minified HTML saved to {output_file}")
    else:
        click.echo("Failed to minify HTML", err=True)


class FileChangeHandler(FileSystemEventHandler):
    def __init__(self, directory, output_dir):
        self.directory = os.path.abspath(directory)
        self.output_dir = output_dir
        self.processing = False
        self.pending_files = set()
    
    def on_modified(self, event):
        if self.processing:
            return
        
        if event.is_directory:
            return
            
        if not (event.src_path.endswith('.html') or event.src_path.endswith('.htm')):
            return
            
        # Skip files in output directory to prevent recursion
        if self.output_dir and os.path.abspath(event.src_path).startswith(os.path.abspath(self.output_dir)):
            return
        
        # Add to pending files
        self.pending_files.add(event.src_path)
        
        # Process after a short delay to avoid duplicate events
        self.process_pending_files()
    
    def process_pending_files(self):
        if not self.pending_files:
            return
            
        # Set processing flag
        self.processing = True
        
        try:
            # Process each file
            for file_path in list(self.pending_files):
                # Skip if file no longer exists
                if not os.path.exists(file_path):
                    self.pending_files.remove(file_path)
                    continue
                
                # Determine output path
                if self.output_dir:
                    rel_path = os.path.relpath(file_path, self.directory)
                    out_file = os.path.join(self.output_dir, rel_path)
                else:
                    out_file = None
                
                # Process the file
                click.echo(f"Processing {file_path}")
                _, styles = process_html_file(file_path, out_file)
                click.echo(f"Extracted {len(styles)} style descriptions")
                
                # Remove from pending files
                self.pending_files.remove(file_path)
        finally:
            # Clear processing flag
            self.processing = False
            
            # If there are still pending files, process them
            if self.pending_files:
                self.process_pending_files()


@main.command()
@click.argument('directory', type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.option('--output', '-o', type=click.Path(), help='Output directory path')
def watch(directory, output):
    """Watch a directory for HTML file changes and process them automatically."""
    # Initialize the ML engine
    initialize_engine()
    
    # Create output directory if it doesn't exist
    if output:
        os.makedirs(output, exist_ok=True)
    
    # Start watching
    click.echo(f"Watching directory: {directory}")
    if output:
        click.echo(f"Output directory: {output}")
    
    # Create event handler and observer
    event_handler = FileChangeHandler(directory, output)
    observer = Observer()
    observer.schedule(event_handler, directory, recursive=True)
    observer.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        click.echo("Stopping file watcher...")
        observer.stop()
    observer.join()


@main.command()
@click.option('--force', is_flag=True, help='Force re-download of models')
@click.option('--model-dir', type=click.Path(), help='Custom directory to store models')
def download(force, model_dir):
    """Download ML models for offline use."""
    if not force and models_are_downloaded():
        click.echo("Models already downloaded. Use --force to re-download.")
        return
    
    click.echo("Downloading models...")
    success = download_models(force, model_dir)
    
    if success:
        click.echo("Models downloaded successfully")
    else:
        click.echo("Failed to download models", err=True)


@main.command()
def benchmark():
    """Run a benchmark to test processing speed."""
    # Test descriptions
    descriptions = [
        "blue background, white text, rounded corners",
        "primary color, bold, large text, centered, with shadow",
        "flex, space between, padding medium, gray background",
        "full width, small rounded corners, thin border, light gray background",
        "absolute position, top right corner, red background, white text, bold, small padding"
    ]
    
    # Initialize the ML engine
    initialize_engine()
    
    # Warm up
    click.echo("Warming up...")
    for _ in range(3):
        for desc in descriptions:
            nl_to_css_fast(desc)
    
    # Run benchmark
    click.echo("\nRunning benchmark...")
    total_time = 0
    num_runs = 10
    
    for i, desc in enumerate(descriptions, 1):
        start_time = time.time()
        
        for _ in range(num_runs):
            nl_to_css_fast(desc)
        
        end_time = time.time()
        avg_time = (end_time - start_time) * 1000 / num_runs  # in milliseconds
        total_time += avg_time
        
        click.echo(f"Description {i}: {avg_time:.2f}ms average ({num_runs} runs)")
    
    click.echo(f"\nOverall average: {total_time / len(descriptions):.2f}ms per description")


if __name__ == '__main__':
    main()