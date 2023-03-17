import pytest

from templates.template_functions import reset_file_id_counter


@pytest.fixture(scope="function", autouse=True)
def reset_file_id_counter_per_test() -> None:
    """Resets the static file ID counter each test."""
    reset_file_id_counter()
