#!/usr/bin/env python3

def test_messages_format():
    """Test that the new messages format works correctly"""
    from ui_components import get_initial_messages
    from ui_handlers import clear_history
    
    print("Testing messages format...")
    print("=" * 50)
    
    # Test initial messages
    initial = get_initial_messages()
    print("Initial messages format:")
    for i, msg in enumerate(initial):
        print(f"  {i+1}. Type: {type(msg)}")
        if isinstance(msg, dict):
            print(f"     Keys: {list(msg.keys())}")
            print(f"     Role: {msg.get('role', 'MISSING')}")
            print(f"     Content: {msg.get('content', 'MISSING')[:50]}...")
        else:
            print(f"     Value: {msg}")
        print()
    
    # Test clear history
    cleared, dropdown, text = clear_history()
    print("Clear history result:")
    print(f"  Type: {type(cleared)}")
    print(f"  Length: {len(cleared)}")
    if cleared:
        print(f"  First message type: {type(cleared[0])}")
        if isinstance(cleared[0], dict):
            print(f"  First message keys: {list(cleared[0].keys())}")
    
    print()
    if all(isinstance(msg, dict) and 'role' in msg and 'content' in msg for msg in initial):
        print("✅ All messages have correct format!")
    else:
        print("❌ Some messages have incorrect format!")

if __name__ == "__main__":
    test_messages_format() 