\# SYSTEM SPECIFICATION: PORTABLE MULTI-PROJECT MCP SERVER WITH DYNAMIC DISCOVERY



\## 1. Objective \& Context

Develop an isolated, highly portable, and model-agnostic MCP (Model Context Protocol) server containing a suite of developer skills (tools). 

\* This project must be completely self-contained so it can be pushed to GitHub and later cloned/installed into any other workspace/project.

\* It must support both high-tier models (like Claude 3.5) and smaller, local models (SLMs like LLaMA-3, Phi-4, Gemma-2) by exposing highly structured, strictly-validated Tool interfaces.



\---



\## 2. Tech Stack \& Architecture

\* \*\*Language:\*\* TypeScript (Node.js) or Python (choose the cleanest, most maintainable option).

\* \*\*Protocol:\*\* Anthropic's Model Context Protocol (MCP) SDK.

\* \*\*Transport:\*\* Strictly `StdioServerTransport` (standard input/output) to ensure universal compatibility with Claude Desktop, Cursor, Windsurf, and custom programmatic clients.

\* \*\*Isolation (Sandbox-First):\*\* Tools must never hardcode absolute project paths. All operations must resolve relative to the client's working directory (`process.cwd()`) or a path explicitly provided by the client.



\---



\## 3. Repository Structure

The generated project must have the following clean structure:





├── .gitignore

├── README.md                  # Comprehensive setup instructions (Git/npm/pip)

├── package.json               # (or pyproject.toml / requirements.txt)

├── tsconfig.json              # (if using TypeScript)

├── .skills.json.example       # Example project-level configuration file

└── src/

├── index.ts               # Entry point: Transport initialization \& lifecycle

├── server.ts              # MCP Server instance, tool registration \& request routing

├── config.ts              # Workspace discovery \& configuration parser (.skills.json)

└── tools/                 # Isolated, modular skill directories

├── projectAnalyzer.ts # AST/Metadata project scanner

└── fileOperations.ts  # Safe workspace file reader/writer (sandboxed)





\---



\## 4. Feature: Dynamic Tool Discovery (Feature Flags)

To prevent executing dangerous tools in sensitive projects, the server must dynamically determine which tools to expose based on a configuration file in the target workspace.



\### Discovery Protocol:

1\. Upon startup, the server must locate the user's current working directory (`process.cwd()`).

2\. Search for a configuration file named `.skills.json` in that directory.

3\. \*\*Filtering in `listTools`:\*\*

&#x20;  \* If `.skills.json` \*\*does not exist\*\*, register only a default, read-only safe toolset (e.g., `analyze\_project\_structure`).

&#x20;  \* If `.skills.json` \*\*exists\*\*, parse it and dynamically register ONLY the tools explicitly listed under `enabled\_skills` (and ensure they are not blacklisted in `disabled\_skills`).

4\. \*\*Error Handling:\*\* If a model attempts to call a tool that is not enabled for the current project, the server must return an explicit, descriptive error: `"Tool \[tool\_name] is disabled by the current project's configuration (.skills.json)"`.



\### Configuration Schema (`.skills.json`):

```json

{

&#x20; "enabled\_skills": \[

&#x20;   "analyze\_project\_structure",

&#x20;   "run\_local\_tests"

&#x20; ],

&#x20; "disabled\_skills": \[

&#x20;   "execute\_db\_query"

&#x20; ]

}

5\. Security Contract (Path Validation)

Since this server will be fetched from GitHub and executed locally across various workspaces, strict directory sandboxing is mandatory:



Implement a robust utility function to resolve and validate file paths.



Every tool receiving a file path argument must verify that the target path resolves inside the allowed workspace directory (process.cwd()).



If a path escape attempt is detected (e.g., passing ../../etc/passwd or /etc/passwd), immediately throw an error and abort execution.



6\. Target Skills to Implement (v1.0.0)

Skill 1: analyze\_project\_structure

Purpose: Allows any model (including smaller LLMs) to quickly grasp the architecture of an unfamiliar workspace without dumping entire files into the context.



Input Arguments Schema:



JSON

{

&#x20; "type": "object",

&#x20; "properties": {

&#x20;   "depth": {

&#x20;     "type": "integer",

&#x20;     "description": "Max directory depth to scan",

&#x20;     "default": 3

&#x20;   }

&#x20; }

}

Behavior: Recursively scans the workspace, respects .gitignore (ignoring node\_modules, build artifacts, .git, venvs), builds a lightweight tree representation of key code files, and extracts structural hints (e.g., languages used, configuration files found).



Skill 2: safe\_read\_file

Purpose: Safely reads file contents with sandboxing checks.



Input Arguments Schema:



JSON

{

&#x20; "type": "object",

&#x20; "properties": {

&#x20;   "file\_path": {

&#x20;     "type": "string",

&#x20;     "description": "Path to the file relative to workspace root"

&#x20;   }

&#x20; },

&#x20; "required": \["file\_path"]

}

7\. Deliverables \& Acceptance Criteria

Your output must include:



Complete, modular, production-ready code implementing the files described above.



A detailed README.md explaining:



How to build and compile the project (npm run build or equivalent).



How to configure the server in Claude Desktop (using the absolute path to the compiled JS file).



How to create and use the .skills.json file in target projects.

