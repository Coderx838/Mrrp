; This file is fully ai generated cuz i dont know nsi lang etc blah blah ... but meow mrrp.

; Mrrp (.mrrp) Windows installer — NSIS script
; Build locally:  makensis /DVERSION=0.1.9 installer.nsi
; CI builds it with: makensis /DVERSION=%VERSION% installer.nsi
; Expects PyInstaller output at: dist\mrrp.exe
; Outputs: Mrrp-Setup-<VERSION>-windows-amd64.exe

!ifndef VERSION
!define VERSION "0.1.9"
!endif

Unicode True
Name "Mrrp ${VERSION} - the cat that remembers the future"
OutFile "Mrrp-Setup-${VERSION}-windows-amd64.exe"
InstallDir "$PROGRAMFILES\Mrrp"
InstallDirRegKey HKLM "Software\Mrrp" "InstallDir"
RequestExecutionLevel admin
SetCompressor /SOLID lzma
ShowInstDetails show
ShowUnInstDetails show

!include "MUI2.nsh"
!include "WinMessages.nsh"
!include "StrFunc.nsh"
${StrStr}
${StrRep}
${UnStrRep}

!define MUI_ABORTWARNING
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_LANGUAGE "English"

Section "Mrrp (required)" SEC_MAIN
  SectionIn RO
  SetOutPath "$INSTDIR"
  File "dist\mrrp.exe"
  File "mrrp.py"
  File "README.md"
  File "usage.txt"
  SetOutPath "$INSTDIR\examples"
  File "examples\hello.mrrp"
  File "examples\hello_world.mrrp"
  File "examples\fibonacci.mrrp"
  File "examples\cat_day.mrrp"
  File "examples\nine_lives.mrrp"
  File "examples\time_travel.mrrp"
  File "examples\power_pack.mrrp"
  ; cat_pack stdlib so `adopt math/strings/games` works from exe too
  SetOutPath "$INSTDIR\cat_pack"
  File "cat_pack\math.mrrp"
  File "cat_pack\strings.mrrp"
  File "cat_pack\games.mrrp"

  WriteUninstaller "$INSTDIR\Uninstall.exe"
  WriteRegStr HKLM "Software\Mrrp" "InstallDir" "$INSTDIR"
  WriteRegStr HKLM "Software\Mrrp" "Version" "${VERSION}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Mrrp" "DisplayName" "Mrrp ${VERSION}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Mrrp" "DisplayVersion" "${VERSION}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Mrrp" "Publisher" "Mrrp"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Mrrp" "UninstallString" '"$INSTDIR\Uninstall.exe"'
  WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Mrrp" "NoModify" 1
  WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Mrrp" "NoRepair" 1

  ; Add $INSTDIR to system PATH (so `mrrp` works everywhere)
  ReadRegStr $0 HKLM "SYSTEM\CurrentControlSet\Control\Session Manager\Environment" "Path"
  ${StrStr} $1 "$0" "$INSTDIR"
  ${If} $1 == ""
    WriteRegExpandStr HKLM "SYSTEM\CurrentControlSet\Control\Session Manager\Environment" "Path" "$0;$INSTDIR"
    SendMessage ${HWND_BROADCAST} ${WM_WININICHANGE} 0 "STR:Environment" /TIMEOUT=5000
  ${EndIf}

  CreateDirectory "$SMPROGRAMS\Mrrp"
  CreateShortCut "$SMPROGRAMS\Mrrp\Mrrp.lnk" "$INSTDIR\mrrp.exe"
  CreateShortCut "$SMPROGRAMS\Mrrp\Uninstall.lnk" "$INSTDIR\Uninstall.exe"
SectionEnd

Section "Uninstall"
  Delete "$INSTDIR\mrrp.exe"
  Delete "$INSTDIR\mrrp.py"
  Delete "$INSTDIR\README.md"
  Delete "$INSTDIR\usage.txt"
  Delete "$INSTDIR\Uninstall.exe"
  Delete "$INSTDIR\examples\hello.mrrp"
  Delete "$INSTDIR\examples\hello_world.mrrp"
  Delete "$INSTDIR\examples\fibonacci.mrrp"
  Delete "$INSTDIR\examples\cat_day.mrrp"
  Delete "$INSTDIR\examples\nine_lives.mrrp"
  Delete "$INSTDIR\examples\time_travel.mrrp"
  Delete "$INSTDIR\examples\power_pack.mrrp"
  RMDir "$INSTDIR\examples"
  Delete "$INSTDIR\cat_pack\math.mrrp"
  Delete "$INSTDIR\cat_pack\strings.mrrp"
  Delete "$INSTDIR\cat_pack\games.mrrp"
  RMDir "$INSTDIR\cat_pack"
  Delete "$SMPROGRAMS\Mrrp\Mrrp.lnk"
  Delete "$SMPROGRAMS\Mrrp\Uninstall.lnk"
  RMDir "$SMPROGRAMS\Mrrp"
  RMDir "$INSTDIR"

  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Mrrp"
  DeleteRegKey HKLM "Software\Mrrp"

  ; Best-effort PATH cleanup: "$INSTDIR;" -> "" then ";$INSTDIR" -> "" then "$INSTDIR" -> ""
  ReadRegStr $0 HKLM "SYSTEM\CurrentControlSet\Control\Session Manager\Environment" "Path"
  ${UnStrRep} $1 "$0" "$INSTDIR;" ""
  ${UnStrRep} $2 "$1" ";$INSTDIR" ""
  ${UnStrRep} $3 "$2" "$INSTDIR" ""
  WriteRegExpandStr HKLM "SYSTEM\CurrentControlSet\Control\Session Manager\Environment" "Path" "$3"
  SendMessage ${HWND_BROADCAST} ${WM_WININICHANGE} 0 "STR:Environment" /TIMEOUT=5000
SectionEnd
