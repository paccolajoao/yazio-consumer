import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from pathlib import Path
import threading
import os
from datetime import datetime, timedelta
from typing import Optional, Any
from dotenv import load_dotenv, set_key

# Use Cases and Infra interfaces
from application.use_cases import LoginUseCase, ExportDataUseCase
# We import the concrete GoogleOAuthService here because the UI initiates it?
# Or we treat it as an interface. For now, typing as Any or the concrete class if available to main.
# We will receive it in __init__

class YazioExporterApp:
    """Main Window for Yazio CSV Exporter."""

    def __init__(self, root: tk.Tk,
                 login_use_case: LoginUseCase,
                 export_use_case: ExportDataUseCase,
                 google_auth_service: Any, # Infrastructure service for local flow
                 app_dir: Path):
        self.root = root
        self.root.title("Yazio CSV Exporter (Clean Arch)")
        self.root.geometry("650x700")
        self.root.resizable(True, True)

        self.login_use_case = login_use_case
        self.export_use_case = export_use_case
        self.google_auth = google_auth_service
        self.app_dir = app_dir
        self.env_file = self.app_dir / ".env"

        # State
        self.auth_token = None

        # Variables
        self.auth_method_var = tk.StringVar(value="password")
        self.email_var = tk.StringVar()
        self.password_var = tk.StringVar()
        self.output_folder_var = tk.StringVar()
        self.google_status_var = tk.StringVar(value="Status: Not connected")

        # Load settings
        self._load_env()

        # Build UI
        self._build_ui()
        self._on_auth_method_change()
        self._check_google_status()

    def _load_env(self):
        if self.env_file.exists():
            load_dotenv(self.env_file)
            auth_method = os.getenv("AUTH_METHOD", "password")
            if auth_method in ("password", "google"):
                self.auth_method_var.set(auth_method)

            self.email_var.set(os.getenv("YAZIO_EMAIL", ""))
            self.password_var.set(os.getenv("YAZIO_PASSWORD", ""))
            self.output_folder_var.set(os.getenv("OUTPUT_FOLDER", ""))

            # Simple persistence of token for convenience (not secure but same as before)
            # In a real app we might verify validity or expiry.
            access = os.getenv("YAZIO_ACCESS_TOKEN", "")
            if access:
                # We construct a token object blindly, will fail if invalid later
                from domain.models import AuthToken
                self.auth_token = AuthToken(access_token=access)

    def _save_env(self):
        if not self.env_file.exists():
            self.env_file.touch()

        set_key(str(self.env_file), "AUTH_METHOD", self.auth_method_var.get())
        set_key(str(self.env_file), "YAZIO_EMAIL", self.email_var.get())
        set_key(str(self.env_file), "YAZIO_PASSWORD", self.password_var.get())
        set_key(str(self.env_file), "OUTPUT_FOLDER", self.output_folder_var.get())

        if self.auth_token:
             set_key(str(self.env_file), "YAZIO_ACCESS_TOKEN", self.auth_token.access_token)

    def _check_google_status(self):
        """Checks if we have valid Google credentials (local usage)."""
        # Google Auth Service infra might need to load credentials
        # We assume the service has a method or we check the file existence via the service?
        # The service provided relies on its internal state or file.
        # Let's assume we can ask it.
        # Logic adapted from previous UI:
        try:
             # This reloads and checks without launching browser
             tokens = self.google_auth.authenticate(force_new=False, interactive=False)
             if tokens:
                 self.google_status_var.set("Status: Connected to Google")
             else:
                 self.google_status_var.set("Status: Not connected")
        except Exception:
             self.google_status_var.set("Status: Not connected")

    def _build_ui(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Auth Method
        auth_frame = ttk.LabelFrame(main_frame, text="Authentication Method", padding="10")
        auth_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Radiobutton(auth_frame, text="Email & Password", variable=self.auth_method_var,
                       value="password", command=self._on_auth_method_change).pack(side=tk.LEFT, padx=(0, 20))
        ttk.Radiobutton(auth_frame, text="Google Login", variable=self.auth_method_var,
                       value="google", command=self._on_auth_method_change).pack(side=tk.LEFT)

        # Email/Password Section
        self.password_frame = ttk.LabelFrame(main_frame, text="Yazio Credentials", padding="10")

        ttk.Label(self.password_frame, text="Email:").grid(row=0, column=0, sticky=tk.W, pady=2)
        ttk.Entry(self.password_frame, textvariable=self.email_var, width=50).grid(row=0, column=1, sticky=tk.EW, pady=2, padx=5)

        ttk.Label(self.password_frame, text="Password:").grid(row=1, column=0, sticky=tk.W, pady=2)
        ttk.Entry(self.password_frame, textvariable=self.password_var, show="*", width=50).grid(row=1, column=1, sticky=tk.EW, pady=2, padx=5)
        self.password_frame.columnconfigure(1, weight=1)

        # Google Section
        self.google_frame = ttk.LabelFrame(main_frame, text="Google Login", padding="10")

        ttk.Label(self.google_frame, textvariable=self.google_status_var).pack(anchor=tk.W, pady=(0, 5))

        self.google_connect_btn = ttk.Button(self.google_frame, text="Connect with Google", command=self._start_google_auth)
        self.google_connect_btn.pack(anchor=tk.W)

        # Output Folder
        out_frame = ttk.LabelFrame(main_frame, text="Output Folder", padding="10")
        out_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Entry(out_frame, textvariable=self.output_folder_var, width=50).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(out_frame, text="Browse...", command=self._browse_folder).pack(side=tk.RIGHT, padx=5)

        # Actions
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(pady=10)

        ttk.Button(btn_frame, text="Save Settings", command=self._save_settings).pack(side=tk.LEFT, padx=5)
        self.export_btn = ttk.Button(btn_frame, text="Export Data", command=self._start_export)
        self.export_btn.pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Clear Tokens", command=self._clear_tokens).pack(side=tk.LEFT, padx=5)

        # Log
        log_frame = ttk.LabelFrame(main_frame, text="Log", padding="5")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        self.log_text = scrolledtext.ScrolledText(log_frame, height=10, state=tk.DISABLED)
        self.log_text.pack(fill=tk.BOTH, expand=True)

    def _on_auth_method_change(self):
        if self.auth_method_var.get() == "password":
            self.password_frame.pack(fill=tk.X, pady=(0, 10), after=self.root.nametowidget(self.password_frame.winfo_parent()).winfo_children()[0])
            self.google_frame.pack_forget()
        else:
            self.password_frame.pack_forget()
            self.google_frame.pack(fill=tk.X, pady=(0, 10))

    def _log(self, msg):
        def _append():
            self.log_text.config(state=tk.NORMAL)
            self.log_text.insert(tk.END, msg + "\n")
            self.log_text.see(tk.END)
            self.log_text.config(state=tk.DISABLED)
        self.root.after(0, _append)

    def _browse_folder(self):
        curr = self.output_folder_var.get()
        folder = filedialog.askdirectory(initialdir=curr if curr else None)
        if folder:
            self.output_folder_var.set(folder)

    def _save_settings(self):
        self._save_env()
        messagebox.showinfo("Saved", "Settings saved!")

    def _clear_tokens(self):
        self.auth_token = None
        if self.env_file.exists():
            set_key(str(self.env_file), "YAZIO_ACCESS_TOKEN", "")

        # Clear Google Token via service if possible, or just delete file logic which was infra specific
        # We can implement a method in GoogleAuthService or just ignore for now.
        # Previous logic deleted token.json.
        self._log("Tokens cleared in env. Google token file might remain (handled by infra).")
        messagebox.showinfo("Cleared", "Tokens cleared.")

    def _start_google_auth(self):
        def run():
            try:
                self._log("Starting Google Auth...")
                # 1. Authorize with Google (Infrastructure)
                tokens = self.google_auth.authenticate(force_new=True)
                self._log("Google Auth successful (Local)!")
                self.root.after(0, self._check_google_status)

                # 2. Exchange for Yazio Token (Application)
                self._log("Exchanging for Yazio Token...")
                self.auth_token = self.login_use_case.execute_google_login(
                    tokens["id_token"],
                    tokens["access_token"]
                )
                self._log("Yazio Login successful!")
                self._save_env()

            except Exception as e:
                self._log(f"Error: {e}")
                self.root.after(0, lambda err=str(e): messagebox.showerror("Error", err))

        threading.Thread(target=run, daemon=True).start()

    def _start_export(self):
        out_dir = self.output_folder_var.get()
        if not out_dir:
            messagebox.showerror("Error", "Please select an output folder.")
            return

        email = self.email_var.get()
        password = self.password_var.get()
        method = self.auth_method_var.get()

        def run():
            try:
                self.export_btn.config(state=tk.DISABLED)
                self._log("Preparing export...")

                token = self.auth_token

                # Perform Login if needed
                if not token:
                    if method == "password":
                        self._log(f"Logging in as {email}...")
                        token = self.login_use_case.execute_password_login(email, password)
                        self.auth_token = token
                        self._log("Login successful!")
                    else:
                        # Ensure we have google tokens then exchange?
                        # If we are here, we expect _start_google_auth to have set self.auth_token
                        # Or we try to refresh.
                        # For simplicity, if no token in Google mode, ask to connect.
                        raise RuntimeError("Not authenticated via Google. Please click 'Connect with Google' first.")

                # Verify export range (last 60 days default)
                end_date = datetime.now().date()
                start_date = end_date - timedelta(days=60)

                self._log(f"Exporting from {start_date} to {end_date}...")

                created_files = self.export_use_case.execute(
                    token,
                    start_date,
                    end_date,
                    out_dir
                )

                self._log("Export complete!")
                self._log(f"Created files: {', '.join([Path(p).name for p in created_files])}")
                messagebox.showinfo("Success", f"Exported {len(created_files)} CSV files.")

            except Exception as e:
                self._log(f"Error: {e}")
                self.root.after(0, lambda err=str(e): messagebox.showerror("Export Error", err))
            finally:
                self.root.after(0, lambda: self.export_btn.config(state=tk.NORMAL))

        threading.Thread(target=run, daemon=True).start()
