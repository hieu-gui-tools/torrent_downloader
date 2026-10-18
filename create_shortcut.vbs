Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

strProjectDir = fso.GetParentFolderName(WScript.ScriptFullName)
strDesktop = WshShell.SpecialFolders("Desktop")
strShortcutPath = strDesktop & "\Torrent Downloader.lnk"
strIconPath = strProjectDir & "\assets\app.ico"
strVbsPath = strProjectDir & "\run.vbs"

Set oShortcut = WshShell.CreateShortcut(strShortcutPath)
oShortcut.TargetPath = "wscript.exe"
oShortcut.Arguments = """" & strVbsPath & """"
oShortcut.WorkingDirectory = strProjectDir
oShortcut.WindowStyle = 1

If fso.FileExists(strIconPath) Then
    oShortcut.IconLocation = strIconPath & ",0"
End If

oShortcut.Description = "Torrent Downloader Pro - Fast & Multi-Torrent Downloader"
oShortcut.Save

WScript.Echo "Shortcut 'Torrent Downloader' da duoc tao thanh cong tai Desktop!"
