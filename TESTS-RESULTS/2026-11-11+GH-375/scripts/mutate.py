import sys
path, old, new = sys.argv[1], sys.argv[2].encode().decode('unicode_escape'), sys.argv[3].encode().decode('unicode_escape')
s = open(path).read()
assert s.count(old) == 1, f"mutation anchor not unique/found: {old[:50]!r}"
open(path, "w").write(s.replace(old, new))
