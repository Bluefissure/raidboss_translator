# raidboss_translator

## To use

1. copy-paste language locale from `***.js` to a file (take locale.json` for example)
2. Run in python console:

```python
from translator import Translator
t = Translator()
t.download_res()
t.init_db()
t.translate("locale.json")
```

