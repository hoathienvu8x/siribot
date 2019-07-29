# An AIML chat Resful with python

> The chatbot AIML resful using python no dependencies frameworks

```bash
#!/bin/bash

ok=$(python -c "try:
	import aimll
	print('OK')
except ImportError:
	print('NO')")

if [ "$ok" == "NO" ]; then
	pip install aiml
fi

echo "Install completed"
```

## Using code

```bash
python siri.py
```

To test open webbrowser `http://localhost:8800/question/hello`