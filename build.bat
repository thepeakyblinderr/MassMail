@echo off
echo Installing dependencies...
pip install -r requirements.txt

echo.
echo Building MassMail.exe ...
pyinstaller ^
  --noconfirm ^
  --onefile ^
  --windowed ^
  --name "MassMail" ^
  --hidden-import keyring.backends.Windows ^
  --hidden-import keyring.backends ^
  --hidden-import openpyxl ^
  main.py

echo.
echo ============================================
echo  Done!  Find MassMail.exe in the dist/ folder
echo ============================================
pause
