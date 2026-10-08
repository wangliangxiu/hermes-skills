# Desktop Icon Left-Alignment via C# + Win32 API

From session 2026-06-27. Tested successfully on **Acer Nitro AN515-55 (Windows 11)** with 31 desktop icons.

## The Code

```csharp
using System;
using System.Runtime.InteropServices;
using System.Windows.Forms;

class AlignDesktopIcons
{
    [DllImport("user32.dll", SetLastError = true)]
    static extern IntPtr FindWindow(string lpClassName, string lpWindowName);
    
    [DllImport("user32.dll", SetLastError = true, CharSet = CharSet.Auto)]
    static extern IntPtr SendMessage(IntPtr hWnd, uint Msg, IntPtr wParam, IntPtr lParam);
    
    [DllImport("user32.dll", SetLastError = true)]
    static extern IntPtr FindWindowEx(IntPtr hWndParent, IntPtr hWndChildAfter, string lpszClass, string lpszWindow);
    
    const uint LVM_GETITEMCOUNT = 0x1004;
    const uint LVM_SETITEMPOSITION = 0x100F;
    
    [StructLayout(LayoutKind.Sequential)]
    struct POINT { public int x; public int y; }
    
    static void Main()
    {
        IntPtr progman = FindWindow("Progman", "Program Manager");
        IntPtr worker = FindWindowEx(progman, IntPtr.Zero, "SHELLDLL_DefView", null);
        IntPtr listview = FindWindowEx(worker, IntPtr.Zero, "SysListView32", null);
        
        if (listview == IntPtr.Zero)
        {
            // Try alternate method (WorkerW) — needed on Windows 10/11
            IntPtr ptr = IntPtr.Zero;
            while (true)
            {
                ptr = FindWindowEx(IntPtr.Zero, ptr, "WorkerW", null);
                if (ptr == IntPtr.Zero) break;
                IntPtr ww = FindWindowEx(ptr, IntPtr.Zero, "SHELLDLL_DefView", null);
                if (ww != IntPtr.Zero)
                {
                    listview = FindWindowEx(ww, IntPtr.Zero, "SysListView32", null);
                    if (listview != IntPtr.Zero) break;
                }
            }
        }
        
        if (listview == IntPtr.Zero)
        {
            Console.WriteLine("ERROR: Cannot find desktop listview");
            return;
        }
        
        int count = (int)SendMessage(listview, LVM_GETITEMCOUNT, IntPtr.Zero, IntPtr.Zero);
        Console.WriteLine("Icons found: " + count);
        
        // Left align: all icons in column 0
        // Preserve vertical spacing (grid aligned)
        int startX = 15;
        int iconSpacingY = 100;
        int startY = 10;
        
        for (int i = 0; i < count; i++)
        {
            int x = startX;
            int y = startY + (i * iconSpacingY);
            
            // Pack x,y into LPARAM (low word = x, high word = y)
            IntPtr lParam = (IntPtr)((y << 16) | (x & 0xFFFF));
            
            SendMessage(listview, LVM_SETITEMPOSITION, (IntPtr)i, lParam);
        }
        
        Console.WriteLine("Done! " + count + " icons aligned left.");
        
        // Force desktop refresh
        SendMessage(progman, 0x001C, IntPtr.Zero, IntPtr.Zero);
    }
}
```

## Compilation & Execution

```batch
REM Find the C# compiler
dir C:\Windows\Microsoft.NET\Framework\v4.0.30319\csc.exe

REM Compile (note: System.Windows.Forms.dll for Screen info, optional if hardcoded)
csc.exe /target:exe /out:%TEMP%\AlignIcons.exe %TEMP%\AlignIcons.cs /reference:System.Windows.Forms.dll

REM Run
%TEMP%\AlignIcons.exe
```

The C# compiler (`csc.exe`) ships with .NET Framework and is available on any standard Windows install at `C:\Windows\Microsoft.NET\Framework\v4.0.30319\csc.exe`.

## Icon Count Note

Works for default icon sizes (medium). With very small/large icons, adjust `iconSpacingY`.
