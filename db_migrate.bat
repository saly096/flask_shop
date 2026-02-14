@echo off
REM 数据库迁移管理脚本

:menu
cls
echo ===== Flask Shop 数据库管理 =====
echo 1. 初始化迁移目录
echo 2. 创建迁移脚本
echo 3. 执行迁移
echo 4. 回滚到上一版本
echo 5. 查看迁移状态
echo 0. 退出
echo.
set /p choice="请选择操作: "

if "%choice%"=="1" goto init
if "%choice%"=="2" goto migrate
if "%choice%"=="3" goto upgrade
if "%choice%"=="4" goto downgrade
if "%choice%"=="5" goto status
if "%choice%"=="0" exit

:init
echo.
echo ===== 初始化迁移目录 =====
flask db init
pause
goto menu

:migrate
echo.
echo ===== 创建迁移脚本 =====
set /p msg="请输入迁移描述 (如 add_user_table): "
flask db migrate -m "%msg%"
pause
goto menu

:upgrade
echo.
echo ===== 执行迁移 =====
flask db upgrade
pause
goto menu

:downgrade
echo.
echo ===== 回滚迁移 =====
flask db downgrade
pause
goto menu

:status
echo.
echo ===== 迁移状态 =====
flask db history
pause
goto menu
