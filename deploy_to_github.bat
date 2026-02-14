@echo off
REM Flask Shop 项目部署脚本

echo ===== 开始初始化 Git 仓库 =====

REM 1. 初始化 Git 仓库
git init
if %errorlevel% neq 0 (
    echo Git 初始化失败！
    pause
    exit /b 1
)

REM 2. 添加所有文件到暂存区
echo.
echo ===== 添加文件到暂存区 =====
git add .

REM 3. 查看状态
echo.
echo ===== 当前状态 =====
git status

REM 4. 提交代码
echo.
echo ===== 提交代码 =====
set /p commit_msg="请输入提交信息: "
git commit -m "%commit_msg%"

REM 5. 关联远程仓库（请先在 GitHub 创建仓库）
echo.
echo ===== 关联远程仓库 =====
set /p remote_url="请输入 GitHub 仓库地址 (如: https://github.com/你的用户名/flask_shop.git): "
git remote add origin %remote_url%

REM 6. 推送到 GitHub
echo.
echo ===== 推送到 GitHub =====
git push -u origin master

echo.
echo ===== 完成！=====
pause
