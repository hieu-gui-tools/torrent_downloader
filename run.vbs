Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

' Get project directory
strDir = fso.GetParentFolderName(WScript.ScriptFullName)
WshShell.CurrentDirectory = strDir

' Launch silently without showing black console window
' 0 = Hide window, False = Do not wait for script to finish
WshShell.Run "cmd.exe /c uv run torrent-downloader", 0, False

Set WshShell = Nothing
Set fso = Nothing
