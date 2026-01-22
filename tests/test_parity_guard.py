
import pytest
from unittest.mock import MagicMock, patch
import sys
import ast
from pathlib import Path

# Import the module to test
sys.path.append(str(Path(__file__).parent.parent / "tools"))
import parity_guard
from parity_guard import ParityChecker

@pytest.fixture
def checker():
    return ParityChecker()

def test_ast_valid_explicit_usage(checker):
    """Test standard usage: args.field"""
    code = """
import argparse
parser = argparse.ArgumentParser()
parser.add_argument("--level")
args = parser.parse_args()
print(args.level)
    """
    with patch("pathlib.Path.read_text", return_value=code):
        # Patch the module-level FEATURES dictionary directly on the module object
        with patch.object(parity_guard, "FEATURES", {
            "level": {"cli_arg": "--level", "repolens_usage": "args.level"}
        }):
            checker.check_repolens()
            # Assert no errors
            assert not checker.errors, f"Errors found: {checker.errors}"
            # Verify pass message in stdout (captured by pytest if we didn't use capsys?
            # actually checking errors is enough for logic verification)

def test_ast_valid_getattr_usage(checker):
    """Test getattr usage: getattr(args, 'field')"""
    code = """
import argparse
args = parser.parse_args()
val = getattr(args, 'level')
    """
    with patch("pathlib.Path.read_text", return_value=code):
        with patch.object(parity_guard, "FEATURES", {
            "level": {"cli_arg": None, "repolens_usage": "args.level"}
        }):
            checker.check_repolens()
            assert not checker.errors

def test_ast_invalid_getattr_usage(checker):
    """Test invalid getattr: getattr(other, 'field') should FAIL"""
    code = """
import argparse
other = {}
val = getattr(other, 'level')
    """
    with patch("pathlib.Path.read_text", return_value=code):
        with patch.object(parity_guard, "FEATURES", {
            "level": {"cli_arg": None, "repolens_usage": "args.level"}
        }):
            checker.check_repolens()
            assert len(checker.errors) == 1
            assert "not accessed" in checker.errors[0]

def test_ast_generic_usage_valid(checker):
    """Test generic usage: vars(args) + literal key usage"""
    code = """
import argparse
args = parser.parse_args()
d = vars(args)
print(d['level'])
    """
    with patch("pathlib.Path.read_text", return_value=code):
        with patch.object(parity_guard, "FEATURES", {
            "level": {"cli_arg": None, "repolens_usage": "args.level"}
        }):
            checker.check_repolens()
            assert not checker.errors

def test_ast_generic_usage_invalid_help_only(checker):
    """
    Counterexample: vars(args) exists, but 'level' is ONLY in a help string.
    """
    code = """
import argparse
args = parser.parse_args()
d = vars(args)
print("Configure the level of detail")
    """
    with patch("pathlib.Path.read_text", return_value=code):
        with patch.object(parity_guard, "FEATURES", {
            "level": {"cli_arg": None, "repolens_usage": "args.level"}
        }):
            checker.check_repolens()
            # This should FAIL because 'level' is not used as a key/access
            assert len(checker.errors) == 1, "Should fail if 'level' is only in a string description"

def test_ast_generic_usage_invalid_quoted_in_help(checker):
    """Harder case: The word is quoted in a string but not used."""
    code = """
import argparse
args = parser.parse_args()
d = vars(args)
print("Use the 'level' flag to set...")
    """
    with patch("pathlib.Path.read_text", return_value=code):
        with patch.object(parity_guard, "FEATURES", {
            "level": {"cli_arg": None, "repolens_usage": "args.level"}
        }):
            checker.check_repolens()
            assert len(checker.errors) == 1
