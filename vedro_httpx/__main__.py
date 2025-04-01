import argparse
from typing import Optional

from vedro_httpx.spec_generator import APISpecBuilder, HARReader, OpenAPISpecGenerator


def generate_spec(har_directory: str, *, base_url: Optional[str] = None) -> str:
    """
    Generate an OpenAPI specification from HAR files in a specified directory.

    This function reads all HAR files from the provided directory, extracts HTTP
    request and response data, builds an API specification, and converts it into an
    OpenAPI specification format. If a base_url is provided, only entries whose full
    URL starts with the given base_url are processed and grouped under that URL.

    :param har_directory: The directory path where HAR files are located.
    :param base_url: Optional base URL to filter and group entries.
    :return: The generated OpenAPI specification as a YAML string.
    """
    har_reader = HARReader(har_directory)
    entries = har_reader.get_entries()

    api_spec_builder = APISpecBuilder()
    api_spec = api_spec_builder.build_spec(entries, base_url=base_url)

    open_api_spec_generator = OpenAPISpecGenerator()
    open_api_spec = open_api_spec_generator.generate_spec(api_spec)

    return open_api_spec


def main() -> None:
    """
    Main entry point of the script.

    This function parses command-line arguments to determine the HAR directory and an optional
    base URL filter, generates an OpenAPI specification from the HAR files located in the provided
    directory, and prints the resulting specification.
    """
    parser = argparse.ArgumentParser(description="Generate OpenAPI spec from HAR files")
    parser.add_argument("har_directory", help="Directory containing HAR files")

    help_text = (
        "Optional base URL filter. Only process HAR entries with URLs starting with this value. "
        "Examples: 'http://localhost:8080/api' or 'http://localhost:8080/api/v1'"
    )
    parser.add_argument("--base-url", help=help_text, default=None)

    args = parser.parse_args()
    open_api_spec = generate_spec(args.har_directory, base_url=args.base_url)
    print(open_api_spec)


if __name__ == "__main__":
    main()
