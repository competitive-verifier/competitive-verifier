---
title: Multiple document
keep_single: true
documentation_of:
- visible.hello
- no-index.hello
- hidden.hello
---

# Multiple document


```yml
title: Multiple document
keep_single: true
documentation_of:
- visible.hello
- no-index.hello
- hidden.hello
```

Multiple files can be specified for `documentation_of`.
If `keep_single` is true, documentation of those files will be generated. If `keep_single` is not specified or is false, a redirect will be generated.

See this page for an example of the true case; see [encodings](../encoding/encodings) for an example of the false case.