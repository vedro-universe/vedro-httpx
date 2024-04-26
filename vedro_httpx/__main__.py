import sys

from vedro_httpx.spec_generator import APISpecBuilder, HARReader, OpenAPISpecGenerator


def generate_spec(har_directory: str) -> str:
    har_reader = HARReader(har_directory)
    entries = har_reader.get_entries()

    api_spec_builder = APISpecBuilder()
    api_spec = api_spec_builder.build_spec(entries)

    open_api_spec_generator = OpenAPISpecGenerator()
    open_api_spec = open_api_spec_generator.generate_spec(api_spec)

    return open_api_spec


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: vedro-httpx <har_directory>")
        sys.exit(1)

    open_api_spec = generate_spec(sys.argv[1])
    print(open_api_spec)


if __name__ == "__main__":
    main()
