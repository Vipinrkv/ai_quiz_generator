Get-ChildItem C:\,D:\,E:\,F:\,G:\ -Recurse -Force -ErrorAction SilentlyContinue | Where-Object { $_.FullName -match 'Autodesk|ArtCAM' } | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue


dir C:\*ArtCAM* /s /b
dir C:\*Autodesk* /s /b


I can see the problem from your screenshot.

You're using PowerShell 2.0 on Windows 7, which is much older than current versions, and the command I gave isn't parsing correctly there.

Also, your screenshot shows this error:

> Remove-Item : A positional parameter cannot be found...



Let's use commands that work reliably on Windows 7.

Step 1: Find all Autodesk and ArtCAM folders

Open Command Prompt as Administrator (not PowerShell) and run:

dir C:\*ArtCAM* /s /b
dir C:\*Autodesk* /s /b

If you have D:, E:, F:, G: drives:

dir D:\*ArtCAM* /s /b
dir D:\*Autodesk* /s /b

Repeat for each drive.


---

Step 2: Delete them

For each folder you find:

rmdir /s /q "FULL_FOLDER_PATH"

For example:

rmdir /s /q "C:\Program Files\Autodesk"
rmdir /s /q "C:\ProgramData\Autodesk"
rmdir /s /q "C:\Users\GULSHAN\AppData\Roaming\Autodesk"


---

Step 3: If you want to remove ALL Autodesk registry keys

Run Command Prompt as Administrator:

reg delete "HKLM\SOFTWARE\Autodesk" /f
reg delete "HKLM\SOFTWARE\Wow6432Node\Autodesk" /f
reg delete "HKCU\Software\Autodesk" /f


---

I also noticed something important

Your desktop says:

> This copy of Windows is not genuine



and you're running Windows 7 Professional SP1 (64-bit).

Windows 7 is no longer supported, and many newer installers (including later Autodesk products) won't install correctly on it.

I can give you something better

I can write a single Windows 7 batch (.bat) file that automatically:

Uninstalls Autodesk products (where possible)

Deletes all Autodesk and ArtCAM folders from every drive

Removes registry entries

Cleans temporary files

Removes installer leftovers


You would just run it once as Administrator. That is much more reliable than typing many commands manually.