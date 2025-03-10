# PetMate Tests

This directory contains unit tests for the PetMate application.

## Test Structure

- `conftest.py`: Contains pytest fixtures used across test files
- `test_auth.py`: Tests for authentication functionality
- `test_routes.py`: Tests for main routes
- `test_gallery.py`: Tests for the gallery functionality
- `test_admin.py`: Tests for admin functionality

## Running Tests

To run all tests:

```bash
python -m pytest
```

To run specific test files:

```bash
python -m pytest tests/test_auth.py
```

To run specific test functions:

```bash
python -m pytest tests/test_auth.py::TestAuth::test_register_and_login
```

To run tests with specific markers:

```bash
python -m pytest -m gallery
```

## Known Issues

There are currently some issues with the tests:

1. **Pet Model Constraints**: The `Pet` model has a `NOT NULL` constraint on the `owner_id` field, but some tests are trying to create pets without setting this field.
2. **Form Field Mismatch**: In the `add_pet` route, the form expects a `temperament` field, but our test is sending a `bio` field.
3. **Template Content Assertions**: Some tests are looking for specific text in the response that may not be present in the actual templates.

## Fixing the Tests

To fix these issues:

1. Make sure all `Pet` objects created in tests have a valid `owner_id`.
2. Update the test data to match the expected form fields in the routes.
3. Simplify assertions to check for status codes rather than specific content when the content may vary.

## Adding Markers to Tests

You can add markers to tests by adding a decorator:

```python
@pytest.mark.gallery
def test_something():
    # Test code here
```

Available markers are listed in the `pytest.ini` file.

## Test Coverage

To run tests with coverage report:

```bash
python -m pytest --cov=app
```

For a detailed HTML coverage report:

```bash
python -m pytest --cov=app --cov-report=html
```

This will create a directory called `htmlcov` with the coverage report.

## Test Database

The tests use a separate testing database configuration that's specified in the `create_app` function when the `testing` parameter is provided. Make sure your app's `config.py` defines appropriate testing database settings. 