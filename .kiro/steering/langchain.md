# LangChain

Tento projekt používá **LangChain 0.3.x** se stabilními verzemi.

## Verze

- `langchain==0.3.7`
- `langchain-google-genai==2.0.5`
- `langchain-core==0.3.15`
- `pydantic==2.9.2`

## Pravidla

- Používej přesné verze uvedené výše
- Importuj z `langchain` (ne `langchain_core`):
  - `from langchain.prompts import ChatPromptTemplate`
  - `from langchain.output_parsers import PydanticOutputParser`
  - `from langchain.schema import HumanMessage, SystemMessage`
- Dokumentace: https://docs.langchain.com/oss/python/langchain/overview

## Příklad

```python
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser

llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-lite")
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant"),
    ("user", "{input}")
])
chain = prompt | llm
```
