import winreg
import tkinter as tk
from tkinter import messagebox, simpledialog, filedialog
import os
import ctypes

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def search_url_protocol():
    url_protocols = []
    # Open the HKEY_CLASSES_ROOT registry hive
    with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, '') as root_key:
        try:
            i = 0
            while True:
                # Enumerate all subkeys under HKEY_CLASSES_ROOT
                subkey_name = winreg.EnumKey(root_key, i)
                subkey_path = f"{subkey_name}"

                try:
                    # Open the subkey
                    with winreg.OpenKey(root_key, subkey_path) as subkey:
                        try:
                            # Check if the subkey has a value named 'URL Protocol'
                            url_protocol_value, _ = winreg.QueryValueEx(subkey, 'URL Protocol')
                            if not url_protocol_value or '""' in url_protocol_value:
                                command_subkey_path = f"{subkey_path}\\shell\\open\\command"
                                try:
                                    with winreg.OpenKey(root_key, command_subkey_path) as command_subkey:
                                        command_value, _ = winreg.QueryValueEx(command_subkey, '')
                                        url_protocols.append((subkey_path, command_value))
                                except FileNotFoundError:
                                    pass  # The command subkey does not exist
                        except FileNotFoundError:
                            pass  # The value 'URL Protocol' does not exist in this subkey
                except FileNotFoundError:
                    pass  # The subkey does not exist

                i += 1
        except OSError:
            pass  # No more subkeys to enumerate
    return url_protocols

def display_entries():
    entries = search_url_protocol()
    for widget in entries_frame.winfo_children():
        widget.destroy()
    for entry in entries:
        key_path, command_value = entry
        frame = tk.Frame(entries_frame, bd=1, relief=tk.SOLID)
        frame.pack(fill=tk.X, padx=5, pady=2)

        header_frame = tk.Frame(frame)
        header_frame.pack(fill=tk.X)

        tk.Label(header_frame, text=f"{key_path}://", font=('Times 16')).pack(side=tk.LEFT)

        details_frame = tk.Frame(frame)
        details_frame.pack(fill=tk.X)

        tk.Label(details_frame, text=f"Command Value: {command_value}").pack(side=tk.LEFT)
        tk.Button(header_frame, text="Replace", command=lambda k=key_path, c=command_value: modify_key(k, c)).pack(side=tk.RIGHT, padx=5)
        tk.Button(header_frame, text="Remove", command=lambda k=key_path: remove_key(k)).pack(side=tk.RIGHT, padx=5)

def add_key():
    key_name = simpledialog.askstring("Input", "Enter the URI name:\t\t\t\t")
    if key_name:
        command_value = ask_command_value("Enter the command value:\t\t\t\t")
        if command_value:
            try:
                with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, key_name) as new_key:
                    winreg.SetValueEx(new_key, 'URL Protocol', 0, winreg.REG_SZ, '')
                    command_subkey_path = f"{key_name}\\shell\\open\\command"
                    with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, command_subkey_path) as command_subkey:
                        winreg.SetValueEx(command_subkey, '', 0, winreg.REG_SZ, command_value)
                display_entries()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to add key: {e}")

def modify_key(key_path, current_command_value):
    command_value = ask_command_value("Enter the new command value:", initialvalue=current_command_value)
    if command_value:
        try:
            command_subkey_path = f"{key_path}\\shell\\open\\command"
            with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, command_subkey_path, 0, winreg.KEY_SET_VALUE) as command_subkey:
                winreg.SetValueEx(command_subkey, '', 0, winreg.REG_SZ, command_value)
            display_entries()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to modify key: {e}")

def remove_key(key_path):
    try:
        winreg.DeleteKey(winreg.HKEY_CLASSES_ROOT, key_path)
        display_entries()
    except Exception as e:
        messagebox.showerror("Error", f"Failed to remove key: {e}")

def on_mousewheel(event):
    canvas.yview_scroll(int(-1*(event.delta/120)), "units")

def ask_command_value(prompt, initialvalue=""):
    def browse_file():
        file_path = filedialog.askopenfilename(filetypes=[("Executable files", "*.exe")])
        if file_path:
            command_var.set(f'"{file_path}"')

    def on_cancel():
        command_var.set("")
        command_dialog.destroy()

    command_dialog = tk.Toplevel(root)
    command_dialog.title("Input")
    command_dialog.grab_set()  # Make the dialogue modal

    tk.Label(command_dialog, text=prompt).pack(padx=10, pady=10)

    command_var = tk.StringVar(value=initialvalue)
    command_entry = tk.Entry(command_dialog, textvariable=command_var, width=50)
    command_entry.pack(padx=10, pady=5)

    browse_button = tk.Button(command_dialog, text="Browse", command=browse_file)
    browse_button.pack(padx=10, pady=5)

    ok_button = tk.Button(command_dialog, text="OK", command=command_dialog.destroy)
    ok_button.pack(side=tk.LEFT, padx=10, pady=5)

    cancel_button = tk.Button(command_dialog, text="Cancel", command=on_cancel)
    cancel_button.pack(side=tk.RIGHT, padx=10, pady=5)

    command_dialog.wait_window()
    return command_var.get()

def backup_registry():
    file_path = filedialog.asksaveasfilename(defaultextension=".reg", filetypes=[("Registry Files", "*.reg")])
    if file_path:
        try:
            with open(file_path, 'w') as file:
                file.write("Windows Registry Editor Version 5.00\n\n")
                for key_path, command_value in search_url_protocol():
                    file.write(f'[HKEY_CLASSES_ROOT\\{key_path}\\shell\\open\\command]\n')
                    file.write(f'"@"="{command_value}"\n\n')
            messagebox.showinfo("Backup", "Registry backup successful!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to backup registry: {e}")

def restore_registry():
    file_path = filedialog.askopenfilename(filetypes=[("Registry Files", "*.reg")])
    if file_path:
        try:
            os.system(f'regedit /s "{file_path}"')
            messagebox.showinfo("Restore", "Registry restore successful!")
            display_entries()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to restore registry: {e}")

# Create the main window
root = tk.Tk()
root.title("Installed URIs")
root.geometry("1100x550+50+50")

# Check admin privileges and display at the top
admin_label = tk.Label(root, text=f"Admin Privileges: {'Yes' if is_admin() else 'No'}")
admin_label.pack(fill=tk.X, padx=10, pady=5)

# Create the canvas and scrollbar for scrolling
canvas = tk.Canvas(root)
scrollbar = tk.Scrollbar(root, orient="vertical", command=canvas.yview)
scrollable_frame = tk.Frame(canvas)

scrollable_frame.bind(
    "<Configure>",
    lambda e: canvas.configure(
        scrollregion=canvas.bbox("all")
    )
)

canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
canvas.configure(yscrollcommand=scrollbar.set)

# Bind mouse wheel events to the canvas
canvas.bind_all("<MouseWheel>", on_mousewheel)

# Create the entries frame inside the scrollable frame
entries_frame = tk.Frame(scrollable_frame)
entries_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

# Create the buttons frame at the top
buttons_frame = tk.Frame(root)
buttons_frame.pack(fill=tk.X, padx=10, pady=10)

# Create the buttons
tk.Button(buttons_frame, text="Add Key", command=add_key).pack(side=tk.LEFT, padx=5)
tk.Button(buttons_frame, text="Refresh", command=display_entries).pack(side=tk.LEFT, padx=5)
tk.Button(buttons_frame, text="Backup", command=backup_registry).pack(side=tk.LEFT, padx=5)
tk.Button(buttons_frame, text="Restore", command=restore_registry).pack(side=tk.LEFT, padx=5)

# Pack the canvas and scrollbar
canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

# Display the initial entries
display_entries()

# Start the Tkinter event loop
root.mainloop()