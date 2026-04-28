@echo off
chcp 65001 >nul
echo ========================================
echo 配置 GitHub 访问令牌
echo ========================================
echo.
echo 请按以下步骤操作：
echo.
echo 1. 打开浏览器访问: https://github.com/settings/tokens
echo 2. 点击 "Generate new token (classic)"
echo 3. 勾选权限: repo (完整仓库访问)
echo 4. 生成并复制令牌
echo.
pause

set /p GITHUB_TOKEN="请粘贴你的 GitHub Token: "

echo.
echo 正在配置 Git...
git config --global credential.github.helper store

echo https://github.com > %TEMP%\git-creds.txt
echo username=hnwxwt >> %TEMP%\git-creds.txt
echo password=%GITHUB_TOKEN% >> %TEMP%\git-creds.txt

git credential approve < %TEMP%\git-creds.txt
del %TEMP%\git-creds.txt

echo.
echo ✓ GitHub Token 配置完成！
echo.
echo 现在可以推送代码了:
echo git push github main
echo.
pause
