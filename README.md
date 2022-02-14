# Basic JEDI Workflow

```mermaid
graph TD
    A([Initialization]) --> B([Read WRF-Hydro Restart])
    B --> C([Apply JEDI Filter])
    C --> D([Increment Restart])
    D --> F([Run WRF-Hydro, Advance Model ])
    F --> G([Model Done?])
    G --> no --> C
    G --> yes --> J([Finish])
```
