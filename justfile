# List all available commands
default:
    @just --list

# Run all tests
test:
    poetry run pytest tests/

# Run tests with verbose output
test-v:
    poetry run pytest tests/ -v

# Run tests with print output enabled
test-s:
    poetry run pytest tests/ -s

# Run tests matching a specific pattern (usage: just test-k "pattern")
test-k pattern:
    poetry run pytest tests/ -k "{{pattern}}"

# Run the Streamlit app
app:
    poetry run streamlit run app.py 