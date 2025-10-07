
# UV Installation --> powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"        
> uv init   
> uv venv rag_venv
> rag_venv\Scripts\activate

> uv add -r .\requirements.txt
> uv add ipykernel


Step 1: Activate your global venv

> uv venv activate global_venv
(global_venv) PS D:\krishna-codejournal>

Step 2: Install Jupyter and ipykernel (if not installed in global venv)

uv pip install jupyter ipykernel

Step 3: Register the global venv as a Jupyter kernel

python -m ipykernel install --user --name=global_venv --display-name "Python (global_venv)"

Step 4: Switch your notebook to this kernel

- Jupyter Notebook/Lab:
  Open your notebook → Kernel → Change Kernel → Python (global_venv)

- VS Code:
  Click the kernel selector (top right) → choose Python (global_venv)