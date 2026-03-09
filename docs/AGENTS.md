## Purpose
Эта система нужна для демонстрации работы с kafka и анализа пропускной способности данного приложения. Стоит рассматривать consumer, producer и event_generator как отдельные сервисы.

## Tooling
Обязательные команды:
- python -m black .
- pytest -v
- poetry add <package>

## Defenition of Done
- все тесты пройдены
- новый код покрыт тестами
- линтер black не имеет замечаний

## Canonical Documentation
- ARCHITECTURE.md
- logic.md