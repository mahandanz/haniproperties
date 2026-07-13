import ftfy

with open("listings.csv", "rb") as f:
    raw = f.read()

text = raw.decode("utf-8", errors="replace")
fixed = ftfy.fix_text(text)
fixed = ftfy.fix_text(fixed)  # second pass in case of double-encoding

with open("listings.csv", "w", encoding="utf-8-sig", newline="") as f:
    f.write(fixed)

print("Done — file re-saved as clean UTF-8")