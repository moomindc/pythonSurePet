# Virtual Environment Setup

Run these commands from the `TeamsCLI` directory.

## 1. Create the virtual environment

```powershell
python -m venv venv
```

## 2. Activate it

```powershell
.\venv\Scripts\Activate.ps1
.\venv\Scripts\activate
```


Your prompt will change to show `(venv)` when active.

> **If you see an execution policy error**, run this once then retry:
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```

## 3. Install dependencies

```powershell
pip install -r requirements.txt
```

## 4. Run the CLI

```powershell
python surepet.py
```

---

## Deactivate when done

```powershell
deactivate
```

## Re-activate in a future session

```powershell
.\venv\Scripts\Activate.ps1
```
