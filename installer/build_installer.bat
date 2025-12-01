@echo off
echo ================================================
echo IT Ticket Manager - Build Script
echo ================================================
echo.

echo [1/4] Nettoyage des anciens builds...
if exist ..\dist rmdir /s /q ..\dist
if exist ..\build rmdir /s /q ..\build
if exist Output rmdir /s /q Output

echo [2/4] Construction de l'executable avec PyInstaller...
cd ..
pyinstaller build_config.spec
if errorlevel 1 (
    echo ERREUR: PyInstaller a echoue
    pause
    exit /b 1
)

echo [3/4] Verification de l'executable...
if not exist dist\ITTicketManager.exe (
    echo ERREUR: L'executable n'a pas ete cree
    pause
    exit /b 1
)

echo [4/4] Creation de l'installeur avec Inno Setup...
cd installer
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" setup_script.iss
if errorlevel 1 (
    echo ERREUR: Inno Setup a echoue
    echo Assurez-vous qu'Inno Setup est installe
    pause
    exit /b 1
)

echo.
echo ================================================
echo BUILD TERMINE AVEC SUCCES !
echo ================================================
echo.
echo L'installeur se trouve dans: installer\Output\
echo.
pause
