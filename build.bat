@echo off
echo Installing dependencies...
pip install PyQt6 openpyxl keyring pyinstaller

echo.
echo Building MassMail.exe ...
pyinstaller ^
  --noconfirm ^
  --onefile ^
  --windowed ^
  --name "MassMail" ^
  --collect-all keyring ^
  --collect-all openpyxl ^
  --hidden-import keyring ^
  --hidden-import keyring.backends ^
  --hidden-import keyring.backends.Windows ^
  --hidden-import keyring.backends.fail ^
  main.py

echo.
echo ============================================
echo  Done!  Find MassMail.exe in the dist/ folder
echo ============================================
pause
