@echo off
REM DMAG OKR - start on Windows (needs Docker Desktop running)
docker compose up -d
echo.
echo Lan dau khoi dong mat 2-4 phut de tao du lieu. Theo doi: docker compose logs -f odoo
echo Mo trinh duyet: http://localhost:8069   (admin / admin)
pause
