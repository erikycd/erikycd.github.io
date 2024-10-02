---
permalink: /
title: "About me"
excerpt: "Main"
author_profile: true
redirect_from: 
  - /about/
  - /about.html
---

I am a scientist with a track record in the field of computer science. Currently, I serve as an associate researcher at UNAM, spearheading projects focused mainly on artificial intelligence in education (AIEd).

Main interests
======
* 👾 Artificial intelligence
* 💬 Natural language processing
* 👀 Computer vision
* 📚 Educational Technology (EdTech)
* 🏥 Medical image analysis

```python
import pandas as pd

# Define elements
elements = {
    "👾": "Artificial intelligence",
    "💬": "Natural language processing",
    "👀": "Computer vision",
    "📚": "Educational Technology (EdTech)",
    "🏥": "Medical image analysis"
}

# Create a dataframe with dictionary
df = pd.DataFrame(list(elements.items()), columns=["Emoji", "Field"])

# Show dataframe
print("List of interests:")
print(df)
```