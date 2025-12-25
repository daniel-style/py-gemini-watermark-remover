#!/usr/bin/env python3
"""
Gemini Watermark Tool - Command Line Interface

A command-line tool to remove Gemini watermarks from images.
"""

import argparse
import sys
from pathlib import Path
from .watermark_remover import WatermarkRemover, WatermarkSize, process_image, process_directory, is_url


__version__ = "0.2.5"


def print_banner():
    """Print ASCII banner"""
    banner = r"""
╔═╗┌─┐┌┬┐┬┌┐┌┬             
║ ╦├┤ ││││││││             
╚═╝└─┘┴ ┴┴┘└┘┴             
╦ ╦┌─┐┌┬┐┌─┐┬─┐┌┬┐┌─┐┬─┐┬┌─
║║║├─┤ │ ├┤ ├┬┘│││├─┤├┬┘├┴┐
╚╩╝┴ ┴ ┴ └─┘┴└─┴ ┴┴ ┴┴└─┴ ┴
╦═╗┌─┐┌┬┐┌─┐┬  ┬┌─┐┬─┐     
╠╦╝├┤ ││││ │└┐┌┘├┤ ├┬┘     
╩╚═└─┘┴ ┴└─┘ └┘ └─┘┴└─     

 Watermark Remover - Python Edition
 Version: {}
""".format(__version__)
    print(banner)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Remove Gemini watermarks from images using reverse alpha blending',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Simple mode - edit file in-place
  %(prog)s image.jpg

  # Specify output file
  %(prog)s -i watermarked.jpg -o clean.jpg

  # Batch processing
  %(prog)s -i ./input_folder/ -o ./output_folder/

  # Force watermark size
  %(prog)s -i image.jpg -o clean.jpg --force-small
        """
    )

    # Positional argument for simple mode
    parser.add_argument(
        'simple_input',
        nargs='?',
        help='Input image file (simple mode - edits in-place)'
    )

    # Input/Output arguments
    parser.add_argument(
        '-i', '--input',
        type=str,
        help='Input image file or directory'
    )

    parser.add_argument(
        '-o', '--output',
        type=str,
        help='Output image file or directory'
    )

    # Operation mode
    parser.add_argument(
        '-r', '--remove',
        action='store_true',
        default=True,
        help='Remove watermark (default behavior)'
    )

    parser.add_argument(
        '--add',
        action='store_true',
        help='Add watermark (for testing)'
    )

    # Watermark size options
    parser.add_argument(
        '--force-small',
        action='store_true',
        help='Force 48×48 watermark size'
    )

    parser.add_argument(
        '--force-large',
        action='store_true',
        help='Force 96×96 watermark size'
    )

    # Logo value
    parser.add_argument(
        '--logo-value',
        type=float,
        default=255.0,
        help='Logo brightness value (default: 255.0 = white)'
    )

    # Detection options
    parser.add_argument(
        '--no-detect',
        action='store_true',
        help='Disable automatic watermark detection (process all images)'
    )

    # Output options
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose output'
    )

    parser.add_argument(
        '-q', '--quiet',
        action='store_true',
        help='Suppress all output except errors'
    )

    parser.add_argument(
        '-b', '--banner',
        action='store_true',
        help='Show full ASCII banner'
    )

    # Version
    parser.add_argument(
        '-V', '--version',
        action='version',
        version=f'%(prog)s {__version__}'
    )

    args = parser.parse_args()

    # Show banner if requested
    if args.banner and not args.quiet:
        print_banner()

    # Determine operation mode
    remove_watermark = not args.add

    # Determine force size
    force_size = None
    if args.force_small:
        force_size = WatermarkSize.SMALL
    elif args.force_large:
        force_size = WatermarkSize.LARGE

    # Handle simple mode (single argument)
    if args.simple_input and not args.input:
        input_path = Path(args.simple_input)

        if not input_path.exists():
            print(f"Error: File not found: {input_path}", file=sys.stderr)
            return 1

        if not args.quiet:
            print(f"⚠️  Warning: Simple mode will overwrite the original file!")
            print(f"Processing: {input_path.name}")

        # Process in-place
        success = process_image(
            input_path,
            input_path,
            remove=remove_watermark,
            force_size=force_size,
            logo_value=args.logo_value,
            auto_detect=not args.no_detect
        )

        if success:
            if not args.quiet:
                print("✓ Done!")
            return 0
        else:
            print("✗ Failed!", file=sys.stderr)
            return 1

    # Handle standard mode (input + output)
    if not args.input or not args.output:
        print("Error: Both --input and --output are required (or use simple mode)", file=sys.stderr)
        parser.print_help()
        return 1

    input_str = args.input
    output_path = Path(args.output)

    # Check if input is URL
    if is_url(input_str):
        if not args.quiet:
            print(f"Processing remote image...")

        success = process_image(
            input_str,
            output_path,
            remove=remove_watermark,
            force_size=force_size,
            logo_value=args.logo_value,
            auto_detect=not args.no_detect
        )

        if success:
            if not args.quiet:
                print("✓ Done!")
            return 0
        else:
            print("✗ Failed!", file=sys.stderr)
            return 1

    input_path = Path(input_str)

    if not input_path.exists():
        print(f"Error: Input path not found: {input_path}", file=sys.stderr)
        return 1

    # Single file processing
    if input_path.is_file():
        if not args.quiet:
            print(f"Processing: {input_path.name}")

        success = process_image(
            input_path,
            output_path,
            remove=remove_watermark,
            force_size=force_size,
            logo_value=args.logo_value,
            auto_detect=not args.no_detect
        )

        if success:
            if not args.quiet:
                print("✓ Done!")
            return 0
        else:
            print("✗ Failed!", file=sys.stderr)
            return 1

    # Directory processing
    elif input_path.is_dir():
        if not args.quiet:
            print(f"Batch processing: {input_path} -> {output_path}")

        success_count, skip_count, fail_count = process_directory(
            input_path,
            output_path,
            remove=remove_watermark,
            force_size=force_size,
            logo_value=args.logo_value,
            auto_detect=not args.no_detect
        )

        if fail_count == 0:
            if not args.quiet:
                print("✓ All images processed successfully!")
            return 0
        else:
            print(f"⚠ Completed with errors: {success_count} succeeded, {fail_count} failed",
                  file=sys.stderr)
            return 1

    else:
        print(f"Error: Invalid input path: {input_path}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
