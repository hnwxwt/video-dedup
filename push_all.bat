@echo off
chcp 65001 >nul
echo ========================================
echo   推送到 GitHub 和 Gitee
echo ========================================
echo.

echo [1/3] 检查当前分支...
for /f "tokens=*" %%i in ('git branch --show-current') do set BRANCH=%%i
echo 当前分支: %BRANCH%
echo.

echo [2/3] 推送到 GitHub...
git push github %BRANCH%
if errorlevel 1 (
    echo ❌ GitHub 推送失败
    pause
    exit /b 1
)
echo ✅ GitHub 推送成功
echo.

echo [3/3] 推送到 Gitee...
git push origin %BRANCH%
if errorlevel 1 (
    echo ❌ Gitee 推送失败
    pause
    exit /b 1
)
echo ✅ Gitee 推送成功
echo.

echo ========================================
echo   所有仓库推送完成！
echo ========================================
pause
