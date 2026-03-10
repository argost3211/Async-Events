## Purpose
Эта система нужна для демонстрации работы с kafka и анализа пропускной способности данного приложения. Стоит рассматривать consumer, producer и event_generator как отдельные сервисы.

## Tooling
Обязательные команды:
- python -m black .
- pytest -v
- poetry add <package>
- alembic revision --autogenerate -m <message>
- flake8 .

## Definition of Done
- покрытие тестами выше 85 процентов
- все тесты пройдены
- линтер black не имеет замечаний
- flake8 не имеет замечаний

## Canonical Documentation
- ARCHITECTURE.md
- logic.md
- REFERENCE_EXAMPLES.md

## MUST NOT (запрещено)
- создавать миграции без учета примеров миграций из @REFERENCE_EXAMPLES.md
- давать переменным имена без учета примеров из @REFERENCE_EXAMPLES.md


## MUST (обязательно)
- сначала нужно писать тесты, а потом реализацию (TDD)