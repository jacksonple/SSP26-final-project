# PROMPT.md

## zero-shot

```text
Identify the key data elements (KDEs) in the security document '{doc_name}'. For each KDE provide its name and the associated requirements. Format output as YAML:

element1:
  name: <element name>
  requirements:
    - <req1>
    - <req2>

Document:
{doc_text}

YAML output:
```

## few-shot

```text
Example 1:
Document: '1.1 Users must have unique accounts. 1.2 Passwords must be 12+ characters.'
Output:
element1:
  name: User Accounts
  requirements:
    - Users must have unique accounts
    - Passwords must be 12+ characters

Example 2:
Document: '2.1 All traffic must be encrypted. 2.2 Use TLS 1.2 or higher.'
Output:
element1:
  name: Network Encryption
  requirements:
    - All traffic must be encrypted
    - Use TLS 1.2 or higher

Now identify KDEs in document '{doc_name}':
{doc_text}

Output YAML:
```

## chain-of-thought

```text
Analyze security document '{doc_name}' step by step.

Step 1: List all distinct security topics in the document.
Step 2: For each topic, collect all related requirements.
Step 3: Assign each topic a short descriptive name (the KDE name).
Step 4: Output the result as YAML:

element1:
  name: <KDE name>
  requirements:
    - <requirement>

Document:
{doc_text}

Follow steps 1-4 and produce the YAML output:
```
