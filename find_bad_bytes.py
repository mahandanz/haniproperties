# find_bad_bytes.py
with open("listings.csv", "rb") as f:
    raw = f.read()

bad_positions = []
i = 0
while i < len(raw):
    try:
        raw[i:i+1].decode("utf-8")
        i += 1
    except UnicodeDecodeError:
        bad_positions.append(i)
        i += 1

print(f"Found {len(bad_positions)} problematic byte positions")
for pos in bad_positions[:20]:
    start = max(0, pos - 40)
    end = pos + 40
    print(f"\n--- position {pos} ---")
    print(raw[start:end])