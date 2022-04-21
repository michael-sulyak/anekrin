import typing

from tortoise import Model
from tortoise.backends.base.schema_generator import BaseSchemaGenerator
from tortoise.indexes import Index


class UniqueTogether(Index):
    INDEX_CREATE_TEMPLATE = (
        'ALTER TABLE {table_name} DROP CONSTRAINT IF EXISTS {index_name};'
        'ALTER TABLE {table_name} ADD CONSTRAINT {index_name} UNIQUE ({fields}){extra};'
    )

    def __init__(
        self, *,
        fields: typing.Optional[typing.Set[str]] = None,
        name: typing.Optional[str] = None,
        is_deferrable_initially_immediate: bool = False,
    ) -> None:
        self.fields = list(fields or [])

        if not fields:
            raise ValueError('At least one field or expression is required to define an index.')

        self.name = name
        self.extra = ''

        if is_deferrable_initially_immediate:
            self.extra += ' DEFERRABLE INITIALLY IMMEDIATE'

    def get_sql(self, schema_generator: BaseSchemaGenerator, model: typing.Type[Model], safe: bool):
        return self.INDEX_CREATE_TEMPLATE.format(
            index_name=schema_generator.quote(
                self.name or schema_generator._generate_index_name('ut_idx', model, self.fields)
            ),
            table_name=schema_generator.quote(model._meta.db_table),
            fields=', '.join(schema_generator.quote(f) for f in self.fields),
            extra=self.extra,
        )

    def index_name(self, schema_generator: BaseSchemaGenerator, model: typing.Type[Model]):
        return self.name or schema_generator._generate_index_name('ut_idx', model, self.fields)
