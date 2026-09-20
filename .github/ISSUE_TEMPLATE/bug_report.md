---
name: Something does not work
about: An error, a wrong result, or behaviour that surprised you
labels: bug
---

**What happened.**

**What you expected.**

**A script that shows it.**

```python
import jerlov
print(jerlov.__version__, jerlov.__file__)
```

<!-- The path matters: `python examples/foo.py` loads an installed copy in
preference to a working tree, which produces confusing failures. -->

**Versions.**
<!-- Python and NumPy. The package claims numpy>=1.22 and that claim is
tested, so a failure on an old NumPy is a real bug here. -->
