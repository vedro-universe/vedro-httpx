import sys

from vedro_httpx.spec_generator import APISpecBuilder, HARReader, OpenAPISpecGenerator


def generate_spec(har_directory: str) -> str:
    """
    Generate an OpenAPI specification from HAR files in a specified directory.

    This function reads all HAR files from the provided directory, extracts
    HTTP request and response data, builds an API specification, and converts
    it into an OpenAPI specification format.

    :param har_directory: The directory path where HAR files are located.
    :return: The generated OpenAPI specification as a YAML string.
    """
    har_reader = HARReader(har_directory)
    entries = har_reader.get_entries()

    api_spec_builder = APISpecBuilder()
    api_spec = api_spec_builder.build_spec(entries)

    open_api_spec_generator = OpenAPISpecGenerator()
    open_api_spec = open_api_spec_generator.generate_spec(api_spec)

    return open_api_spec


def main() -> None:
    """
    Main entry point of the script.

    This function checks for the correct usage of the script by verifying
    the command-line arguments, generates an OpenAPI specification from the
    HAR directory provided as input, and prints the result.
    """
    if len(sys.argv) != 2:
        print("Usage: vedro-httpx <har_directory>")
        sys.exit(1)

    open_api_spec = generate_spec(sys.argv[1])
    print(open_api_spec)


if __name__ == "__main__":
    main()
