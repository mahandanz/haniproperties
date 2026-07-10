path = "listings.csv"

with open(path, "rb") as f:
    data = f.read()

try:
    data.decode("utf-8-sig")
    print("File is valid UTF-8 — no issue found.")
except UnicodeDecodeError as e:
    pos = e.start
    print(f"Bad byte 0x{data[pos]:02x} at position {pos}")
    # Show context around the error
    start = max(0, pos - 100)
    end = min(len(data), pos + 50)
    context = data[start:end]
    print("\n--- Context (raw bytes, may show garbage) ---")
    print(context.decode("cp1252", errors="replace"))

    # Figure out which line number this falls on
    line_num = data[:pos].count(b"\n") + 1
    print(f"\nThis is roughly on line {line_num} of the CSV.")