
# UV Installation

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

## Initialize UV

```sh
uv init
```

## Create Virtual Environment

```sh
uv venv 
.venv\Scripts\activate
```

## Install Requirements

```sh
uv add -r .\requirements.txt
uv add ipykernel
```