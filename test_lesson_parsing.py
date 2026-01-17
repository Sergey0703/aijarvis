import re

def parse_lesson_content(content: str):
    """
    Parses the lesson content into Vocabulary Focus and News Digest.
    """
    vocab_section = ""
    digest_section = content

    # Look for Vocabulary Focus
    vocab_match = re.search(r"Vocabulary Focus:(.*?)(?=---START_OF_DIGEST---|$)", content, re.DOTALL | re.IGNORECASE)
    if vocab_match:
        vocab_section = vocab_match.group(1).strip()

    # Look for Digest
    digest_match = re.search(r"---START_OF_DIGEST---(.*)", content, re.DOTALL)
    if digest_match:
        digest_section = digest_match.group(1).strip()
    
    return vocab_section, digest_section

# Test Cases
test_text = """
Some intro text.
Vocabulary Focus:
- Apple (яблоко)
- Banana (банан)
---START_OF_DIGEST---
1. News Title 1
Content here...
2. News Title 2
Content here...
"""

test_text_no_vocab = """
---START_OF_DIGEST---
Just news here.
"""

test_text_no_markers = "Just plain text."

print("Test 1 (Normal):")
v, d = parse_lesson_content(test_text)
print(f"Vocab: '{v}'")
print(f"Digest: '{d}'")

print("\nTest 2 (No Vocab):")
v, d = parse_lesson_content(test_text_no_vocab)
print(f"Vocab: '{v}'")
print(f"Digest: '{d}'")

print("\nTest 3 (No Markers):")
v, d = parse_lesson_content(test_text_no_markers)
print(f"Vocab: '{v}'")
print(f"Digest: '{d}'")
