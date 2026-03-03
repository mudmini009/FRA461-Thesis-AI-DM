# Run via: conda activate ai_dm_core && pytest tests/test_toon_bidirectional.py
import sys
import os
import pytest

# Ensure we can import from src
sys.path.append(os.getcwd())

from src.models.toon_converter import TOONConverter

def test_toon_bidirectional_simple_match():
    """Test 1: Standard Python Dict -> TOON -> Python Dict (Exact match verification)"""
    mock_llm_response = 'type:FIXED|command:ATTACK|target:e2|attack_type:melee'
    
    decoded = TOONConverter.decode(mock_llm_response)
    
    assert decoded["type"] == "FIXED"
    assert decoded["command"] == "ATTACK"
    assert decoded["target"] == "e2"
    assert decoded["attack_type"] == "melee"

def test_toon_bidirectional_edge_cases():
    """Test 2: Edge cases (missing fields, weird characters, booleans, nulls)"""
    # LLM might occasionally wrap with quotes or spaces, throw in nulls, or weird casing
    mock_llm_response = '   type : CREATIVE | allowed:"true" | consumed_item:null | dc: 15 | array_test:[a, b, c] '
    
    decoded = TOONConverter.decode(mock_llm_response)
    
    assert decoded["type"] == "CREATIVE"
    assert decoded["allowed"] is True
    assert decoded["consumed_item"] is None
    assert decoded["dc"] == 15
    assert decoded["array_test"] == ["a", "b", "c"]
    
def test_toon_bidirectional_empty_handling():
    """Test 2a: Handling completely malformed or empty strings safely"""
    decoded_empty = TOONConverter.decode("")
    assert decoded_empty == {}
    
    decoded_malformed = TOONConverter.decode("just a random string no colons")
    assert decoded_malformed == {}
    
    decoded_markdown = TOONConverter.decode("```text\ntype:FIXED|command:MOVE\n```")
    assert decoded_markdown["type"] == "FIXED"
    assert decoded_markdown["command"] == "MOVE"

def test_toon_bidirectional_llm_simulation():
    """Test 3: LLM Mock Simulation for actual Arbiter output"""
    # Simulating what get_creative_judgment will return
    mock_llm_response = 'allowed:false|reason:You dont have a rope in your inventory to tie them up|check_stat:NONE|dc:99|on_success_condition:null|target_name_guess:Goblin Scavenger|consumed_item:null'
    
    decoded = TOONConverter.decode(mock_llm_response)
    
    assert decoded["allowed"] is False
    assert decoded["reason"] == "You dont have a rope in your inventory to tie them up"
    assert decoded["check_stat"] == "NONE"
    assert decoded["dc"] == 99
    assert decoded["on_success_condition"] is None
    assert decoded["target_name_guess"] == "Goblin Scavenger"
    assert decoded["consumed_item"] is None

if __name__ == "__main__":
    pytest.main(["-v", "tests/test_toon_bidirectional.py"])
