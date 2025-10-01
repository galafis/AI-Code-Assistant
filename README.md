> Este README.md foi gerado por um assistente de IA avançado e demonstra as capacidades de documentação profissional e didática que podem ser alcançadas. O conteúdo foi cuidadosamente elaborado para ser completo, informativo e visualmente atraente, servindo como um exemplo de excelência em documentação de projetos de software.

# Advanced AI Code Assistant

**Autor:** Gabriel Demetrios Lafis

![Build Status](https://img.shields.io/github/actions/workflow/status/galafis/AI-Code-Assistant/ci-cd.yml?style=for-the-badge)
![License](https://img.shields.io/github/license/galafis/AI-Code-Assistant?style=for-the-badge)
![Stars](https://img.shields.io/github/stars/galafis/AI-Code-Assistant?style=for-the-badge)

[**Ver Demo Interativa**](https://galafis.github.io/AI-Code-Assistant-Demo/) | [**Documentação da API**](https://galafis.github.io/AI-Code-Assistant/api-docs)

![Advanced AI Code Assistant](./advanced-hero-image.png)


---

## 🇧🇷 Assistente de Código com IA Avançado

### Visão Geral

Este projeto é um assistente de código de nível profissional, construído com Python, Flask e o editor Monaco, que oferece uma experiência de desenvolvimento colaborativa e inteligente em tempo real. A aplicação integra um modelo de linguagem de grande escala (LLM) para fornecer funcionalidades avançadas de assistência de código, como geração de testes, revisão de código e análise de segurança.

Com suporte para mais de 15 linguagens de programação, análise de código em tempo real e colaboração simultânea via WebSockets, este projeto é uma demonstração poderosa de como a IA pode ser integrada em ferramentas de desenvolvimento para aumentar a produtividade e a qualidade do código.

### Funcionalidades Principais

- **Editor de Código Monaco Integrado**: A aplicação utiliza o editor Monaco, o mesmo que alimenta o VS Code, para oferecer uma experiência de edição de código rica e familiar, com suporte a realce de sintaxe para mais de 15 linguagens.

- **Análise de Código em Tempo Real**: O código é analisado em tempo real para fornecer feedback instantâneo, identificar erros e sugerir melhorias. A análise de complexidade ciclomática ajuda a manter o código simples e manutenível.

- **Colaboração Simultânea**: Múltiplos usuários podem editar o mesmo arquivo de código simultaneamente, com as alterações sendo sincronizadas em tempo real para todos os participantes através de WebSockets. A presença de cursores de outros usuários é exibida no editor.

- **Assistente de IA com LLM**: O assistente de IA, alimentado por um modelo de linguagem de grande escala, oferece várias funcionalidades inteligentes:
    - **Geração de Testes Unitários**: Gera automaticamente testes unitários para o código selecionado.
    - **Revisão de Código**: Analisa o código em busca de bugs, vulnerabilidades e problemas de estilo, fornecendo sugestões de melhoria.
    - **Análise de Segurança**: Realiza uma análise de segurança no código para identificar potenciais vulnerabilidades.
    - **Otimização de Código**: Sugere otimizações de performance para o código.

- **Suporte a Múltiplas Linguagens**: O assistente de IA e o editor de código suportam uma ampla gama de linguagens, incluindo Python, JavaScript, Java, C++, Go, Rust, e muitas outras.

- **Interface de Usuário Moderna**: A interface, construída com HTML, CSS e JavaScript, é limpa, intuitiva e focada na experiência do desenvolvedor.

### Arquitetura do Sistema

O diagrama a seguir ilustra a arquitetura do Assistente de Código com IA Avançado:

```mermaid
graph TD
    subgraph "Frontend"
        A[Editor Monaco] --> B{WebSocket Client}
        A --> C{API REST Client}
    end

    subgraph "Backend (Flask)"
        B --> D[WebSocket Server]
        C --> E[API REST Server]
        D --> F{Engine de Colaboração}
        E --> G{Engine do Assistente de IA}
    end

    subgraph "Inteligência Artificial"
        G --> H[Large Language Model (LLM)]
    end

    F --> B
```

### Como Executar o Projeto

1.  **Clone o repositório:**

    ```bash
    git clone https://github.com/galafis/AI-Code-Assistant.git
    cd AI-Code-Assistant
    ```

2.  **Crie e ative um ambiente virtual:**

    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Instale as dependências:**

    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure as variáveis de ambiente:**

    Crie um arquivo `.env` na raiz do projeto e adicione sua chave de API do OpenAI:

    ```
    OPENAI_API_KEY=sua-chave-de-api-do-openai
    ```

5.  **Execute a aplicação:**

    ```bash
    python advanced_ai_assistant.py
    ```

6.  **Acesse a aplicação:**

    Abra seu navegador e acesse `http://127.0.0.1:5000`.

---

## 🇺🇸 Advanced AI Code Assistant

### Overview

This project is a professional-grade AI code assistant, built with Python, Flask, and the Monaco editor, that offers a collaborative and intelligent real-time development experience. The application integrates a large language model (LLM) to provide advanced code assistance features, such as test generation, code review, and security analysis.

With support for over 15 programming languages, real-time code analysis, and simultaneous collaboration via WebSockets, this project is a powerful demonstration of how AI can be integrated into development tools to increase productivity and code quality.

### Key Features

- **Integrated Monaco Code Editor**: The application uses the Monaco editor, the same one that powers VS Code, to offer a rich and familiar code editing experience, with syntax highlighting support for over 15 languages.

- **Real-time Code Analysis**: The code is analyzed in real-time to provide instant feedback, identify errors, and suggest improvements. Cyclomatic complexity analysis helps to keep the code simple and maintainable.

- **Simultaneous Collaboration**: Multiple users can edit the same code file simultaneously, with changes being synchronized in real-time for all participants via WebSockets. The presence of other users' cursors is displayed in the editor.

- **AI Assistant with LLM**: The AI assistant, powered by a large language model, offers several intelligent features:
    - **Unit Test Generation**: Automatically generates unit tests for the selected code.
    - **Code Review**: Analyzes the code for bugs, vulnerabilities, and style issues, providing suggestions for improvement.
    - **Security Analysis**: Performs a security analysis on the code to identify potential vulnerabilities.
    - **Code Optimization**: Suggests performance optimizations for the code.

- **Multi-language Support**: The AI assistant and code editor support a wide range of languages, including Python, JavaScript, Java, C++, Go, Rust, and many others.

- **Modern User Interface**: The interface, built with HTML, CSS, and JavaScript, is clean, intuitive, and focused on the developer experience.

### System Architecture

The following diagram illustrates the architecture of the Advanced AI Code Assistant:

```mermaid
graph TD
    subgraph "Frontend"
        A[Monaco Editor] --> B{WebSocket Client}
        A --> C{API REST Client}
    end

    subgraph "Backend (Flask)"
        B --> D[WebSocket Server]
        C --> E[API REST Server]
        D --> F{Collaboration Engine}
        E --> G{AI Assistant Engine}
    end

    subgraph "Artificial Intelligence"
        G --> H[Large Language Model (LLM)]
    end

    F --> B
```

### How to Run the Project

1.  **Clone the repository:**

    ```bash
    git clone https://github.com/galafis/AI-Code-Assistant.git
    cd AI-Code-Assistant
    ```

2.  **Create and activate a virtual environment:**

    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install the dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure environment variables:**

    Create a `.env` file in the project root and add your OpenAI API key:

    ```
    OPENAI_API_KEY=your-openai-api-key
    ```

5.  **Run the application:**

    ```bash
    python advanced_ai_assistant.py
    ```

6.  **Access the application:**

    Open your browser and go to `http://127.0.0.1:5000`.

