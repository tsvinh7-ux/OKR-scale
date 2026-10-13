@echo off
REM DMAG OKR - run every automated test on Windows (needs Docker Desktop running)
docker compose run --rm tests
pause
